from typing import List, Optional, Dict, Any, Set
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import structlog
import uuid

from app.models.agent_organization import (
    AgentOrganization, WorkflowExecution, WorkflowTask, HumanInteractionRequest,
    WorkflowExecutionCreate, ExecutionStatus, TaskStatus
)
from app.services.workflow_execution_agent import WorkflowExecutionAgent
from app.services.template_service import template_service
from openai import OpenAI


logger = structlog.get_logger()


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflow execution with human-in-the-loop"""
    
    def __init__(self, llm_client: Optional[OpenAI] = None):
        self.llm_client = llm_client
        self.logger = logger.bind(service="WorkflowOrchestrator")
        
        # Active executions
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.agent_instances: Dict[str, WorkflowExecutionAgent] = {}
        self.pending_human_interactions: Dict[str, HumanInteractionRequest] = {}
        
        # Coordination state
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        self.agent_load: Dict[str, int] = {}  # agent_id -> current task count
        
    async def initiate_workflow_execution(self,
                                        workflow_template_id: str,
                                        organization_id: str,
                                        initiated_by: str,
                                        initial_context: Dict[str, Any] = None) -> WorkflowExecution:
        """Initiate a new workflow execution"""
        
        self.logger.info(
            "Initiating workflow execution",
            workflow_template_id=workflow_template_id,
            organization_id=organization_id,
            initiated_by=initiated_by
        )
        
        try:
            # Get workflow template from database
            workflow_template = await template_service.get_template(workflow_template_id)
            if not workflow_template:
                raise ValueError(f"Workflow template {workflow_template_id} not found")
            print ("---> After get_template")
            # Get agent organization (mock for now - would come from database)
            organization = await self._get_agent_organization(organization_id)
            if not organization:
                raise ValueError(f"Agent organization {organization_id} not found")
            print ("---> After get_agent_organization")
            # Create workflow tasks from template
            tasks = self._create_tasks_from_template(workflow_template)
            print
            # Create workflow execution
            execution = WorkflowExecution(
                workflow_template_id=workflow_template_id,
                organization_id=organization_id,
                tasks=tasks,
                execution_context=initial_context or {},
                initiated_by=initiated_by,
                status=ExecutionStatus.PENDING.value
            )
            print ("---> After create_workflow_execution")
            # Store execution
            self.active_executions[execution.id] = execution
            print ("---> After store_workflow_execution")
            # Initialize agent instances
            await self._initialize_agent_instances(organization, execution)
            print ("---> After initialize_agent_instances")
            # Start execution
            execution_task = asyncio.create_task(self._execute_workflow(execution))
            print ("---> After start_execution_task")
            self.logger.info(
                "Workflow execution initiated",
                execution_id=execution.id,
                task_count=len(tasks),
                organization_agents=len(organization.agents)
            )
            
            return execution
            
        except Exception as e:
            self.logger.error("Failed to initiate workflow execution", error=str(e))
            raise
    
    async def _execute_workflow(self, execution: WorkflowExecution) -> None:
        """Execute the workflow with multi-agent coordination"""
        
        execution.status = ExecutionStatus.RUNNING.value
        
        try:
            while not self._is_workflow_complete(execution):
                # Get ready tasks (dependencies satisfied)
                ready_tasks = self._get_ready_tasks(execution)
                
                if not ready_tasks:
                    # Check if waiting for human interaction
                    if execution.human_approvals_pending:
                        self.logger.info(
                            "Workflow paused - waiting for human approval",
                            execution_id=execution.id,
                            pending_approvals=len(execution.human_approvals_pending)
                        )
                        execution.status = ExecutionStatus.PAUSED.value
                        await asyncio.sleep(5)  # Wait before checking again
                        continue
                    else:
                        # No ready tasks and no pending approvals - potential deadlock
                        self.logger.warning(
                            "No ready tasks available - potential deadlock",
                            execution_id=execution.id
                        )
                        break
                
                # Assign and execute ready tasks
                task_assignments = await self._assign_tasks_to_agents(ready_tasks, execution)
                
                # Execute tasks in parallel
                execution_coroutines = []
                for task_id, agent_id in task_assignments.items():
                    task = next(t for t in execution.tasks if t.id == task_id)
                    agent = self.agent_instances[agent_id]
                    
                    coroutine = self._execute_task_with_monitoring(
                        agent, task, execution.execution_context, execution
                    )
                    execution_coroutines.append(coroutine)
                
                # Wait for all assigned tasks to complete
                if execution_coroutines:
                    task_results = await asyncio.gather(*execution_coroutines, return_exceptions=True)
                    
                    # Process results
                    for i, result in enumerate(task_results):
                        if isinstance(result, Exception):
                            self.logger.error(
                                "Task execution exception",
                                execution_id=execution.id,
                                error=str(result)
                            )
                        else:
                            self._process_task_result(result, execution)
                
                # Brief pause before next iteration
                await asyncio.sleep(1)
            
            # Determine final status
            if self._all_tasks_completed(execution):
                execution.status = ExecutionStatus.COMPLETED.value
                execution.actual_completion = datetime.utcnow()
                self.logger.info(
                    "Workflow execution completed successfully",
                    execution_id=execution.id,
                    duration=(execution.actual_completion - execution.started_at).total_seconds()
                )
            else:
                execution.status = ExecutionStatus.FAILED.value
                self.logger.error(
                    "Workflow execution failed",
                    execution_id=execution.id
                )
                
        except Exception as e:
            execution.status = ExecutionStatus.FAILED.value
            execution.error_log.append({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'phase': 'execution'
            })
            self.logger.error("Workflow execution failed with exception", error=str(e))
    
    async def _execute_task_with_monitoring(self,
                                          agent: WorkflowExecutionAgent,
                                          task: WorkflowTask,
                                          context: Dict[str, Any],
                                          execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task with monitoring and error handling"""
        
        try:
            # Update execution tracking
            execution.current_tasks.append(task.id)
            
            # Execute task
            result = await agent.execute_task(task, context, execution)
            
            # Handle handoffs
            if result.get('requires_handoff'):
                handoff_result = await self._handle_task_handoff(
                    task, result, agent, execution
                )
                result.update(handoff_result)
            
            # Update execution tracking
            if task.id in execution.current_tasks:
                execution.current_tasks.remove(task.id)
            
            if result.get('status') == TaskStatus.COMPLETED.value:
                execution.completed_tasks.append(task.id)
            elif result.get('status') == TaskStatus.FAILED.value:
                execution.failed_tasks.append(task.id)
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Task monitoring failed",
                task_id=task.id,
                agent_id=agent.agent_node.id,
                error=str(e)
            )
            
            # Clean up tracking
            if task.id in execution.current_tasks:
                execution.current_tasks.remove(task.id)
            execution.failed_tasks.append(task.id)
            
            return {
                'task_id': task.id,
                'status': TaskStatus.FAILED.value,
                'error': str(e),
                'agent_id': agent.agent_node.id
            }
    
    async def _handle_task_handoff(self,
                                 task: WorkflowTask,
                                 task_result: Dict[str, Any],
                                 current_agent: WorkflowExecutionAgent,
                                 execution: WorkflowExecution) -> Dict[str, Any]:
        """Handle task handoff between agents"""
        
        target_agent_id = task_result.get('target_agent')
        if not target_agent_id or target_agent_id not in self.agent_instances:
            return {
                'handoff_success': False,
                'error': f'Target agent {target_agent_id} not available'
            }
        
        target_agent = self.agent_instances[target_agent_id]
        
        # Perform handoff
        handoff_result = await current_agent.handoff_to_agent(
            target_agent_id, task, task_result, execution
        )
        
        if handoff_result.get('success'):
            # Update task assignment
            task.assigned_agent_id = target_agent_id
            self.task_assignments[task.id] = target_agent_id
            
            # Re-execute with new agent
            new_result = await target_agent.execute_task(task, execution.execution_context, execution)
            
            return {
                'handoff_success': True,
                'handoff_record': handoff_result,
                'new_execution_result': new_result
            }
        else:
            return {
                'handoff_success': False,
                'error': handoff_result.get('error', 'Handoff failed')
            }
    
    async def _assign_tasks_to_agents(self,
                                    ready_tasks: List[WorkflowTask],
                                    execution: WorkflowExecution) -> Dict[str, str]:
        """Assign ready tasks to appropriate agents"""
        
        assignments = {}
        organization = await self._get_agent_organization(execution.organization_id)
        
        for task in ready_tasks:
            # Find best agent for this task
            best_agent_id = await self._find_best_agent_for_task(task, organization, execution)
            
            if best_agent_id:
                assignments[task.id] = best_agent_id
                self.task_assignments[task.id] = best_agent_id
                
                # Update agent load tracking
                self.agent_load[best_agent_id] = self.agent_load.get(best_agent_id, 0) + 1
                
                self.logger.info(
                    "Task assigned to agent",
                    task_id=task.id,
                    task_name=task.name,
                    agent_id=best_agent_id
                )
            else:
                self.logger.warning(
                    "No suitable agent found for task",
                    task_id=task.id,
                    task_name=task.name
                )
        
        return assignments
    
    async def _find_best_agent_for_task(self,
                                      task: WorkflowTask,
                                      organization: AgentOrganization,
                                      execution: WorkflowExecution) -> Optional[str]:
        """Find the best agent to handle a specific task"""
        
        candidate_agents = []
        
        for agent_node in organization.agents:
            # Check agent availability
            current_load = self.agent_load.get(agent_node.id, 0)
            if current_load >= agent_node.max_concurrent_tasks:
                continue
            
            # Check agent capabilities
            capability_score = self._calculate_capability_score(task, agent_node)
            
            # Check task-specific requirements (mock logic)
            if task.name.lower().startswith('validate') and agent_node.role.value != 'validator':
                capability_score *= 0.5
            
            if capability_score > 0:
                candidate_agents.append({
                    'agent_id': agent_node.id,
                    'score': capability_score,
                    'load': current_load
                })
        
        if not candidate_agents:
            return None
        
        # Sort by score (desc) and load (asc)
        candidate_agents.sort(key=lambda x: (-x['score'], x['load']))
        
        return candidate_agents[0]['agent_id']
    
    def _calculate_capability_score(self, task: WorkflowTask, agent_node) -> float:
        """Calculate how well an agent's capabilities match a task"""
        
        # Basic capability matching logic
        score = 0.5  # Base score
        
        # Check if agent has relevant capabilities
        task_keywords = (task.name + " " + task.description).lower().split()
        
        for capability in agent_node.capabilities:
            capability_keywords = (capability.name + " " + capability.description).lower().split()
            
            # Simple keyword matching
            matches = len(set(task_keywords) & set(capability_keywords))
            if matches > 0:
                score += capability.confidence_level * 0.3
        
        # Role-based scoring
        if task.name.lower().startswith('coordinate') and agent_node.role.value == 'coordinator':
            score += 0.4
        elif task.name.lower().startswith('validate') and agent_node.role.value == 'validator':
            score += 0.4
        elif agent_node.role.value == 'specialist':
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_ready_tasks(self, execution: WorkflowExecution) -> List[WorkflowTask]:
        """Get tasks that are ready to execute (dependencies satisfied)"""
        
        ready_tasks = []
        completed_task_ids = set(execution.completed_tasks)
        current_task_ids = set(execution.current_tasks)
        failed_task_ids = set(execution.failed_tasks)
        
        for task in execution.tasks:
            # Skip if already processed or currently running
            if (task.id in completed_task_ids or 
                task.id in current_task_ids or 
                task.id in failed_task_ids):
                continue
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = all(
                dep_id in completed_task_ids for dep_id in task.dependencies
            )
            
            if dependencies_satisfied:
                ready_tasks.append(task)
        
        return ready_tasks
    
    def _is_workflow_complete(self, execution: WorkflowExecution) -> bool:
        """Check if workflow execution is complete"""
        
        total_tasks = len(execution.tasks)
        processed_tasks = len(execution.completed_tasks) + len(execution.failed_tasks)
        
        return processed_tasks >= total_tasks
    
    def _all_tasks_completed(self, execution: WorkflowExecution) -> bool:
        """Check if all tasks completed successfully"""
        
        return len(execution.completed_tasks) == len(execution.tasks)
    
    def _process_task_result(self, result: Dict[str, Any], execution: WorkflowExecution) -> None:
        """Process task execution result"""
        
        # Update agent load tracking
        agent_id = result.get('agent_id')
        if agent_id and agent_id in self.agent_load:
            self.agent_load[agent_id] = max(0, self.agent_load[agent_id] - 1)
        
        # Log result
        execution.agent_actions.append({
            'action_type': 'task_completion',
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Handle human approval requirements
        if result.get('status') == TaskStatus.WAITING_APPROVAL.value:
            task_id = result.get('task_id')
            if task_id:
                execution.human_approvals_pending.append(task_id)
    
    async def _initialize_agent_instances(self, 
                                        organization: AgentOrganization,
                                        execution: WorkflowExecution) -> None:
        """Initialize agent instances for the organization"""
        print (f"---> Initializing agent instances for organization {organization}")
        for agent_node in organization.agents:
            print (f"---> Initializing agent instance for {agent_node.name} ({agent_node.id})")
            # Create agent instance 
            agent_instance = WorkflowExecutionAgent(
                agent_node=agent_node,
                organization=organization,
                llm_client=self.llm_client
            )
            
            self.agent_instances[agent_node.id] = agent_instance
            self.agent_load[agent_node.id] = 0
        
        self.logger.info(
            "Agent instances initialized",
            execution_id=execution.id,
            agent_count=len(organization.agents)
        )
    
    def _create_tasks_from_template(self, workflow_template) -> List[WorkflowTask]:
        """Create workflow tasks from template"""
        
        tasks = []
        template_data = workflow_template.template_data
        
        if isinstance(template_data, dict) and 'nodes' in template_data:
            for node in template_data['nodes']:
                task = WorkflowTask(
                    id=node.get('id', str(uuid.uuid4())),
                    name=node.get('data', {}).get('label', 'Unnamed Task'),
                    description=node.get('data', {}).get('description', ''),
                    objective=node.get('data', {}).get('objective', ''),
                    completion_criteria=node.get('data', {}).get('completionCriteria', ''),
                    context=node.get('data', {})
                )
                tasks.append(task)
            
            # Add dependencies based on edges
            if 'edges' in template_data:
                for edge in template_data['edges']:
                    target_id = edge.get('target')
                    source_id = edge.get('source')
                    
                    # Find target task and add dependency
                    for task in tasks:
                        if task.id == target_id and source_id:
                            task.dependencies.append(source_id)
        
        return tasks
    
    async def _get_agent_organization(self, organization_id: str) -> Optional[AgentOrganization]:
        """Get agent organization by ID (mock implementation)"""
        
        # Mock agent organization for testing
        from app.models.agent_organization import AgentNode, AgentRole, AgentStrategy, AgentCapability, AgentTool
        
        return AgentOrganization(
            id=organization_id,
            name="Default Workflow Organization",
            description="Default multi-agent organization for workflow execution",
            agents=[
                AgentNode(
                    id="coordinator-001",
                    name="Workflow Coordinator",
                    role=AgentRole.COORDINATOR,
                    strategy=AgentStrategy.HYBRID,
                    capabilities=[
                        AgentCapability(
                            name="Task Coordination",
                            description="Coordinate multiple tasks and agents",
                            confidence_level=0.9
                        )
                    ],
                    tools=[
                        AgentTool(
                            name="agent_handoff",
                            description="Hand off tasks to other agents",
                            tool_type="coordination"
                        )
                    ],
                    can_handoff_to=["specialist-001", "validator-001"],
                    max_concurrent_tasks=5
                ),
                AgentNode(
                    id="specialist-001",
                    name="Task Specialist",
                    role=AgentRole.SPECIALIST,
                    strategy=AgentStrategy.REACT,
                    capabilities=[
                        AgentCapability(
                            name="Task Execution",
                            description="Execute specialized tasks",
                            confidence_level=0.8
                        )
                    ],
                    tools=[
                        AgentTool(
                            name="database_query",
                            description="Query databases",
                            tool_type="database"
                        ),
                        AgentTool(
                            name="api_request",
                            description="Make API requests",
                            tool_type="api"
                        )
                    ],
                    requires_human_approval=True,
                    can_handoff_to=["validator-001"],
                    max_concurrent_tasks=3
                ),
                AgentNode(
                    id="validator-001",
                    name="Task Validator",
                    role=AgentRole.VALIDATOR,
                    strategy=AgentStrategy.CHAIN_OF_THOUGHT,
                    capabilities=[
                        AgentCapability(
                            name="Task Validation",
                            description="Validate task completion",
                            confidence_level=0.9
                        )
                    ],
                    tools=[
                        AgentTool(
                            name="task_validation",
                            description="Validate task results",
                            tool_type="validation"
                        )
                    ],
                    max_concurrent_tasks=2
                )
            ],
            entry_points=["coordinator-001"],
            max_execution_time_minutes=120,
            require_human_supervision=True,
            allow_parallel_execution=True
        )
    
    # Public methods for external interaction
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of workflow execution"""
        
        execution = self.active_executions.get(execution_id)
        if not execution:
            return None
        
        return {
            'execution_id': execution_id,
            'status': execution.status,
            'progress': {
                'total_tasks': len(execution.tasks),
                'completed_tasks': len(execution.completed_tasks),
                'failed_tasks': len(execution.failed_tasks),
                'current_tasks': len(execution.current_tasks)
            },
            'started_at': execution.started_at.isoformat(),
            'estimated_completion': execution.estimated_completion.isoformat() if execution.estimated_completion else None,
            'human_approvals_pending': len(execution.human_approvals_pending),
            'agent_actions_count': len(execution.agent_actions)
        }
    
    async def respond_to_human_interaction(self,
                                         interaction_id: str,
                                         response: str,
                                         choice: Optional[str] = None) -> bool:
        """Respond to human interaction request"""
        
        if interaction_id not in self.pending_human_interactions:
            return False
        
        interaction = self.pending_human_interactions[interaction_id]
        interaction.human_response = response
        interaction.human_choice = choice
        interaction.responded_at = datetime.utcnow()
        interaction.status = "responded"
        
        # Remove from pending
        del self.pending_human_interactions[interaction_id]
        
        # Update execution
        execution = self.active_executions.get(interaction.execution_id)
        if execution and interaction.task_id in execution.human_approvals_pending:
            execution.human_approvals_pending.remove(interaction.task_id)
            execution.human_feedback.append({
                'interaction_id': interaction_id,
                'task_id': interaction.task_id,
                'response': response,
                'choice': choice,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return True
    
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause workflow execution"""
        
        execution = self.active_executions.get(execution_id)
        if execution:
            execution.status = ExecutionStatus.PAUSED.value
            return True
        return False
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume paused workflow execution"""
        
        execution = self.active_executions.get(execution_id)
        if execution and execution.status == ExecutionStatus.PAUSED.value:
            execution.status = ExecutionStatus.RUNNING.value
            # Restart execution task
            asyncio.create_task(self._execute_workflow(execution))
            return True
        return False
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel workflow execution"""
        
        execution = self.active_executions.get(execution_id)
        if execution:
            execution.status = ExecutionStatus.CANCELLED.value
            execution.actual_completion = datetime.utcnow()
            return True
        return False