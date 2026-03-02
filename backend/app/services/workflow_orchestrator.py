from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import structlog
import uuid

from app.models.agent_organization import (
    AgentOrganization, WorkflowExecution, WorkflowTask, HumanInteractionRequest,
    ExecutionStatus, TaskStatus
)
from app.services.workflow_execution_agent import WorkflowExecutionAgent
from app.services.template_service import template_service
from app.services.workflow_execution_service import workflow_execution_service
from app.services.websocket_manager import websocket_manager
from openai import OpenAI

# Note: Graphiti memory enhancement is now handled at the agent level in WorkflowExecutionAgent
# Each agent can have use_memory_enhancement=True/False to enable/disable memory for their tasks

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
            # Get agent organization (mock for now - would come from database)
            organization = await self._get_agent_organization(organization_id)
            if not organization:
                raise ValueError(f"Agent organization {organization_id} not found")
            # Create workflow execution using the database service
            # IMPORTANT: Use organization.id (the actual organization ID) not organization_id (which might be a template ID)
            execution = await workflow_execution_service.create_execution(
                workflow_template_id=workflow_template_id,
                initiated_by=initiated_by,
                organization_id=organization.id,  # Use the actual organization ID from the retrieved/created organization
                execution_context=initial_context or {},
                priority=1
            )
            
            # Store execution in memory for orchestration
            self.active_executions[execution.id] = execution
            
            # Register execution with WebSocket manager for real-time updates
            websocket_manager.register_execution(execution.id, initiated_by)
            # Initialize agent instances
            await self._initialize_agent_instances(organization, execution)
            # Start execution
            asyncio.create_task(self._execute_workflow(execution))
            
            return execution
            
        except Exception as e:
            self.logger.error("Failed to initiate workflow execution", error=str(e))
            raise
    
    async def _execute_workflow(self, execution: WorkflowExecution) -> None:
        """Execute the workflow with multi-agent coordination

        Note: Memory enhancement is now handled at the agent level, not workflow level.
        Each agent can have use_memory_enhancement=True to enable Graphiti memory for their tasks.
        This is checked in WorkflowExecutionAgent.execute_task() before task execution.
        """
        self.logger.info(
            "Starting workflow execution",
            execution_id=execution.id,
            workflow_template_id=execution.workflow_template_id
        )
        execution.status = ExecutionStatus.RUNNING
        # Update status in database
        await workflow_execution_service.update_execution_status(execution.id, ExecutionStatus.RUNNING)
        
        # Send real-time execution update
        await websocket_manager.send_execution_update(execution.id, {
            'status': 'running',
            'message': '🚀 Workflow execution started',
            'total_tasks': len(execution.tasks)
        })
        
        try:
            while not self._is_workflow_complete(execution):
                # Get ready tasks (dependencies satisfied)
                ready_tasks = self._get_ready_tasks(execution)
                
                if not ready_tasks:
                    # Check if waiting for human interaction
                    if execution.human_approvals_pending:
                        
                        execution.status = ExecutionStatus.PAUSED
                        # Update status in database
                        await workflow_execution_service.update_execution_status(execution.id, ExecutionStatus.PAUSED)
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

                    # Check if any task returned to PENDING state
                    has_pending_task = False

                    # Process results
                    for i, result in enumerate(task_results):
                        

                        # Check for PENDING status - workflow should pause
                        if isinstance(result, dict) and result.get('status') == TaskStatus.PENDING.value:
                            has_pending_task = True
                            

                        # Check for PAUSED status - workflow should pause immediately
                        if isinstance(result, dict) and result.get('status') == TaskStatus.PAUSED.value:
                            

                            # Update workflow status to PAUSED
                            execution.status = ExecutionStatus.PAUSED
                            await workflow_execution_service.update_execution_status(
                                execution.id,
                                ExecutionStatus.PAUSED
                            )

                            # Send WebSocket notification
                            await websocket_manager.send_execution_update(execution.id, {
                                'status': 'paused',
                                'message': f'⏸️ Workflow paused: {result.get("pause_reason", "Task requested pause")}',
                                'task_id': ready_tasks[i].id,
                                'pause_reason': result.get('pause_reason', 'Task requested pause')
                            })

                            
                            return  # Stop workflow execution

                        # Enhanced JSON canvas update detection and processing
                        results = result.get('results') if isinstance(result, dict) else None
                        response = results.get('response') if results else None

                        if response and isinstance(response, str):
                            # Check for JSON canvas update markers
                            if ("JSON_START" in response and "JSON_END" in response):
                                # Extract JSON content between markers
                                json_content = response.replace("JSON_START", "").replace("JSON_END", "").strip()

                                # Determine canvas type based on JSON content
                                canvas_type = "workflow"  # default
                                if any(keyword in json_content.lower() for keyword in ['"role":', '"skills":', '"department":']):
                                    canvas_type = "agent"


                                # Send specialized canvas update message
                                await websocket_manager.send_execution_update(execution.id, {
                                    'type': 'canvas_update',
                                    'canvas_type': canvas_type,
                                    'json_content': json_content,
                                    'message': f"Canvas update received for {canvas_type} designer",
                                    'task_id': ready_tasks[i].id,
                                    'agent_name': self._get_agent_name(ready_tasks[i].assigned_agent_id) if ready_tasks[i].assigned_agent_id else 'Unassigned'
                                })

                            # Check for other structured data patterns (potential JSON without markers)
                            elif any(pattern in response.lower() for pattern in ['"nodes":', '"edges":', '"workflow":', '"agents":']):
                                # This might be JSON without explicit markers

                                await websocket_manager.send_execution_update(execution.id, {
                                    'type': 'potential_canvas_update',
                                    'content': response,
                                    'message': "Potential canvas data detected - please review",
                                    'task_id': ready_tasks[i].id
                                })
                        
                        if isinstance(result, Exception):
                            self.logger.error(
                                "Task execution exception",
                                execution_id=execution.id,
                                error=str(result)
                            )
                        else:
                            self._process_task_result(result, execution)

                    # If any task is in PENDING state, pause the workflow execution
                    if has_pending_task:
                        execution.status = ExecutionStatus.PAUSED
                        # Update status in database
                        await workflow_execution_service.update_execution_status(execution.id, ExecutionStatus.PAUSED)

                        # Send pause notification
                        await websocket_manager.send_execution_update(execution.id, {
                            'status': 'paused',
                            'message': '⏸️  Workflow paused - task returned to PENDING state',
                            'pending_tasks': [t.id for t in execution.tasks if t.status == TaskStatus.PENDING]
                        })

                        
                        break  # Exit the workflow execution loop

                # Brief pause before next iteration
                await asyncio.sleep(1)
            
            # Determine final status
            if self._all_tasks_completed(execution):
                execution.status = ExecutionStatus.COMPLETED
                execution.actual_completion = datetime.utcnow()
                # Update status in database
                await workflow_execution_service.update_execution_status(execution.id, ExecutionStatus.COMPLETED)

                # Extract final response from the last completed task
                final_response = self._extract_final_response(execution)

                # Send completion update with final response
                completion_message = '✅ Workflow execution completed successfully!'
                if final_response:
                    completion_message += f'\n\n**Final Response:**\n{final_response}'

                await websocket_manager.send_execution_update(execution.id, {
                    'status': 'completed',
                    'message': completion_message,
                    'completed_tasks': len(execution.completed_tasks),
                    'total_tasks': len(execution.tasks),
                    'duration': (execution.actual_completion - execution.started_at).total_seconds(),
                    'final_response': final_response
                })

                # Also send the final response as a chat message for better visibility
                if final_response:
                    self.logger.info(
                        "Sending final workflow response to chat",
                        execution_id=execution.id,
                        response_length=len(final_response)
                    )
                    await websocket_manager.send_chat_message(
                        execution_id=execution.id,
                        message_content=final_response,
                        agent_id='workflow-completion',
                        agent_name='Workflow Result',
                        message_type='workflow_response',
                        metadata={
                            'workflow_id': execution.workflow_template_id,
                            'execution_id': execution.id,
                            'completed_tasks': len(execution.completed_tasks),
                            'total_tasks': len(execution.tasks)
                        }
                    )
                else:
                    self.logger.warning(
                        "No final response extracted from workflow",
                        execution_id=execution.id,
                        agent_actions_count=len(execution.agent_actions)
                    )

            else:
                execution.status = ExecutionStatus.FAILED
                # Update status in database
                await workflow_execution_service.update_execution_status(execution.id, ExecutionStatus.FAILED, "Workflow execution incomplete")
                
                # Send failure update
                await websocket_manager.send_execution_update(execution.id, {
                    'status': 'failed',
                    'message': '❌ Workflow execution failed - some tasks could not be completed',
                    'completed_tasks': len(execution.completed_tasks),
                    'failed_tasks': len(execution.failed_tasks),
                    'total_tasks': len(execution.tasks)
                })
                
                self.logger.error(
                    "Workflow execution failed",
                    execution_id=execution.id
                )
                
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_log.append({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'phase': 'execution'
            })
            # Update status in database
            await workflow_execution_service.update_execution_status(execution.id, ExecutionStatus.FAILED, str(e))
            self.logger.error("Workflow execution failed with exception", error=str(e))
    
    async def _execute_task_with_monitoring(self,
                                          agent: WorkflowExecutionAgent,
                                          task: WorkflowTask,
                                          context: Dict[str, Any],
                                          execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute task with monitoring and error handling

        Note: Memory enhancement (Graphiti) is handled at the agent level.
        If agent.agent_node.use_memory_enhancement is True, the agent will automatically
        search and enhance context with Graphiti memory before task execution.
        This is done in WorkflowExecutionAgent.execute_task().
        """

        try:
            # Update task status to IN_PROGRESS using helper method
            execution.update_task_status(task.id, TaskStatus.IN_PROGRESS)

            # Update task status in database
            await workflow_execution_service.update_task_status(
                task.id, TaskStatus.IN_PROGRESS, agent.agent_node.id
            )

            # Execute task
            result = await agent.execute_task(task, context, execution)

            # Handle handoffs
            if result.get('requires_handoff'):
                handoff_result = await self._handle_task_handoff(
                    task, result, agent, execution
                )
                result.update(handoff_result)

            # Determine final status based on result
            result_status_str = result.get('status', 'completed')

            # Map string status to TaskStatus enum
            if result_status_str == TaskStatus.PAUSED.value or result_status_str == 'PAUSED':
                final_status = TaskStatus.PAUSED
            elif result_status_str == TaskStatus.FAILED.value or result_status_str == 'failed':
                final_status = TaskStatus.FAILED
            elif result_status_str == TaskStatus.PENDING.value or result_status_str == 'pending':
                final_status = TaskStatus.PENDING
            else:
                final_status = TaskStatus.COMPLETED

            # Update task status using helper method
            execution.update_task_status(task.id, final_status)

            # Update task status in database
            await workflow_execution_service.update_task_status(
                task.id, final_status, agent.agent_node.id, result
            )

            if final_status == TaskStatus.PAUSED:
                self.logger.info(
                    "Task paused - workflow will pause",
                    task_id=task.id,
                    execution_id=execution.id,
                    pause_reason=result.get('pause_reason', 'Unknown')
                )
            elif final_status == TaskStatus.PENDING:
                self.logger.info(
                    "Task returned to PENDING state - workflow will pause",
                    task_id=task.id,
                    execution_id=execution.id
                )

            return result

        except Exception as e:
            self.logger.error(
                "Task monitoring failed",
                task_id=task.id,
                agent_id=agent.agent_node.id,
                error=str(e)
            )

            # Update task status to FAILED using helper method
            execution.update_task_status(task.id, TaskStatus.FAILED)

            # Update task status in database
            await workflow_execution_service.update_task_status(
                task.id, TaskStatus.FAILED, agent.agent_node.id, {
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
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
            
            # Update task assignment in database
            await workflow_execution_service.update_task_assignment(task.id, target_agent_id)
            
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
                
                # Update task assignment in database
                await workflow_execution_service.update_task_assignment(task.id, best_agent_id)
                
                # Update agent load tracking
                self.agent_load[best_agent_id] = self.agent_load.get(best_agent_id, 0) + 1
                
               
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
        # Use the WorkflowExecution helper method which checks task status directly
        return execution.get_ready_tasks()
    
    def _is_workflow_complete(self, execution: WorkflowExecution) -> bool:
        """Check if workflow execution is complete"""
        # A workflow is complete when all tasks are either completed or failed
        total_tasks = len(execution.tasks)
        completed = len([t for t in execution.tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in execution.tasks if t.status == TaskStatus.FAILED])

        return (completed + failed) >= total_tasks
    
    def _all_tasks_completed(self, execution: WorkflowExecution) -> bool:
        """Check if all tasks completed successfully"""
        total_tasks = len(execution.tasks)
        completed = len([t for t in execution.tasks if t.status == TaskStatus.COMPLETED])
        return completed == total_tasks

    def _extract_final_response(self, execution: WorkflowExecution) -> Optional[str]:
        """Extract the final response from the workflow execution

        Looks through agent_actions to find the last task completion result
        and extracts the response/summary from it.
        """
        try:
            # Look through agent_actions in reverse order to find the last task result
            for action in reversed(execution.agent_actions):
                if action.get('action_type') == 'task_completion':
                    result = action.get('result', {})
                    self.logger.info(
                        "Processing task completion result",
                        execution_id=execution.id,
                        result=result
                    )

                    # Try to extract response from various possible locations
                    if isinstance(result, dict):
                        # Check for 'results' > 'response' structure
                        results = result.get('results', {})
                        if isinstance(results, dict):
                            response = results.get('response')
                            if response and isinstance(response, str):
                                # Clean up the response - remove JSON/YAML canvas markers if present
                                if 'JSON_START' in response or 'YaMl_StArT' in response:
                                    continue  # Skip canvas updates
                                return response[:2000]  # Limit length

                            # Check for execution_summary
                            summary = results.get('execution_summary')
                            if summary and isinstance(summary, str):
                                return summary[:2000]

                        # Check for direct response
                        direct_response = result.get('response')
                        if direct_response and isinstance(direct_response, str):
                            return direct_response[:2000]

                        # Check for execution_summary at top level
                        exec_summary = result.get('execution_summary')
                        if exec_summary and isinstance(exec_summary, str):
                            return exec_summary[:2000]

            # If no response found in agent_actions, check task results directly
            for task in reversed(execution.tasks):
                if task.status == TaskStatus.COMPLETED and task.results:
                    results = task.results
                    if isinstance(results, dict):
                        response = results.get('response') or results.get('execution_summary')
                        if response and isinstance(response, str):
                            if 'JSON_START' not in response and 'YaMl_StArT' not in response:
                                return response[:2000]

            return None
        except Exception as e:
            self.logger.warning("Failed to extract final response", error=str(e))
            return None
    
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
        
        # Send real-time task result to monitoring console via WebSocket
        agent_id = result.get('agent_id')
        agent_name = 'Unknown Agent'
        if agent_id and agent_id in self.agent_instances:
            agent_instance = self.agent_instances[agent_id]
            agent_name = agent_instance.agent_node.name
        
        workflow_name = f"Workflow-{execution.workflow_template_id[:8]}..."
        
        asyncio.create_task(websocket_manager.send_task_result_as_agent_thought(
            execution.id, 
            result, 
            agent_name, 
            workflow_name
        ))
        
        # Handle human approval requirements
        if result.get('status') == TaskStatus.WAITING_APPROVAL.value:
            task_id = result.get('task_id')
            if task_id:
                execution.human_approvals_pending.append(task_id)
    
    async def _initialize_agent_instances(self, 
                                        organization: AgentOrganization,
                                        execution: WorkflowExecution) -> None:
        """Initialize agent instances for the organization"""
        for agent_node in organization.agents:
            # Create agent instance 
            agent_instance = WorkflowExecutionAgent(
                agent_node=agent_node,
                organization=organization,
                llm_client=self.llm_client
            )
            
            self.agent_instances[agent_node.id] = agent_instance
            self.agent_load[agent_node.id] = 0
        
        
    
    def _create_tasks_from_template(self, workflow_template) -> List[WorkflowTask]:
        """Create workflow tasks from template"""

        tasks = []
        template_data = workflow_template.template_data

        # Debug: Log the entire template_data structure
        

        # Debug: Log first node structure if available
        if isinstance(template_data, dict) and 'nodes' in template_data and len(template_data['nodes']) > 0:
            first_node = template_data['nodes'][0]
            

        # Map original node IDs to new unique task IDs for dependency resolution
        node_id_mapping = {}

        if isinstance(template_data, dict) and 'nodes' in template_data:
            for node in template_data['nodes']:
                original_node_id = node.get('id', str(uuid.uuid4()))
                unique_task_id = str(uuid.uuid4())  # Always generate unique ID

                # Store mapping for dependency resolution
                node_id_mapping[original_node_id] = unique_task_id

                # Extract node data and type
                node_data = node.get('data', {})
                node_type = node_data.get('type', 'action')

                # Debug logging to verify node type extraction
                

                task = WorkflowTask(
                    id=unique_task_id,
                    name=node_data.get('label', 'Unnamed Task'),
                    description=node_data.get('description', ''),
                    objective=node_data.get('objective', ''),
                    completion_criteria=node_data.get('completionCriteria', ''),
                    status=TaskStatus.PENDING,
                    context={
                        **node_data,
                        'original_node_id': original_node_id,  # Store original ID for reference
                        'task_type': node_type  # Pass node type as task_type
                    }
                )
                tasks.append(task)
            
            # Add dependencies based on edges using mapped IDs
            if 'edges' in template_data:
                for edge in template_data['edges']:
                    source_id = edge.get('source')
                    target_id = edge.get('target')
                    
                    if source_id in node_id_mapping and target_id in node_id_mapping:
                        # Find the target task and add the source task as a dependency
                        target_task_id = node_id_mapping[target_id]
                        source_task_id = node_id_mapping[source_id]
                        
                        for task in tasks:
                            if task.id == target_task_id:
                                task.dependencies.append(source_task_id)
                                break
        
        return tasks
    
    async def _get_agent_organization(self, organization_id: str) -> Optional[AgentOrganization]:
        """Get agent organization by ID from database, with template integration"""
        
        try:
            from app.services.agent_organization_service import agent_organization_service
            # First, try to get existing organization from database
            organization = await agent_organization_service.get_agent_organization(organization_id)
            
            if organization:
                
                return organization
            
            # If not found, try to treat organization_id as a template_id and create from template
            
            organization = await agent_organization_service.create_organization_from_template(
                agent_template_id=organization_id,
                organization_name=f"Generated Organization {organization_id[:8]}",
                created_by="system"
            )
            
            if organization:
                
                return organization
            
            # If template creation also fails, fall back to mock organization
            self.logger.warning(
                "Failed to create from template, falling back to mock organization",
                template_id=organization_id
            )
            return await self._create_fallback_organization(organization_id)
            
        except Exception as e:
            self.logger.error(
                "Failed to get or create agent organization, falling back to mock",
                organization_id=organization_id,
                error=str(e)
            )
            # Fallback to mock organization on any error
            return await self._create_fallback_organization(organization_id)
    
    async def _create_fallback_organization(self, organization_id: str) -> AgentOrganization:
        """Create fallback mock organization when database is unavailable"""
        
        from app.models.agent_organization import AgentNode, AgentRole, AgentStrategy, AgentCapability, AgentTool
        
        
        return AgentOrganization(
            id=organization_id,
            name="Fallback Workflow Organization",
            description="Fallback multi-agent organization for workflow execution",
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
    
    async def load_execution_from_database(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Load workflow execution from database into memory for orchestration"""
        try:
            # Get execution from database
            execution = await workflow_execution_service.get_execution(execution_id)
            if execution:
                # Store in memory for orchestration
                self.active_executions[execution_id] = execution
               
                return execution
            return None
        except Exception as e:
            self.logger.error("Failed to load execution from database", 
                            execution_id=execution_id, error=str(e))
            return None
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of workflow execution"""
        
        execution = self.active_executions.get(execution_id)
        if not execution:
            # Try to load from database
            execution = await self.load_execution_from_database(execution_id)
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
            execution.status = ExecutionStatus.PAUSED
            # Update status in database
            await workflow_execution_service.update_execution_status(execution_id, ExecutionStatus.PAUSED)
            return True
        return False
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume paused workflow execution"""

        # First check if execution is already in memory
        execution = self.active_executions.get(execution_id)

        # If not in memory, load from database
        if not execution:
            
            execution = await workflow_execution_service.get_execution(execution_id)

            if not execution:
                self.logger.error("Execution not found in database",
                                execution_id=execution_id)
                return False

    
        # Check if execution is paused
        if execution.status != ExecutionStatus.PAUSED:
            self.logger.warning("Cannot resume execution - not in PAUSED state",
                              execution_id=execution_id,
                              current_status=execution.status.value)
            return False

        # Update status to RUNNING
        execution.status = ExecutionStatus.RUNNING

        # Synchronize task lists with actual task statuses
        execution.sync_task_lists()

        # Add to active executions if not already there
        self.active_executions[execution_id] = execution

        # Update status in database
        await workflow_execution_service.update_execution_status(
            execution_id,
            ExecutionStatus.RUNNING
        )


        # Restart execution task
        asyncio.create_task(self._execute_workflow(execution))

        return True
    
    def _get_agent_name(self, agent_id: str) -> str:
        """Get agent name from agent ID, with fallback to ID if not found"""
        if not agent_id:
            return 'Unassigned'
            
        # Try to get from active agent instances first
        agent_instance = self.agent_instances.get(agent_id)
        if agent_instance and hasattr(agent_instance, 'agent_name'):
            return agent_instance.agent_name
            
        # Try to get from current execution's organization
        for execution in self.active_executions.values():
            if hasattr(execution, '_organization'):
                org = execution._organization
                if org and org.agents:
                    for agent in org.agents:
                        if agent.id == agent_id:
                            return agent.name
                            
        # Fallback to agent ID if we can't find the name
        return f'Agent-{agent_id[:8]}'
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel workflow execution"""
        
        execution = self.active_executions.get(execution_id)
        if execution:
            execution.status = ExecutionStatus.CANCELLED
            execution.actual_completion = datetime.utcnow()
            # Update status in database
            await workflow_execution_service.update_execution_status(execution_id, ExecutionStatus.CANCELLED, "Cancelled by user")
            return True
        return False