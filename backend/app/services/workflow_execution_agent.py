from typing import List, Optional, Dict, Any, Callable, Tuple
import json
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import structlog
import uuid

from app.models.agent_organization import (
    AgentNode, AgentOrganization, WorkflowTask, WorkflowExecution,
    HumanInteractionRequest, AgentStrategy, AgentRole, TaskStatus, ExecutionStatus
)
from app.services.template_service import template_service
from openai import OpenAI


logger = structlog.get_logger()


class WorkflowExecutionAgent:
    """AI Agent for executing workflow tasks with multi-agent coordination"""
    
    def __init__(self, 
                 agent_node: AgentNode,
                 organization: AgentOrganization,
                 llm_client: Optional[OpenAI] = None):
        self.agent_node = agent_node
        self.organization = organization
        self.llm_client = llm_client
        self.logger = logger.bind(
            agent_id=agent_node.id,
            agent_name=agent_node.name,
            agent_role=agent_node.role.value
        )
        
        # Agent state
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
        
        task_id = task.id
        self.logger.info(
            "Starting task execution",
            task_id=task_id,
            task_name=task.name,
            objective=task.objective
        )
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS.value
        task.started_at = datetime.utcnow()
        task.assigned_agent_id = self.agent_node.id
        
        try:
            # Choose execution strategy
            if self.agent_node.strategy == AgentStrategy.CHAIN_OF_THOUGHT:
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
                    task.status = TaskStatus.COMPLETED.value
                    task.completed_at = datetime.utcnow()
                    result.update(approval_result.get('feedback', {}))
                else:
                    task.status = TaskStatus.ESCALATED.value
                    result['escalation_reason'] = approval_result.get('reason', 'Human rejected')
            else:
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.utcnow()
            
            # Store results
            task.results = result
            
            self.logger.info(
                "Task execution completed",
                task_id=task_id,
                status=task.status,
                confidence=result.get('confidence', 0.0)
            )
            
            return {
                'task_id': task_id,
                'status': task.status,
                'results': result,
                'agent_id': self.agent_node.id,
                'execution_time': (task.completed_at - task.started_at).total_seconds() if task.completed_at else None
            }
            
        except Exception as e:
            self.logger.error("Task execution failed", task_id=task_id, error=str(e))
            task.status = TaskStatus.FAILED.value
            task.results = {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return {
                'task_id': task_id,
                'status': task.status,
                'error': str(e),
                'agent_id': self.agent_node.id
            }
    
    async def _execute_with_chain_of_thought(self,
                                           task: WorkflowTask,
                                           execution_context: Dict[str, Any],
                                           workflow_execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task using Chain of Thought reasoning"""
        
        if not self.llm_client:
            return await self._fallback_execution(task, execution_context)
        
        # Build Chain of Thought prompt
        cot_prompt = self._build_cot_prompt(task, execution_context, workflow_execution)
        
        reasoning_steps = []
        final_result = {}
        
        for step in range(self.agent_node.max_iterations):
            try:
                # Get reasoning step from LLM
                completion = self.llm_client.chat.completions.create(
                    model="gpt-4",
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
        
        if not self.llm_client:
            return await self._fallback_execution(task, execution_context)
        
        react_history = []
        observations = []
        
        for iteration in range(self.agent_node.max_iterations):
            try:
                # ReAct prompt with current state
                react_prompt = self._build_react_prompt(task, execution_context, react_history, observations)
                print(f"ReAct Prompt for iteration {iteration + 1}:\n{react_prompt}\n")
                # Get thought and action from LLM
                completion = self.llm_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": react_prompt},
                        {"role": "user", "content": "Think about what action to take next, then take it."}
                    ],
                    temperature=0.3,
                    max_tokens=600
                )
                
                response = completion.choices[0].message.content
                print(f"ReAct Response for iteration {iteration + 1}:\n{response}\n")
                # Parse thought and action
                thought, action = self._parse_react_response(response)
                
                # Execute action
                action_result = await self._execute_react_action(action, task, execution_context)
                
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
                    human_response = await self._request_human_interaction(
                        task, action_result, workflow_execution
                    )
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
        
        # Wait for human response (mock implementation - in real system would use WebSocket/polling)
        await asyncio.sleep(1)  # Simulate waiting for human response
        
        # Mock human approval for testing
        return {
            'status': 'approved',
            'feedback': {
                'human_comments': 'Task completed satisfactorily',
                'approval_timestamp': datetime.utcnow().isoformat()
            }
        }
    
    async def _request_human_interaction(self,
                                       task: WorkflowTask,
                                       context: Dict[str, Any],
                                       workflow_execution: WorkflowExecution) -> str:
        """Request human interaction during task execution"""
        
        interaction_request = HumanInteractionRequest(
            execution_id=workflow_execution.id,
            task_id=task.id,
            agent_id=self.agent_node.id,
            interaction_type="clarification",
            message=context.get('message', 'Agent needs human input'),
            context=context,
            options=context.get('options', []),
            response_deadline=datetime.utcnow() + timedelta(seconds=300)
        )
        
        # Mock human response for testing
        await asyncio.sleep(0.5)
        return "Proceed with the planned action"
    
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
    async def _generic_tool_execution(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Generic tool execution wrapper"""
        return {
            'success': True,
            'tool_name': tool_name,
            'parameters': kwargs,
            'observation': f"Tool {tool_name} executed with parameters: {kwargs}"
        }
    
    # Helper methods for building prompts and parsing responses
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
    
    async def _execute_react_action(self, action: str, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a ReAct action"""
        if action.startswith("complete_task"):
            return {
                'completed': True,
                'observation': 'Task marked as completed',
                'confidence': 0.9
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