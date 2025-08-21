from typing import List, Optional, Dict, Any, Callable, Tuple
import json
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import structlog
from typing import Awaitable
import uuid
import os

import dspy
from dspy import Signature, InputField, OutputField
from pydantic import BaseModel, Field

from app.models.agent_organization import (
    AgentNode, AgentOrganization, WorkflowTask, WorkflowExecution,
    HumanInteractionRequest, AgentStrategy, AgentRole, TaskStatus, ExecutionStatus
)
from app.services.template_service import template_service
from app.services.websocket_manager import websocket_manager
from app.services.tool_registry_service import tool_registry_service
from openai import OpenAI


logger = structlog.get_logger()

# Configure DSPy at module level (before any async tasks)
_global_llm_instance = None

try:
    # Configure litellm to drop unsupported parameters via environment variable
    # This is more reliable than setting it at runtime
    os.environ["LITELLM_DROP_PARAMS"] = "True"
    
    # Also set it directly in case the env var isn't read yet
    import litellm
    litellm.drop_params = True
    
    _global_llm_instance = dspy.LM(
        model="openai/gpt-3.5-turbo",
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    dspy.configure(lm=_global_llm_instance)
    logger.info("DSPy configured globally for WorkflowExecutionAgent with litellm drop_params enabled")
except Exception as e:
    logger.error("Failed to configure DSPy for WorkflowExecutionAgent", error=str(e))
    _global_llm_instance = None


# DSPy Signatures for different execution strategies
class SimpleTaskExecution(Signature):
    """Execute a task using simple direct execution strategy"""
    
    # Input fields
    task_name: str = InputField(desc="Name of the task to execute")
    task_description: str = InputField(desc="Detailed description of the task")
    task_objective: str = InputField(desc="Main objective or goal of the task")
    completion_criteria: str = InputField(desc="Criteria that define task completion")
    agent_name: str = InputField(desc="Name of the executing agent")
    agent_role: str = InputField(desc="Role of the executing agent")
    agent_capabilities: str = InputField(desc="List of agent capabilities")
    available_tools: str = InputField(desc="Available tools for task execution")
    execution_context: str = InputField(desc="JSON context for task execution")
    
    # Output fields
    execution_result: str = OutputField(desc="Result of task execution")
    confidence_score: str = OutputField(desc="Confidence score between 0.0 and 1.0")
    success_status: str = OutputField(desc="Whether execution was successful (true/false)")
    reasoning: str = OutputField(desc="Explanation of the execution approach and results")


class ChainOfThoughtPlanning(Signature):
    """Plan task execution using Chain of Thought reasoning"""
    
    # Input fields
    task_name: str = InputField(desc="Name of the task to plan")
    task_description: str = InputField(desc="Detailed description of the task")
    task_objective: str = InputField(desc="Main objective or goal of the task")
    completion_criteria: str = InputField(desc="Criteria that define task completion")
    agent_capabilities: str = InputField(desc="List of agent capabilities")
    available_tools: str = InputField(desc="Available tools for task execution")
    execution_context: str = InputField(desc="JSON context for task execution")
    
    # Output fields
    reasoning_steps: str = OutputField(desc="JSON list of reasoning steps")
    execution_plan: str = OutputField(desc="Detailed execution plan")
    required_tools: str = OutputField(desc="Tools needed for execution")
    confidence_score: str = OutputField(desc="Confidence score between 0.0 and 1.0")


class HumanInputRequest:
    def __init__(self, question: str):
        self.question = question
        self._response_future = asyncio.Future()

    async def response(self) -> str:
        """Wait for the response to be provided"""
        return await self._response_future

    def set_response(self, response: str):
        """Provide the response and notify waiters"""
        self._response_future.set_result(response)

class TaskResult(BaseModel):
    """Structured output for task execution results"""
    success: bool = Field(description="Whether the task was completed successfully")
    strategy: str = Field(description="Execution strategy used")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    execution_summary: str = Field(description="Summary of execution")
    reasoning: str = Field(description="Detailed reasoning and steps taken")
    response: str = Field(description="Task execution response")
    task_id: str = Field(description="ID of the executed task")
    agent_id: str = Field(description="ID of the executing agent")
    completed_at: str = Field(description="ISO timestamp of completion")


# DSPy Modules for different execution strategies
class SimpleExecutionModule(dspy.Module):
    """DSPy module for simple task execution"""
    
    def __init__(self):
        super().__init__()
        self.execute_task = dspy.ChainOfThought(SimpleTaskExecution)
    
    def forward(self, task_name, task_description, task_objective, completion_criteria,
                agent_name, agent_role, agent_capabilities, available_tools, execution_context):
        
        # Get available tools from registry
        try:
            available_tools_list = tool_registry_service.get_tools_for_dspy()
        except Exception as e:
            logger.warning("Failed to get tools from registry", error=str(e))
            available_tools_list = []
        
        result = self.execute_task(
            task_name=task_name,
            task_description=task_description,
            task_objective=task_objective,
            completion_criteria=completion_criteria,
            agent_name=agent_name,
            agent_role=agent_role,
            agent_capabilities=agent_capabilities,
            available_tools=available_tools,
            execution_context=execution_context
        )
        
        return result


class ChainOfThoughtModule(dspy.Module):
    """DSPy module for Chain of Thought task execution"""
    
    def __init__(self):
        super().__init__()
        self.plan_execution = dspy.ChainOfThought(ChainOfThoughtPlanning)
    
    def forward(self, task_name, task_description, task_objective, completion_criteria,
                agent_capabilities, available_tools, execution_context):
        
        result = self.plan_execution(
            task_name=task_name,
            task_description=task_description,
            task_objective=task_objective,
            completion_criteria=completion_criteria,
            agent_capabilities=agent_capabilities,
            available_tools=available_tools,
            execution_context=execution_context
        )
        
        return result


class TaskExecutionSignature(Signature):
    """Signature for DSPy ReAct task execution"""
    task_name = InputField(desc="Name of the task to execute")
    task_objective = InputField(desc="Main objective or goal of the task")
    current_context = InputField(desc="Current execution context and available information")
    
    response = OutputField(desc="Final response or result after completing the task")


class WorkflowExecutionAgent:
    """
    AI Agent for executing workflow tasks with multi-agent coordination.
    
    This agent now supports DSPy framework with enhanced user interaction capabilities:
    
    Features:
    - DSPy-powered execution strategies (Simple, Chain of Thought, ReAct)
    - Intelligent user information requests through chat panel
    - Real-time WebSocket communication for agent thoughts and user interactions
    - Graceful fallback to OpenAI client when DSPy is unavailable
    
    User Interaction Actions (available in ReAct mode):
    - request_user_info: <question> - Ask user for specific information
    - ask_user: <question> - Request clarification from user  
    - seek_clarification: <question> - Get more details from user
    - human_interaction: <message> - Request general human assistance
    """
    
    def __init__(self, 
                 agent_node: AgentNode,
                 organization: AgentOrganization,
                 llm_client: Optional[OpenAI] = None):
        self.agent_node = agent_node
        self.organization = organization
        self.llm_client = llm_client  # Keep for fallback compatibility
        self.logger = logger.bind(
            agent_id=agent_node.id,
            agent_name=agent_node.name,
            agent_role=agent_node.role.value
        )
        
        # Use the global LLM instance configured at module level
        self.llm = _global_llm_instance
        
        # Initialize DSPy modules (they will use the global configuration)
        if self.llm is not None:
            self.simple_executor = SimpleExecutionModule()
            self.cot_planner = ChainOfThoughtModule()
            # Initialize dspy.ReAct with tools - will be done lazily when needed
            self.react_executor = None
            self.logger.info("DSPy modules initialized for WorkflowExecutionAgent")
        else:
            self.logger.warning("DSPy not configured - falling back to OpenAI client")
            self.simple_executor = None
            self.cot_planner = None
            self.react_executor = None
        
        # Agent state
        self.current_execution_id: Optional[str] = None  # Will be set when executing workflow
        self.current_tasks: Dict[str, WorkflowTask] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.reasoning_history: List[Dict[str, Any]] = []
        self.pending_approvals: Dict[str, HumanInteractionRequest] = {}
        
        # Initialize tools
        self.available_tools = self._initialize_tools()
        
    def _initialize_tools(self) -> Dict[str, Callable]:
        """Initialize available tools for the agent"""
        tools = {}
        
        for tool in self.agent_node.tools:
            # Map tool names to implementations
            if tool.name == "database_query":
                tools[tool.name] = self._tool_database_query
            elif tool.name == "api_request":
                tools[tool.name] = self._tool_api_request
            elif tool.name == "file_operation":
                tools[tool.name] = self._tool_file_operation
            elif tool.name == "human_interaction":
                tools[tool.name] = self._tool_human_interaction
            elif tool.name == "agent_handoff":
                tools[tool.name] = self._tool_agent_handoff
            elif tool.name == "task_validation":
                tools[tool.name] = self._tool_task_validation
            elif tool.name == "knowledge_search":
                tools[tool.name] = self._tool_knowledge_search
            elif tool.name == "notification":
                tools[tool.name] = self._tool_notification
            else:
                # Generic tool wrapper
                tools[tool.name] = lambda **kwargs: self._generic_tool_execution(tool.name, **kwargs)
        
        return tools
    
    async def execute_task(self, 
                          task: WorkflowTask,
                          execution_context: Dict[str, Any],
                          workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a single workflow task"""
        
        # Set the current execution ID for human-in-the-loop tools
        self.current_execution_id = workflow_execution.id
        
        task_id = task.id
        self.logger.info(
            "Starting task execution",
            task_id=task_id,
            task_name=task.name,
            objective=task.objective
        )
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        task.assigned_agent_id = self.agent_node.id
        print (f"===>Agent {self.agent_node.name}, strategy {self.agent_node.strategy} is executing task {task.name} with ID {task_id}")
        try:
            # Choose execution strategy
            if self.agent_node.strategy == AgentStrategy.SIMPLE:
                result = await self._execute_with_simple(task, execution_context, workflow_execution)
            elif self.agent_node.strategy == AgentStrategy.CHAIN_OF_THOUGHT:
                result = await self._execute_with_chain_of_thought(task, execution_context, workflow_execution)
            elif self.agent_node.strategy == AgentStrategy.REACT:
                result = await self._execute_with_react(task, execution_context, workflow_execution)
            else:  # HYBRID
                result = await self._execute_with_hybrid_strategy(task, execution_context, workflow_execution)
            
            # Check if human approval required
            if (self.agent_node.requires_human_approval or 
                result.get('confidence', 1.0) < self.agent_node.human_escalation_threshold):
                
                approval_result = await self._request_human_approval(task, result, workflow_execution)
                if approval_result['status'] == 'approved':
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    result.update(approval_result.get('feedback', {}))
                else:
                    task.status = TaskStatus.ESCALATED
                    result['escalation_reason'] = approval_result.get('reason', 'Human rejected')
            else:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
            
            # Store results
            task.results = result
            print(f"===> task: {task}")
            
            self.logger.info(
                "Task execution completed",
                task_id=task_id,
                status=task.status,
                confidence=result.get('confidence', 0.0)
            )
            
            # Clean up execution ID
            self.current_execution_id = None
            
            return {
                'task_id': task_id,
                'status': task.status.value,
                'results': result,
                'agent_id': self.agent_node.id,
                'execution_time': (task.completed_at - task.started_at).total_seconds() if task.completed_at else None
            }
            
        except Exception as e:
            self.logger.error("Task execution failed", task_id=task_id, error=str(e))
            task.status = TaskStatus.FAILED
            task.results = {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Clean up execution ID
            self.current_execution_id = None
            
            return {
                'task_id': task_id,
                'status': task.status.value,
                'error': str(e),
                'agent_id': self.agent_node.id
            }
    
    async def _execute_with_simple(self,
                                  task: WorkflowTask,
                                  execution_context: Dict[str, Any],
                                  workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using simple direct execution without complex reasoning"""
        
        # Try DSPy first, fallback to OpenAI client if needed
        if self.simple_executor is not None and self.llm is not None:
            return await self._execute_with_dspy_simple(task, execution_context, workflow_execution)
        elif self.llm_client:
            return await self._execute_with_openai_simple(task, execution_context, workflow_execution)
        else:
            return await self._fallback_execution(task, execution_context)
    
    async def _execute_with_dspy_simple(self,
                                       task: WorkflowTask,
                                       execution_context: Dict[str, Any],
                                       workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using DSPy SimpleExecutionModule"""
        
        self.logger.info(
            "Executing task with DSPy simple strategy",
            task_id=task.id,
            agent_id=self.agent_node.id
        )
        
        try:
            # Prepare inputs for DSPy signature
            agent_capabilities = json.dumps([cap.name for cap in self.agent_node.capabilities])
            available_tools = json.dumps(list(self.available_tools.keys()))
            execution_context_str = json.dumps(execution_context, default=str)
            
            # Send agent thought to WebSocket
            await websocket_manager.send_agent_thought(
                user_id=workflow_execution.initiated_by,
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                workflow_id=workflow_execution.id,
                workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                thought_type='thought',
                message=f"Processing simple task execution with DSPy:\nTask: {task.name}\nObjective: {task.objective}",
                metadata={
                    'step': 'dspy_simple_execution',
                    'tool': 'dspy_simple_module',
                    'confidence': 0.8,
                    'reasoning': f"Using DSPy simple execution for task {task.name}",
                    'context': {'task_id': task.id}
                }
            )
            
            # Use DSPy to execute task
            with dspy.context(lm=self.llm):
                prediction = self.simple_executor(
                    task_name=task.name,
                    task_description=task.description or "",
                    task_objective=task.objective or "Complete the task successfully",
                    completion_criteria=task.completion_criteria or "Task meets objective requirements",
                    agent_name=self.agent_node.name,
                    agent_role=self.agent_node.role.value,
                    agent_capabilities=agent_capabilities,
                    available_tools=available_tools,
                    execution_context=execution_context_str
                )
            
            # Send DSPy response to WebSocket
            await websocket_manager.send_agent_thought(
                user_id=workflow_execution.initiated_by,
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                workflow_id=workflow_execution.id,
                workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                thought_type='action',
                message=f"DSPy Simple Execution Result:\n{prediction.execution_result}",
                metadata={
                    'step': 'dspy_simple_response',
                    'tool': 'dspy_simple_module',
                    'confidence': float(prediction.confidence_score),
                    'reasoning': prediction.reasoning,
                    'context': {'success': prediction.success_status}
                }
            )
            
            # Convert DSPy prediction to expected format
            success = prediction.success_status.lower() == 'true'
            confidence = float(prediction.confidence_score) if prediction.confidence_score.replace('.', '').isdigit() else 0.8
            
            result = {
                'success': success,
                'strategy': 'simple',
                'confidence': confidence,
                'execution_summary': f"Task '{task.name}' executed using DSPy simple strategy by {self.agent_node.name}",
                'reasoning': prediction.reasoning,
                'response': prediction.execution_result,
                'task_id': task.id,
                'agent_id': self.agent_node.id,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                "DSPy simple strategy execution completed",
                task_id=task.id,
                agent_id=self.agent_node.id,
                success=success,
                confidence=confidence
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "DSPy simple strategy execution failed",
                task_id=task.id,
                agent_id=self.agent_node.id,
                error=str(e)
            )
            
            return {
                'success': False,
                'strategy': 'simple',
                'confidence': 0.0,
                'error': f"DSPy execution failed: {str(e)}",
                'task_id': task.id,
                'agent_id': self.agent_node.id
            }
    
    async def _execute_with_openai_simple(self,
                                         task: WorkflowTask,
                                         execution_context: Dict[str, Any],
                                         workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Fallback execution using direct OpenAI client calls"""
        
        self.logger.info(
            "Executing task with OpenAI simple strategy (fallback)",
            task_id=task.id,
            agent_id=self.agent_node.id
        )
        
        simple_prompt = self._build_simple_prompt(task, execution_context, workflow_execution)
        
        # Send agent thought to WebSocket
        await websocket_manager.send_agent_thought(
            user_id=workflow_execution.initiated_by,
            agent_id=self.agent_node.id,
            agent_name=self.agent_node.name,
            workflow_id=workflow_execution.id,
            workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
            thought_type='thought',
            message=f"Simple prompt processing:\n{self._format_chat_messages_for_display(simple_prompt)}",
            metadata={
                'step': 'Simple prompt',
                'tool': 'simple_strategy',
                'confidence': 0.8,
                'reasoning': f"Processing simple prompt for task {task.name}",
                'context': {'prompt_length': len(simple_prompt)}
            }
        )
        
        try:
            completion = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=simple_prompt,
                max_tokens=1500,
                temperature=0.5
            )
            
            response_text = completion.choices[0].message.content
            
            await websocket_manager.send_agent_thought(
                user_id=workflow_execution.initiated_by,
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                workflow_id=workflow_execution.id,
                workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                thought_type='action',
                message=f"LLM response: {response_text}",
                metadata={
                    'step': 'simple_prompt_response',
                    'tool': 'gpt-3.5-turbo',
                    'confidence': 0.9,
                    'reasoning': 'LLM generated response',
                    'context': {'response_length': len(response_text), 'model': 'gpt-4'}
                }
            )
            
            result = {
                'success': True,
                'strategy': 'simple',
                'confidence': 0.8,
                'execution_summary': f"Task '{task.name}' executed directly by {self.agent_node.name}",
                'response': response_text,
                'task_id': task.id,
                'agent_id': self.agent_node.id,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(
                "OpenAI simple strategy execution failed",
                task_id=task.id,
                agent_id=self.agent_node.id,
                error=str(e)
            )
            
            return {
                'success': False,
                'strategy': 'simple',
                'confidence': 0.0,
                'error': str(e),
                'task_id': task.id,
                'agent_id': self.agent_node.id
            }
    
    async def _execute_with_chain_of_thought(self,
                                           task: WorkflowTask,
                                           execution_context: Dict[str, Any],
                                           workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using Chain of Thought reasoning"""
        
        # Try DSPy first, fallback to OpenAI client if needed
        if self.cot_planner is not None and self.llm is not None:
            return await self._execute_with_dspy_cot(task, execution_context, workflow_execution)
        elif self.llm_client:
            return await self._execute_with_openai_cot(task, execution_context, workflow_execution)
        else:
            return await self._fallback_execution(task, execution_context)
    
    async def _execute_with_dspy_cot(self,
                                    task: WorkflowTask,
                                    execution_context: Dict[str, Any],
                                    workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using DSPy ChainOfThoughtModule"""
        
        self.logger.info(
            "Executing task with DSPy Chain of Thought strategy",
            task_id=task.id,
            agent_id=self.agent_node.id
        )
        
        try:
            # Prepare inputs for DSPy signature
            agent_capabilities = json.dumps([cap.name for cap in self.agent_node.capabilities])
            available_tools = json.dumps(list(self.available_tools.keys()))
            execution_context_str = json.dumps(execution_context, default=str)
            
            # Send agent thought to WebSocket
            await websocket_manager.send_agent_thought(
                user_id=workflow_execution.initiated_by,
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                workflow_id=workflow_execution.id,
                workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                thought_type='thought',
                message=f"Planning task execution with DSPy Chain of Thought:\nTask: {task.name}\nObjective: {task.objective}",
                metadata={
                    'step': 'dspy_cot_planning',
                    'tool': 'dspy_cot_module',
                    'confidence': 0.8,
                    'reasoning': f"Using DSPy Chain of Thought planning for task {task.name}",
                    'context': {'task_id': task.id}
                }
            )
            
            # Use DSPy to plan task execution
            with dspy.context(lm=self.llm):
                prediction = self.cot_planner(
                    task_name=task.name,
                    task_description=task.description or "",
                    task_objective=task.objective or "Complete the task successfully",
                    completion_criteria=task.completion_criteria or "Task meets objective requirements",
                    agent_capabilities=agent_capabilities,
                    available_tools=available_tools,
                    execution_context=execution_context_str
                )
            
            # Parse reasoning steps from DSPy output
            reasoning_steps = []
            try:
                reasoning_steps_data = json.loads(prediction.reasoning_steps)
                if isinstance(reasoning_steps_data, list):
                    reasoning_steps = reasoning_steps_data
            except (json.JSONDecodeError, AttributeError):
                reasoning_steps = [{"step": 1, "reasoning": prediction.reasoning_steps}]
            
            # Send DSPy response to WebSocket
            await websocket_manager.send_agent_thought(
                user_id=workflow_execution.initiated_by,
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                workflow_id=workflow_execution.id,
                workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                thought_type='action',
                message=f"DSPy CoT Planning Result:\nPlan: {prediction.execution_plan}\nTools: {prediction.required_tools}",
                metadata={
                    'step': 'dspy_cot_response',
                    'tool': 'dspy_cot_module',
                    'confidence': float(prediction.confidence_score),
                    'reasoning': f"Generated execution plan with {len(reasoning_steps)} steps",
                    'context': {'plan_length': len(prediction.execution_plan)}
                }
            )
            
            # Convert DSPy prediction to expected format
            confidence = float(prediction.confidence_score) if prediction.confidence_score.replace('.', '').isdigit() else 0.8
            
            result = {
                'success': True,
                'strategy': 'chain_of_thought',
                'confidence': confidence,
                'execution_summary': f"Task '{task.name}' planned using DSPy Chain of Thought by {self.agent_node.name}",
                'reasoning_steps': reasoning_steps,
                'execution_plan': prediction.execution_plan,
                'required_tools': prediction.required_tools,
                'response': prediction.execution_plan,
                'task_id': task.id,
                'agent_id': self.agent_node.id,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                "DSPy Chain of Thought execution completed",
                task_id=task.id,
                agent_id=self.agent_node.id,
                confidence=confidence,
                reasoning_steps_count=len(reasoning_steps)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "DSPy Chain of Thought execution failed",
                task_id=task.id,
                agent_id=self.agent_node.id,
                error=str(e)
            )
            
            return {
                'success': False,
                'strategy': 'chain_of_thought',
                'confidence': 0.0,
                'error': f"DSPy CoT execution failed: {str(e)}",
                'task_id': task.id,
                'agent_id': self.agent_node.id
            }
    
    async def _execute_with_openai_cot(self,
                                      task: WorkflowTask,
                                      execution_context: Dict[str, Any],
                                      workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Fallback Chain of Thought execution using direct OpenAI client calls"""
        
        self.logger.info(
            "Executing task with OpenAI Chain of Thought strategy (fallback)",
            task_id=task.id,
            agent_id=self.agent_node.id
        )
        
        # Build Chain of Thought prompt
        cot_prompt = self._build_cot_prompt(task, execution_context, workflow_execution)
        
        reasoning_steps = []
        final_result = {}
        
        for step in range(self.agent_node.max_iterations):
            try:
                # Get reasoning step from LLM
                completion = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": cot_prompt},
                        {"role": "user", "content": f"Step {step + 1}: Reason through the next action needed to complete this task."}
                    ],
                    temperature=0.3,
                    max_tokens=800
                )
                
                reasoning_text = completion.choices[0].message.content
                reasoning_steps.append({
                    'step': step + 1,
                    'reasoning': reasoning_text,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Parse reasoning to extract action
                action_result = await self._parse_and_execute_reasoning(reasoning_text, task, execution_context)
                
                if action_result.get('completed', False):
                    final_result = {
                        'success': True,
                        'reasoning_steps': reasoning_steps,
                        'final_action': action_result,
                        'confidence': action_result.get('confidence', 0.8),
                        'strategy': 'chain_of_thought'
                    }
                    break
                
                # Update context for next iteration
                execution_context['last_action'] = action_result
                
            except Exception as e:
                self.logger.error("CoT reasoning step failed", step=step, error=str(e))
                break
        
        if not final_result:
            final_result = {
                'success': False,
                'reasoning_steps': reasoning_steps,
                'error': 'Could not complete task within max iterations',
                'confidence': 0.3,
                'strategy': 'chain_of_thought'
            }
        
        return final_result
    
    async def _execute_with_react(self,
                                task: WorkflowTask,
                                execution_context: Dict[str, Any],
                                workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using ReAct (Reasoning + Acting) strategy"""
        
        # Try DSPy first, fallback to OpenAI client if needed
        if self.llm is not None:
            return await self._execute_with_dspy_react(task, execution_context, workflow_execution)
        elif self.llm_client:
            return await self._execute_with_openai_react(task, execution_context, workflow_execution)
        else:
            return await self._fallback_execution(task, execution_context)
    
    # A requester is an async function that takes a HumanInputRequest
    # and handles the outbound request to humans, allowing them to provide a response.
    # It should resolve the request by calling request.set_response(response).
    Requester = Callable[[HumanInputRequest], Awaitable[None]]

    def _human_in_the_loop(self, requester: Requester) -> dspy.Tool:
        def ask_human(question: str) -> str:
            """Synchronous wrapper for async human interaction"""
            
            async def async_ask_human():
                request = HumanInputRequest(question)

                # Let requester handle the outbound request
                await requester(request)

                # Wait for response (resolved by requester or external system)
                response = await request.response()
                return response
            
            # Run the async function synchronously using asyncio
            import asyncio
            
            try:
                # Check if there's already an event loop running
                loop = asyncio.get_running_loop()
                # If we're in an async context, we need to be careful
                # Use asyncio.run_coroutine_threadsafe to avoid "RuntimeError: cannot be called from a running event loop"
                import threading
                import concurrent.futures
                
                def run_in_thread():
                    # Instead of creating a new event loop, schedule on the main event loop
                    # Use the main loop to ensure WebSocket connections work properly
                    try:
                        future = asyncio.run_coroutine_threadsafe(async_ask_human(), loop)
                        return future.result(timeout=320)
                    except Exception as e:
                        self.logger.error("Failed to run async_ask_human on main loop", error=str(e))
                        raise
                
                # Run in a separate thread to avoid blocking the current event loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=320)  # 5 min + buffer
                    
            except RuntimeError:
                # No event loop is running, safe to use asyncio.run
                return asyncio.run(async_ask_human())

        return dspy.Tool(ask_human)

    def _create_dspy_tools(self, task: WorkflowTask, execution_context: Dict[str, Any], workflow_execution: WorkflowExecution) -> List[Callable]:
        """Create non-blocking tools for DSPy ReAct execution"""
        tools = []
        
        # Add available workflow tools
        for tool_name, tool_func in self.available_tools.items():
            def create_tool_wrapper(name, func):
                def sync_tool_wrapper(*args, **kwargs):
                    """Synchronous wrapper for workflow tools"""
                    try:
                        # For now, return a placeholder since these tools may be async
                        return f"Tool {name} is available for execution. Call this tool when needed."
                    except Exception as e:
                        return f"Tool {name} failed: {str(e)}"
                
                sync_tool_wrapper.__name__ = name
                sync_tool_wrapper.__doc__ = f"Execute the {name} tool"
                return sync_tool_wrapper
            
            tools.append(create_tool_wrapper(tool_name, tool_func))
        
        # Clean Human-in-the-Loop Tools Suite
        # Simple async tools that send WebSocket messages and wait for responses
        
        async def ask_user_question(question: str) -> str:
            """Ask the user a question via WebSocket and wait for response"""
            from app.services.websocket_manager import websocket_manager
            import uuid
            import asyncio
            
            request_id = str(uuid.uuid4())
            
            # Register pending request
            websocket_manager.pending_responses[request_id] = {
                'execution_id': self.current_execution_id,
                'task_id': task.id,
                'question': question,
                'user_id': workflow_execution.initiated_by,
                'created_at': datetime.utcnow().isoformat(),
                'timeout_seconds': 300,
                'request_type': 'question'
            }
            
            # Send WebSocket message
            await websocket_manager.send_chat_message(
                execution_id=self.current_execution_id,
                message_content=f"❓ **Question Required**\n\n{question}\n\n*Please respond in the chat. Request ID: `{request_id[:8]}...`*",
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                task_id=task.id,
                task_name=task.name,
                message_type='user_request',
                requires_response=True,
                metadata={'request_id': request_id, 'request_type': 'question'}
            )
            
            # Wait for response with async polling
            for _ in range(60):  # 5 minutes (600 * 0.5s)
                if request_id in websocket_manager.user_responses:
                    response = websocket_manager.user_responses.pop(request_id)
                    websocket_manager.pending_responses.pop(request_id, None)
                    return response
                await asyncio.sleep(0.5)
            
            # Timeout
            websocket_manager.pending_responses.pop(request_id, None)
            return f"[TIMEOUT] No response received for question: {question}"
        
        async def request_user_approval(action_description: str) -> str:
            """Request user approval via WebSocket and wait for response"""
            from app.services.websocket_manager import websocket_manager
            import uuid
            import asyncio
            
            request_id = str(uuid.uuid4())
            
            # Register pending request
            websocket_manager.pending_responses[request_id] = {
                'execution_id': self.current_execution_id,
                'task_id': task.id,
                'question': f"Approval required: {action_description}",
                'user_id': workflow_execution.initiated_by,
                'created_at': datetime.utcnow().isoformat(),
                'timeout_seconds': 300,
                'request_type': 'approval'
            }
            
            # Send WebSocket message
            await websocket_manager.send_chat_message(
                execution_id=self.current_execution_id,
                message_content=f"✋ **Approval Required**\n\n{action_description}\n\nRespond with 'approve', 'reject', or provide specific instructions.\n\n*Request ID: `{request_id[:8]}...`*",
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                task_id=task.id,
                task_name=task.name,
                message_type='user_request',
                requires_response=True,
                metadata={'request_id': request_id, 'request_type': 'approval'}
            )
            
            # Wait for response with async polling
            for _ in range(60):  # 5 minutes (600 * 0.5s)
                if request_id in websocket_manager.user_responses:
                    response = websocket_manager.user_responses.pop(request_id)
                    websocket_manager.pending_responses.pop(request_id, None)
                    
                    # Process approval response
                    response_lower = response.lower()
                    if 'approve' in response_lower or 'yes' in response_lower:
                        return f"APPROVED: {response}"
                    elif 'reject' in response_lower or 'no' in response_lower:
                        return f"REJECTED: {response}"
                    else:
                        return f"USER_INSTRUCTIONS: {response}"
                await asyncio.sleep(0.5)
            
            # Timeout
            websocket_manager.pending_responses.pop(request_id, None)
            return f"[TIMEOUT] No approval response received for: {action_description}"
        
        async def request_missing_information(info_type: str, context: str = "") -> str:
            """Request missing information via WebSocket and wait for response"""
            from app.services.websocket_manager import websocket_manager
            import uuid
            import asyncio
            
            request_id = str(uuid.uuid4())
            prompt = f"I need additional information: {info_type}"
            if context:
                prompt += f"\n\nContext: {context}"
            
            # Register pending request
            websocket_manager.pending_responses[request_id] = {
                'execution_id': self.current_execution_id,
                'task_id': task.id,
                'question': prompt,
                'user_id': workflow_execution.initiated_by,
                'created_at': datetime.utcnow().isoformat(),
                'timeout_seconds': 300,
                'request_type': 'information'
            }
            
            # Send WebSocket message
            await websocket_manager.send_chat_message(
                execution_id=self.current_execution_id,
                message_content=f"📝 **Information Required**\n\n{prompt}\n\n*Please provide the requested information. Request ID: `{request_id[:8]}...`*",
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                task_id=task.id,
                task_name=task.name,
                message_type='user_request',
                requires_response=True,
                metadata={'request_id': request_id, 'request_type': 'information'}
            )
            
            # Wait for response with async polling
            for _ in range(60):  # 5 minutes (600 * 0.5s)
                if request_id in websocket_manager.user_responses:
                    response = websocket_manager.user_responses.pop(request_id)
                    websocket_manager.pending_responses.pop(request_id, None)
                    return f"User provided {info_type}: {response}"
                await asyncio.sleep(0.5)
            
            # Timeout
            websocket_manager.pending_responses.pop(request_id, None)
            return f"[TIMEOUT] No information received for: {info_type}"
        
        def complete_task(result: str) -> str:
            """Mark the current task as completed with the given result."""
            try:
                from app.services.websocket_manager import websocket_manager
                
                # Send completion message to WebSocket
                websocket_manager.queue_chat_message_from_thread(
                    execution_id=self.current_execution_id,
                    message_content=f"✅ **Task Completed**\n\n**Task:** {task.name}\n\n**Result:** {result}",
                    agent_id=self.agent_node.id,
                    agent_name=self.agent_node.name,
                    task_id=task.id,
                    task_name=task.name,
                    message_type='task_completion',
                    requires_response=False,
                    metadata={
                        'task_completed': True,
                        'result': result
                    }
                )
                
                return f"Task '{task.name}' completed successfully with result: {result}"
                
            except Exception as e:
                return f"Task '{task.name}' completed with result: {result} (WebSocket notification failed: {str(e)})"
        
        # Create DSPy Tool objects for async human-in-the-loop functions
        # DSPy will handle the async execution properly with acall()
        human_tools = [
            dspy.Tool(ask_user_question, name="ask_user_question", 
                     desc="Ask the user a question and wait for their response"),
            dspy.Tool(request_user_approval, name="request_user_approval", 
                     desc="Request user approval for an action"),
            dspy.Tool(request_missing_information, name="request_missing_information", 
                     desc="Request additional information from the user"),
            dspy.Tool(complete_task, name="complete_task", 
                     desc="Mark the current task as completed with the given result")
        ]
        
        tools.extend(human_tools)
        
        return tools

    async def _execute_with_dspy_react(self,
                                      task: WorkflowTask,
                                      execution_context: Dict[str, Any],
                                      workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using DSPy ReAct directly"""
        
        self.logger.info(
            "Executing task with DSPy ReAct strategy",
            task_id=task.id,
            agent_id=self.agent_node.id
        )
        
        try:
            # Send initial agent thought to WebSocket
            # await websocket_manager.send_agent_thought(
            #     user_id=workflow_execution.initiated_by,
            #     agent_id=self.agent_node.id,
            #     agent_name=self.agent_node.name,
            #     workflow_id=workflow_execution.id,
            #     workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
            #     thought_type='thought',
            #     message=f"Starting DSPy ReAct execution for task: {task.name}",
            #     metadata={
            #         'step': 'react_initialization',
            #         'tool': 'dspy_react',
            #         'confidence': 0.9,
            #         'reasoning': "Initializing ReAct agent with available tools",
            #         'context': {'task_objective': task.objective}
            #     }
            # )
            
            # Create non-blocking tools for ReAct
            print("===> Creating non-blocking tools for DSPy ReAct")
            tools = self._create_dspy_tools(task, execution_context, workflow_execution)
            print("===> Created non-blocking tools for DSPy ReAct")
            # Initialize DSPy ReAct with tools and signature
            react_agent = dspy.ReAct(TaskExecutionSignature, tools=tools, max_iters=1)
            print("===> Initialized DSPy ReAct agent with tools")  
            # Prepare context information
            context_info = {
                'available_tools': list(self.available_tools.keys()),
                'execution_context': execution_context,
                'agent_capabilities': self.agent_node.capabilities if hasattr(self.agent_node, 'capabilities') else []
            }
            print("===> Prepared context information for DSPy ReAct execution")
            # Execute with DSPy ReAct using async call
            with dspy.context(lm=self.llm):
                result = await react_agent.acall(
                    task_name=task.name,
                    task_objective=task.objective or "Complete the task successfully", 
                    current_context=json.dumps(context_info, default=str)
                )
            print("===> DSPy ReAct execution completed")   
            # Send completion thought to WebSocket
            await websocket_manager.send_agent_thought(
                user_id=workflow_execution.initiated_by,
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                workflow_id=workflow_execution.id,
                workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                thought_type='observation',
                message=f"DSPy ReAct completed task execution:\n\nResult: {result.response}",
                metadata={
                    'step': 'react_completion',
                    'tool': 'dspy_react',
                    'confidence': 0.9,
                    'reasoning': "ReAct agent completed task execution",
                    'context': {'result': result.response}
                }
            )
            
            # Convert DSPy Prediction result to JSON-serializable format
            def make_serializable(obj):
                """Convert any object to JSON-serializable format"""
                if isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items() if not str(k).startswith('_')}
                elif hasattr(obj, '__dict__'):
                    return {k: make_serializable(v) for k, v in obj.__dict__.items() if not str(k).startswith('_')}
                else:
                    return str(obj)
            
            react_result_serializable = make_serializable({
                'response': getattr(result, 'response', 'No response available'),
                'completions': getattr(result, 'completions', []),
                'prediction_data': {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
            })
            
            return {
                'success': True,
                'strategy': 'react',
                'confidence': 0.9,
                'execution_summary': f"Task '{task.name}' completed using DSPy ReAct",
                'response': result.response,
                'task_id': task.id,
                'agent_id': self.agent_node.id,
                'completed_at': datetime.utcnow().isoformat(),
                'react_result': react_result_serializable
            }
            
        except Exception as e:
            self.logger.error("DSPy ReAct execution failed", task_id=task.id, error=str(e))
            
            # Send error thought to WebSocket
            await websocket_manager.send_agent_thought(
                user_id=workflow_execution.initiated_by,
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                workflow_id=workflow_execution.id,
                workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                thought_type='error',
                message=f"DSPy ReAct execution failed: {str(e)}",
                metadata={
                    'step': 'react_error',
                    'tool': 'dspy_react',
                    'confidence': 0.1,
                    'reasoning': "ReAct agent encountered an error",
                    'context': {'error': str(e)}
                }
            )
            
            return {
                'success': False,
                'strategy': 'react',
                'confidence': 0.1,
                'error': f'DSPy ReAct execution failed: {str(e)}',
                'task_id': task.id,
                'agent_id': self.agent_node.id
            }
    
    async def _execute_with_openai_react(self,
                                        task: WorkflowTask,
                                        execution_context: Dict[str, Any],
                                        workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Fallback ReAct execution using direct OpenAI client calls"""
        
        self.logger.info(
            "Executing task with OpenAI ReAct strategy (fallback)",
            task_id=task.id,
            agent_id=self.agent_node.id
        )
        
        react_history = []
        observations = []
        
        for iteration in range(self.agent_node.max_iterations):
            try:
                # ReAct prompt with current state
                react_prompt = self._build_react_prompt(task, execution_context, react_history, observations)
                
                # Send agent thought to WebSocket
                await websocket_manager.send_agent_thought(
                    user_id=workflow_execution.initiated_by,
                    agent_id=self.agent_node.id,
                    agent_name=self.agent_node.name,
                    workflow_id=workflow_execution.id,
                    workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                    thought_type='thought',
                    message=f"ReAct iteration {iteration + 1}: Analyzing prompt and planning next action\n\n{self._format_chat_messages_for_display([{'role': 'system', 'content': react_prompt}])}",
                    metadata={
                        'step': f'iteration_{iteration + 1}',
                        'tool': 'react_reasoning',
                        'confidence': 0.8,
                        'reasoning': f"Processing ReAct prompt for iteration {iteration + 1}",
                        'context': {'prompt_length': len(react_prompt)}
                    }
                )
                
                # Get thought and action from LLM
                completion = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": react_prompt},
                        {"role": "user", "content": "Think about what action to take next, then take it."}
                    ],
                    temperature=0.3,
                    max_tokens=600
                )
                
                response = completion.choices[0].message.content
                
                # Send agent response to WebSocket
                await websocket_manager.send_agent_thought(
                    user_id=workflow_execution.initiated_by,
                    agent_id=self.agent_node.id,
                    agent_name=self.agent_node.name,
                    workflow_id=workflow_execution.id,
                    workflow_name=f"Workflow-{workflow_execution.workflow_template_id[:8]}...",
                    thought_type='action',
                    message=f"ReAct iteration {iteration + 1}: Generated response\n\n {response}",
                    metadata={
                        'step': f'iteration_{iteration + 1}',
                        'tool': 'gpt-3.5-turbo',
                        'confidence': 0.9,
                        'reasoning': f"LLM generated response for iteration {iteration + 1}",
                        'context': {'response_length': len(response), 'model': 'gpt-3.5-turbo'}
                    }
                )
                
                # Parse thought and action
                thought, action = self._parse_react_response(response)
                
                # Execute action
                action_result = await self._execute_react_action(action, task, execution_context, workflow_execution)
                
                # Record step
                react_step = {
                    'iteration': iteration + 1,
                    'thought': thought,
                    'action': action,
                    'observation': action_result.get('observation', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }
                react_history.append(react_step)
                observations.append(action_result.get('observation', ''))
                
                # Check if task completed
                if action_result.get('completed', False):
                    return {
                        'success': True,
                        'react_history': react_history,
                        'final_result': action_result,
                        'confidence': action_result.get('confidence', 0.8),
                        'strategy': 'react'
                    }
                
                # Check if need human interaction
                if action_result.get('requires_human', False):
                    # Note: Human-in-the-Loop functionality is handled by DSPy ReAct tools
                    # In fallback OpenAI ReAct mode, provide mock response to continue execution
                    human_response = "Proceeding with default behavior (Human-in-the-Loop not available in fallback mode)"
                    observations.append(f"Human response: {human_response}")
                
            except Exception as e:
                self.logger.error("ReAct iteration failed", iteration=iteration, error=str(e))
                observations.append(f"Error in iteration {iteration}: {str(e)}")
        
        return {
            'success': False,
            'react_history': react_history,
            'error': 'Could not complete task within max iterations',
            'confidence': 0.3,
            'strategy': 'react'
        }
    
    async def _execute_with_hybrid_strategy(self,
                                          task: WorkflowTask,
                                          execution_context: Dict[str, Any],
                                          workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using hybrid CoT + ReAct strategy"""
        
        # First use CoT for planning
        planning_result = await self._plan_with_cot(task, execution_context)
        
        if not planning_result.get('success', False):
            return planning_result
        
        # Then use ReAct for execution
        execution_context['cot_plan'] = planning_result['plan']
        react_result = await self._execute_with_react(task, execution_context, workflow_execution)
        
        # Combine results
        return {
            'success': react_result.get('success', False),
            'planning_phase': planning_result,
            'execution_phase': react_result,
            'confidence': min(planning_result.get('confidence', 0.5), react_result.get('confidence', 0.5)),
            'strategy': 'hybrid'
        }
    
    async def _request_human_approval(self,
                                    task: WorkflowTask,
                                    task_result: Dict[str, Any],
                                    workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Request human approval for task completion"""
        
        approval_request = HumanInteractionRequest(
            execution_id=workflow_execution.id,
            task_id=task.id,
            agent_id=self.agent_node.id,
            interaction_type="approval",
            message=f"Please review and approve the completion of task '{task.name}'",
            context={
                'task_objective': task.objective,
                'completion_criteria': task.completion_criteria,
                'agent_result': task_result,
                'confidence': task_result.get('confidence', 0.0)
            },
            options=["approve", "reject", "modify"],
            response_deadline=datetime.utcnow() + timedelta(seconds=self.agent_node.approval_timeout_seconds)
        )
        
        # Store pending approval
        self.pending_approvals[approval_request.id] = approval_request
        
        # Wait for human approval (mock implementation for testing)
        # Note: This is separate from Human-in-the-Loop tools and handles task completion approval
        await asyncio.sleep(1)  # Simulate waiting for human approval
        
        # Mock approval response for testing
        return {
            'status': 'approved',
            'feedback': {
                'human_comments': 'Task completed satisfactorily',
                'approval_timestamp': datetime.utcnow().isoformat()
            }
        }
    
    
    async def handoff_to_agent(self,
                             target_agent_id: str,
                             task: WorkflowTask,
                             handoff_context: Dict[str, Any],
                             workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Hand off task to another agent"""
        
        if target_agent_id not in self.agent_node.can_handoff_to:
            return {
                'success': False,
                'error': f'Agent {self.agent_node.id} cannot handoff to {target_agent_id}',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Find target agent in organization
        target_agent = None
        for agent in self.organization.agents:
            if agent.id == target_agent_id:
                target_agent = agent
                break
        
        if not target_agent:
            return {
                'success': False,
                'error': f'Target agent {target_agent_id} not found in organization',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Log handoff
        handoff_record = {
            'from_agent': self.agent_node.id,
            'to_agent': target_agent_id,
            'task_id': task.id,
            'handoff_reason': handoff_context.get('reason', 'Agent capability match'),
            'context': handoff_context,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        workflow_execution.agent_actions.append(handoff_record)
        
        self.logger.info(
            "Task handed off to another agent",
            target_agent=target_agent_id,
            task_id=task.id,
            reason=handoff_context.get('reason', 'Unknown')
        )
        
        return {
            'success': True,
            'handoff_record': handoff_record,
            'target_agent': target_agent.dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Tool implementations
    async def _tool_database_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute database query tool"""
        try:
            # Mock database query - in real implementation would use actual database
            result = f"Query executed: {query}"
            return {
                'success': True,
                'result': result,
                'observation': f"Database query completed successfully"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'observation': f"Database query failed: {str(e)}"
            }
    
    async def _tool_api_request(self, url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Execute API request tool"""
        try:
            # Mock API request - in real implementation would use actual HTTP client
            result = f"API {method} request to {url} completed"
            return {
                'success': True,
                'result': result,
                'observation': f"API request successful"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'observation': f"API request failed: {str(e)}"
            }
    
    async def _tool_human_interaction(self, message: str, options: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Human interaction tool"""
        return {
            'success': True,
            'requires_human': True,
            'message': message,
            'options': options or [],
            'observation': f"Human interaction requested: {message}"
        }
    
    async def _tool_agent_handoff(self, target_agent: str, reason: str, **kwargs) -> Dict[str, Any]:
        """Agent handoff tool"""
        return {
            'success': True,
            'requires_handoff': True,
            'target_agent': target_agent,
            'reason': reason,
            'observation': f"Handoff requested to {target_agent}: {reason}"
        }

    async def _tool_task_validation(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """Task validation tool"""
        return {
            'success': True,
            'task_id': task_id,
            'observation': f"Task {task_id} validated successfully"
        }
    
    async def _tool_file_operation(self, operation: str = "read", file_path: str = "", **kwargs) -> Dict[str, Any]:
        """File operation tool"""
        return {
            'success': True,
            'operation': operation,
            'file_path': file_path,
            'observation': f"File operation '{operation}' performed on {file_path}"
        }
    
    async def _tool_knowledge_search(self, query: str = "", **kwargs) -> Dict[str, Any]:
        """Knowledge search tool"""
        return {
            'success': True,
            'query': query,
            'observation': f"Knowledge search performed for: {query}"
        }
    
    async def _tool_notification(self, message: str = "", recipient: str = "", **kwargs) -> Dict[str, Any]:
        """Notification tool"""
        return {
            'success': True,
            'message': message,
            'recipient': recipient,
            'observation': f"Notification sent to {recipient}: {message}"
        }
    
    async def _generic_tool_execution(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Generic tool execution wrapper"""
        return {
            'success': True,
            'tool_name': tool_name,
            'parameters': kwargs,
            'observation': f"Tool {tool_name} executed with parameters: {kwargs}"
        }
    
    # Helper methods for building prompts and parsing responses
    def _build_simple_prompt(self, task: WorkflowTask, context: Dict[str, Any], workflow: WorkflowExecution) -> List[Dict[str, str]]:
        """Build simple execution prompt"""
        return [
            {
                "role": "system",
                "content": f"You are {self.agent_node.name}, a {self.agent_node.role.value} agent in an enterprise automation workflow."
            },
            {
                "role": "user",
                "content": f"""TASK DETAILS:
- Name: {task.name}
- Description: {task.description}
- Objective: {task.objective or 'Complete the task successfully'}
- Completion Criteria: {task.completion_criteria or 'Task meets objective requirements'}
- Context: {json.dumps(context, default=str, indent=2)}
- Available Tools: {', '.join(self.available_tools.keys())}
- Agent Capabilities: {[cap.name for cap in self.agent_node.capabilities]}
- Current Time: {datetime.utcnow().isoformat()}
            """
            }
        ]

    def _build_cot_prompt(self, task: WorkflowTask, context: Dict[str, Any], workflow: WorkflowExecution) -> str:
        """Build Chain of Thought prompt"""
        return f"""You are {self.agent_node.name}, a {self.agent_node.role.value} agent in an enterprise automation workflow.

TASK DETAILS:
- Name: {task.name}
- Description: {task.description}
- Objective: {task.objective or 'Complete the task successfully'}
- Completion Criteria: {task.completion_criteria or 'Task meets objective requirements'}

AVAILABLE TOOLS: {', '.join(self.available_tools.keys())}

AGENT CAPABILITIES: {[cap.name for cap in self.agent_node.capabilities]}

CONTEXT: {json.dumps(context, default=str, indent=2)}

Think step by step about how to complete this task. Break down your reasoning into clear steps and identify the specific actions needed. Consider:
1. What information do you need?
2. What tools should you use?
3. Do you need human input or approval?
4. Should you hand off to another agent?
5. How will you know when the task is complete?

Provide your reasoning in a clear, step-by-step format."""

    def _build_react_prompt(self, task: WorkflowTask, context: Dict[str, Any], history: List[Dict], observations: List[str]) -> str:
        """Build ReAct prompt"""
        history_text = "\n".join([f"Thought: {step['thought']}\nAction: {step['action']}\nObservation: {step['observation']}" for step in history[-3:]])
        
        return f"""You are {self.agent_node.name}, a {self.agent_node.role.value} agent using ReAct (Reasoning + Acting) approach.

TASK: {task.name} - {task.description}
OBJECTIVE: {task.objective or 'Complete the task successfully'}

AVAILABLE TOOLS: {', '.join(self.available_tools.keys())}

PREVIOUS ACTIONS:
{history_text}

INSTRUCTIONS:
1. Think about the current situation and what action to take next
2. Choose ONE specific action to take
3. Format your response as:
   Thought: [your reasoning]
   Action: [specific action with parameters]

Available actions: {', '.join(self.available_tools.keys())}, complete_task, request_human_help, handoff_to_agent"""

    # Additional helper methods would be implemented here for parsing responses, etc.
    
    def _format_chat_messages_for_display(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat message format to readable text for display"""
        formatted_parts = []
        for msg in messages:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            content = content.replace('.', '\n') # Clean up newlines for display
            formatted_parts.append(f"[{role}]: {content}")
        return "\n\n".join(formatted_parts)
    
    def _parse_react_response(self, response: str) -> Tuple[str, str]:
        """Parse ReAct response into thought and action"""
        lines = response.strip().split('\n')
        thought = ""
        action = ""
        
        for line in lines:
            if line.startswith("Thought:"):
                thought = line.replace("Thought:", "").strip()
            elif line.startswith("Action:"):
                action = line.replace("Action:", "").strip()
        
        return thought, action
    
    async def _execute_react_action(self, action: str, task: WorkflowTask, context: Dict[str, Any], workflow_execution: Optional['WorkflowExecution'] = None) -> Dict[str, Any]:
        """Execute a ReAct action"""
        if action.startswith("complete_task"):
            return {
                'completed': True,
                'observation': 'Task marked as completed',
                'confidence': 0.9
            }
        
        # Note: Human-in-the-Loop functionality is now handled by DSPy ReAct tools
        # Legacy user interaction actions are no longer supported in fallback ReAct mode
        if action.startswith("request_user_info") or action.startswith("ask_user") or action.startswith("seek_clarification"):
            return {
                'completed': False,
                'observation': f'User information request not supported in fallback ReAct mode: {action}',
                'confidence': 0.3
            }
        
        if action.startswith("human_interaction") or action.startswith("request_human_help"):
            return {
                'completed': False,
                'observation': f'Human interaction request not supported in fallback ReAct mode: {action}',
                'confidence': 0.3
            }
        
        # Parse tool calls and execute
        for tool_name in self.available_tools.keys():
            if action.startswith(tool_name):
                return await self.available_tools[tool_name]()
        
        return {
            'completed': False,
            'observation': f'Unknown action: {action}',
            'confidence': 0.1
        }
    
    async def _wait_for_user_response(self, task: WorkflowTask, action_result: Dict[str, Any], workflow_execution: Optional['WorkflowExecution']) -> str:
        """Wait for user response to an information request using Human-in-the-Loop pattern"""
        
        self.logger.info("_wait_for_user_response method STARTED - async coroutine executing")
        
        if not workflow_execution:
            self.logger.error("_wait_for_user_response: No workflow execution provided")
            raise ValueError("Workflow execution is required for user response requests")
        
        question = action_result.get('question', 'Information request')
        timeout_seconds = action_result.get('timeout', 300)  # Default 5 minutes
        
        self.logger.info(f"_wait_for_user_response: Processing question with {timeout_seconds}s timeout")
        
        self.logger.info(
            "Creating user response request",
            task_id=task.id,
            agent_id=self.agent_node.id,
            question=question,
            timeout=timeout_seconds
        )
        
        try:
            # Create user response request via WebSocket manager
            self.logger.info(
                "About to create user response request via WebSocket manager",
                execution_id=workflow_execution.id,
                task_id=task.id,
                question=question[:100] + "..." if len(question) > 100 else question
            )
            
            request_id = await websocket_manager.create_user_response_request(
                execution_id=workflow_execution.id,
                task_id=task.id,
                question=question,
                timeout_seconds=timeout_seconds
            )
            
            self.logger.info(
                "WebSocket manager returned request_id",
                request_id=request_id
            )
            
            self.logger.info(
                "User response request created, waiting for response",
                task_id=task.id,
                agent_id=self.agent_node.id,
                request_id=request_id
            )
            
            # Wait for user response with timeout
            user_response = await websocket_manager.wait_for_user_response(
                request_id=request_id,
                timeout_seconds=timeout_seconds
            )
            
            self.logger.info(
                "Received user response",
                task_id=task.id,
                agent_id=self.agent_node.id,
                request_id=request_id,
                user_response=user_response[:100] + "..." if len(user_response) > 100 else user_response
            )
            
            return user_response
            
        except TimeoutError:
            self.logger.warning(
                "User response timeout",
                task_id=task.id,
                agent_id=self.agent_node.id,
                timeout=timeout_seconds
            )
            
            # Send timeout notification to user
            await websocket_manager.send_chat_message(
                execution_id=workflow_execution.id,
                message_content=f"⏰ **Response Timeout**\n\nNo response received within {timeout_seconds} seconds. Proceeding with default behavior.",
                agent_id=self.agent_node.id,
                agent_name=self.agent_node.name,
                task_id=task.id,
                task_name=task.name,
                message_type='timeout_notification',
                requires_response=False
            )
            
            # Return a default response indicating timeout
            return f"[TIMEOUT] No user response received within {timeout_seconds} seconds. Proceeding with default behavior."
            
        except Exception as e:
            self.logger.error(
                "Error waiting for user response",
                task_id=task.id,
                agent_id=self.agent_node.id,
                error=str(e)
            )
            
            # Return an error response
            return f"[ERROR] Failed to get user response: {str(e)}"
    
    async def _parse_and_execute_reasoning(self, reasoning_text: str, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse reasoning text and execute any identified actions"""
        
        # Simple parsing logic - in a real implementation this would be more sophisticated
        reasoning_lower = reasoning_text.lower()
        
        # Check for completion indicators
        completion_indicators = ['task completed', 'finished', 'done', 'complete', 'success']
        if any(indicator in reasoning_lower for indicator in completion_indicators):
            return {
                'completed': True,
                'confidence': 0.8,
                'observation': 'Task identified as completed through reasoning',
                'action': 'complete_task'
            }
        
        # Check for tool usage indicators
        for tool_name in self.available_tools.keys():
            if tool_name.lower() in reasoning_lower:
                tool_result = await self.available_tools[tool_name]()
                return {
                    'completed': False,
                    'confidence': 0.7,
                    'observation': f'Executed tool {tool_name}: {tool_result.get("observation", "Tool executed")}',
                    'action': f'execute_{tool_name}'
                }
        
        # Default - continue reasoning
        return {
            'completed': False,
            'confidence': 0.5,
            'observation': 'Continuing with reasoning process',
            'action': 'continue_reasoning'
        }
    
    async def _fallback_execution(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback execution when LLM is not available"""
        return {
            'success': True,
            'fallback': True,
            'message': f'Task {task.name} executed using fallback logic',
            'confidence': 0.6,
            'strategy': 'fallback'
        }
    
    async def _plan_with_cot(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use CoT for planning phase of hybrid strategy"""
        if not self.llm_client:
            return {
                'success': False,
                'error': 'LLM client not available for planning'
            }
        
        # Implementation would use LLM to create execution plan
        return {
            'success': True,
            'plan': ['Step 1: Analyze task', 'Step 2: Execute action', 'Step 3: Validate result'],
            'confidence': 0.8
        }