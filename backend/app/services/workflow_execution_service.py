from sqlalchemy import select, and_, desc
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import structlog

from app.db.postgres import WorkflowExecutionTable, WorkflowTaskTable, AsyncSessionLocal
from app.models.agent_organization import (
    WorkflowExecution, WorkflowTask, WorkflowExecutionCreate,
    ExecutionStatus, TaskStatus
)
from app.services.template_service import template_service

logger = structlog.get_logger()


class WorkflowExecutionService:
    """Service for managing workflow executions in PostgreSQL database"""
    
    def __init__(self):
        self.logger = logger.bind(service="WorkflowExecutionService")
    
    async def create_execution(
        self,
        workflow_template_id: str,
        initiated_by: str,
        organization_id: Optional[str] = None,
        execution_context: Optional[Dict[str, Any]] = None,
        priority: int = 1
    ) -> WorkflowExecution:
        """Create a new workflow execution from a template"""
        try:
            self.logger.info("Creating workflow execution", 
                           template_id=workflow_template_id, 
                           initiated_by=initiated_by)
            
            async with AsyncSessionLocal() as session:
                # Get the workflow template to extract tasks
                template = await template_service.get_template(workflow_template_id)
                if not template:
                    raise ValueError(f"Workflow template {workflow_template_id} not found")
                
                # Generate execution ID
                execution_id = str(uuid.uuid4())
                
                # Create tasks from template nodes
                tasks = []
                # Map original node IDs to new unique task IDs for dependency resolution
                node_id_mapping = {}
                
                if template.template_data and 'nodes' in template.template_data:
                    for node in template.template_data['nodes']:
                        original_node_id = node.get('id', str(uuid.uuid4()))
                        unique_task_id = str(uuid.uuid4())  # Always generate unique ID
                        
                        # Store mapping for dependency resolution
                        node_id_mapping[original_node_id] = unique_task_id
                        
                        task = WorkflowTask(
                            id=unique_task_id,
                            name=node.get('data', {}).get('label', 'Unnamed Task'),
                            description=node.get('data', {}).get('description', ''),
                            objective=node.get('data', {}).get('objective', ''),
                            completion_criteria=node.get('data', {}).get('completionCriteria', ''),
                            status=TaskStatus.PENDING,
                            dependencies=[],
                            context={
                                'node_type': node.get('data', {}).get('type', 'action'),
                                'position': node.get('position', {}),
                                'original_node_data': node.get('data', {}),
                                'original_node_id': original_node_id  # Store original ID for reference
                            }
                        )
                        tasks.append(task)
                
                # Process edges to set up task dependencies
                if template.template_data and 'edges' in template.template_data:
                    for edge in template.template_data['edges']:
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
                
                # Create workflow execution
                execution = WorkflowExecution(
                    id=execution_id,
                    workflow_template_id=workflow_template_id,
                    organization_id=organization_id,
                    status=ExecutionStatus.PENDING,
                    tasks=tasks,
                    execution_context=execution_context or {},
                    initiated_by=initiated_by,
                    started_at=datetime.utcnow(),
                    estimated_completion=datetime.utcnow() + timedelta(hours=2)  # Default estimate
                )
                
                # Save execution to database
                db_execution = WorkflowExecutionTable(
                    id=execution.id,
                    workflow_template_id=execution.workflow_template_id,
                    organization_id=execution.organization_id,
                    status=execution.status.value,
                    current_tasks=[],
                    completed_tasks=[],
                    failed_tasks=[],
                    execution_context=execution.execution_context,
                    human_approvals_pending=[],
                    human_feedback=[],
                    started_at=execution.started_at,
                    estimated_completion=execution.estimated_completion,
                    initiated_by=execution.initiated_by,
                    agent_actions=[],
                    error_log=[]
                )
                
                session.add(db_execution)
                
                # Save tasks to database
                for task in tasks:
                    db_task = WorkflowTaskTable(
                        id=task.id,
                        execution_id=execution_id,
                        name=task.name,
                        description=task.description,
                        objective=task.objective,
                        completion_criteria=task.completion_criteria,
                        status=task.status.value,
                        dependencies=task.dependencies,
                        context=task.context,
                        results=task.results
                    )
                    session.add(db_task)
                
                await session.commit()
                
                self.logger.info("Workflow execution created successfully", 
                               execution_id=execution_id, 
                               task_count=len(tasks))
                
                return execution
                
        except Exception as e:
            self.logger.error("Failed to create workflow execution", error=str(e))
            raise
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID"""
        try:
            async with AsyncSessionLocal() as session:
                # Get execution
                result = await session.execute(
                    select(WorkflowExecutionTable).where(WorkflowExecutionTable.id == execution_id)
                )
                db_execution = result.scalar_one_or_none()
                
                if not db_execution:
                    return None
                
                # Get tasks
                task_result = await session.execute(
                    select(WorkflowTaskTable).where(WorkflowTaskTable.execution_id == execution_id)
                )
                db_tasks = task_result.scalars().all()
                
                # Convert to domain models
                tasks = []
                for db_task in db_tasks:
                    task = WorkflowTask(
                        id=db_task.id,
                        name=db_task.name,
                        description=db_task.description or '',
                        objective=db_task.objective or '',
                        completion_criteria=db_task.completion_criteria or '',
                        status=TaskStatus(db_task.status),
                        assigned_agent_id=db_task.assigned_agent_id,
                        started_at=db_task.started_at,
                        completed_at=db_task.completed_at,
                        dependencies=db_task.dependencies,
                        context=db_task.context,
                        results=db_task.results,
                        human_feedback=db_task.human_feedback
                    )
                    tasks.append(task)
                
                execution = WorkflowExecution(
                    id=db_execution.id,
                    workflow_template_id=db_execution.workflow_template_id,
                    organization_id=db_execution.organization_id,
                    status=ExecutionStatus(db_execution.status),
                    current_tasks=db_execution.current_tasks,
                    completed_tasks=db_execution.completed_tasks,
                    failed_tasks=db_execution.failed_tasks,
                    tasks=tasks,
                    execution_context=db_execution.execution_context,
                    human_approvals_pending=db_execution.human_approvals_pending,
                    human_feedback=db_execution.human_feedback,
                    started_at=db_execution.started_at,
                    estimated_completion=db_execution.estimated_completion,
                    actual_completion=db_execution.actual_completion,
                    initiated_by=db_execution.initiated_by,
                    agent_actions=db_execution.agent_actions,
                    error_log=db_execution.error_log
                )
                
                return execution
                
        except Exception as e:
            self.logger.error("Failed to get workflow execution", execution_id=execution_id, error=str(e))
            return None
    
    async def update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update execution status"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(WorkflowExecutionTable).where(WorkflowExecutionTable.id == execution_id)
                )
                db_execution = result.scalar_one_or_none()
                
                if not db_execution:
                    return False
                
                db_execution.status = status.value
                db_execution.updated_at = datetime.utcnow()
                
                if status == ExecutionStatus.COMPLETED:
                    db_execution.actual_completion = datetime.utcnow()
                elif status == ExecutionStatus.FAILED and error_message:
                    error_entry = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'level': 'error',
                        'message': error_message,
                        'execution_id': execution_id
                    }
                    db_execution.error_log = db_execution.error_log + [error_entry]
                
                await session.commit()
                
                self.logger.info("Execution status updated", 
                               execution_id=execution_id, 
                               status=status.value)
                return True
                
        except Exception as e:
            self.logger.error("Failed to update execution status", 
                            execution_id=execution_id, 
                            error=str(e))
            return False
    
    async def list_executions(
        self,
        initiated_by: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        workflow_template_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters"""
        try:
            async with AsyncSessionLocal() as session:
                query = select(WorkflowExecutionTable)
                
                # Apply filters
                conditions = []
                if initiated_by:
                    conditions.append(WorkflowExecutionTable.initiated_by == initiated_by)
                if status:
                    conditions.append(WorkflowExecutionTable.status == status.value)
                if workflow_template_id:
                    conditions.append(WorkflowExecutionTable.workflow_template_id == workflow_template_id)
                
                if conditions:
                    query = query.where(and_(*conditions))
                
                query = query.order_by(desc(WorkflowExecutionTable.started_at))
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                db_executions = result.scalars().all()
                
                executions = []
                for db_execution in db_executions:
                    # Get tasks for this execution
                    task_result = await session.execute(
                        select(WorkflowTaskTable).where(WorkflowTaskTable.execution_id == db_execution.id)
                    )
                    db_tasks = task_result.scalars().all()
                    
                    tasks = []
                    for db_task in db_tasks:
                        task = WorkflowTask(
                            id=db_task.id,
                            name=db_task.name,
                            description=db_task.description or '',
                            objective=db_task.objective or '',
                            completion_criteria=db_task.completion_criteria or '',
                            status=TaskStatus(db_task.status),
                            assigned_agent_id=db_task.assigned_agent_id,
                            started_at=db_task.started_at,
                            completed_at=db_task.completed_at,
                            dependencies=db_task.dependencies,
                            context=db_task.context,
                            results=db_task.results,
                            human_feedback=db_task.human_feedback
                        )
                        tasks.append(task)
                    
                    execution = WorkflowExecution(
                        id=db_execution.id,
                        workflow_template_id=db_execution.workflow_template_id,
                        organization_id=db_execution.organization_id,
                        status=ExecutionStatus(db_execution.status),
                        current_tasks=db_execution.current_tasks,
                        completed_tasks=db_execution.completed_tasks,
                        failed_tasks=db_execution.failed_tasks,
                        tasks=tasks,
                        execution_context=db_execution.execution_context,
                        human_approvals_pending=db_execution.human_approvals_pending,
                        human_feedback=db_execution.human_feedback,
                        started_at=db_execution.started_at,
                        estimated_completion=db_execution.estimated_completion,
                        actual_completion=db_execution.actual_completion,
                        initiated_by=db_execution.initiated_by,
                        agent_actions=db_execution.agent_actions,
                        error_log=db_execution.error_log
                    )
                    executions.append(execution)
                
                return executions
                
        except Exception as e:
            self.logger.error("Failed to list workflow executions", error=str(e))
            return []
    
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause a running workflow execution"""
        return await self.update_execution_status(execution_id, ExecutionStatus.PAUSED)
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused workflow execution"""
        return await self.update_execution_status(execution_id, ExecutionStatus.RUNNING)
    
    async def cancel_execution(self, execution_id: str, reason: str = "Cancelled by user") -> bool:
        """Cancel a workflow execution"""
        return await self.update_execution_status(execution_id, ExecutionStatus.CANCELLED, reason)
    
    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        try:
            async with AsyncSessionLocal() as session:
                # Total executions
                total_result = await session.execute(
                    select(WorkflowExecutionTable)
                )
                total_executions = len(total_result.scalars().all())
                
                # Executions by status
                status_stats = {}
                for status in ExecutionStatus:
                    status_result = await session.execute(
                        select(WorkflowExecutionTable).where(WorkflowExecutionTable.status == status.value)
                    )
                    status_stats[status.value] = len(status_result.scalars().all())
                
                # Recent executions (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_result = await session.execute(
                    select(WorkflowExecutionTable).where(WorkflowExecutionTable.started_at >= week_ago)
                )
                recent_executions = len(recent_result.scalars().all())
                
                return {
                    'total_executions': total_executions,
                    'status_breakdown': status_stats,
                    'recent_executions': recent_executions,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error("Failed to get execution stats", error=str(e))
            return {}
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        agent_id: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update task status, assignment, and results in database"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(WorkflowTaskTable).where(WorkflowTaskTable.id == task_id)
                )
                db_task = result.scalar_one_or_none()
                
                if not db_task:
                    self.logger.warning("Task not found for status update", task_id=task_id)
                    return False
                
                # Update task status
                db_task.status = status.value
                
                # Update timestamps based on status
                if status == TaskStatus.IN_PROGRESS and not db_task.started_at:
                    db_task.started_at = datetime.utcnow()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and not db_task.completed_at:
                    db_task.completed_at = datetime.utcnow()
                
                # Update agent assignment if provided
                if agent_id:
                    db_task.assigned_agent_id = agent_id
                
                # Update results if provided
                if results:
                    db_task.results = results
                
                await session.commit()
                
                self.logger.debug("Updated task status", 
                                task_id=task_id, 
                                status=status.value,
                                agent_id=agent_id)
                return True
                
        except Exception as e:
            self.logger.error("Failed to update task status", 
                            task_id=task_id, 
                            status=status.value, 
                            error=str(e))
            return False
    
    async def update_task_assignment(self, task_id: str, agent_id: str) -> bool:
        """Update task agent assignment in database"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(WorkflowTaskTable).where(WorkflowTaskTable.id == task_id)
                )
                db_task = result.scalar_one_or_none()
                
                if not db_task:
                    self.logger.warning("Task not found for assignment update", task_id=task_id)
                    return False
                
                db_task.assigned_agent_id = agent_id
                await session.commit()
                
                self.logger.debug("Updated task assignment", task_id=task_id, agent_id=agent_id)
                return True
                
        except Exception as e:
            self.logger.error("Failed to update task assignment", 
                            task_id=task_id, agent_id=agent_id, error=str(e))
            return False
    
    async def update_task_results(self, task_id: str, results: Dict[str, Any]) -> bool:
        """Update task execution results in database"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(WorkflowTaskTable).where(WorkflowTaskTable.id == task_id)
                )
                db_task = result.scalar_one_or_none()
                
                if not db_task:
                    self.logger.warning("Task not found for results update", task_id=task_id)
                    return False
                
                db_task.results = results
                await session.commit()
                
                self.logger.debug("Updated task results", task_id=task_id)
                return True
                
        except Exception as e:
            self.logger.error("Failed to update task results", task_id=task_id, error=str(e))
            return False


# Global service instance
workflow_execution_service = WorkflowExecutionService()