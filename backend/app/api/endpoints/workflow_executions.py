from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.workflow_execution_service import workflow_execution_service
from app.models.agent_organization import ExecutionStatus
from app.auth.auth import get_current_user
from app.models.user import User
from openai import OpenAI
import os

# Initialize orchestrator with LLM client
try:
    llm_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception:
    llm_client = None

# Import orchestrator
from app.services.workflow_orchestrator import WorkflowOrchestrator
orchestrator = WorkflowOrchestrator(llm_client=llm_client)

router = APIRouter()


class ExecutionCreateRequest(BaseModel):
    workflow_template_id: str = Field(..., description="ID of the workflow template to execute")
    organization_id: Optional[str] = Field(None, description="ID of the agent organization to use")
    execution_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Initial execution context")
    priority: int = Field(default=1, ge=1, le=10, description="Execution priority (1=highest, 10=lowest)")
    use_memory_enhancement: bool = Field(default=True, description="Use Graphiti memory enhancement for agents")


class TaskResponse(BaseModel):
    id: str
    name: str
    description: str
    objective: str
    completion_criteria: str
    status: str
    assigned_agent_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str]
    context: Dict[str, Any]
    results: Dict[str, Any]
    human_feedback: Optional[str] = None


class ExecutionResponse(BaseModel):
    id: str
    workflow_template_id: str
    organization_id: Optional[str] = None
    status: str
    current_tasks: List[str]
    completed_tasks: List[str]
    failed_tasks: List[str]
    tasks: List[TaskResponse]
    execution_context: Dict[str, Any]
    human_approvals_pending: List[str]
    human_feedback: List[Dict[str, Any]]
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    initiated_by: str
    agent_actions: List[Dict[str, Any]]
    error_log: List[Dict[str, Any]]


class ExecutionListResponse(BaseModel):
    executions: List[ExecutionResponse]
    total_count: int


class ExecutionStatsResponse(BaseModel):
    total_executions: int
    status_breakdown: Dict[str, int]
    recent_executions: int
    generated_at: str


@router.post("/{template_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    template_id: str,
    request: ExecutionCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start executing a workflow template
    """
    try:
        # Override template_id from URL
        request.workflow_template_id = template_id
        
        # Enhanced context with memory settings
        enhanced_context = {
            **(request.execution_context or {}),
            "user_id": current_user.id,
            "user_role": current_user.role.value,
            "priority": request.priority,
            "use_memory_enhancement": request.use_memory_enhancement,
            "memory_enabled": request.use_memory_enhancement
        }
        
        # Use orchestrator for consistent execution path (includes memory enhancement)
        execution = await orchestrator.initiate_workflow_execution(
            workflow_template_id=request.workflow_template_id,
            organization_id=request.organization_id or "default-org",
            initiated_by=current_user.id,
            initial_context=enhanced_context
        )
        
        # Convert tasks to response format
        task_responses = []
        for task in execution.tasks:
            task_responses.append(TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                objective=task.objective,
                completion_criteria=task.completion_criteria,
                status=task.status.value,
                assigned_agent_id=task.assigned_agent_id,
                started_at=task.started_at,
                completed_at=task.completed_at,
                dependencies=task.dependencies,
                context=task.context,
                results=task.results,
                human_feedback=task.human_feedback
            ))
        
        return ExecutionResponse(
            id=execution.id,
            workflow_template_id=execution.workflow_template_id,
            organization_id=execution.organization_id,
            status=execution.status.value,
            current_tasks=execution.current_tasks,
            completed_tasks=execution.completed_tasks,
            failed_tasks=execution.failed_tasks,
            tasks=task_responses,
            execution_context=execution.execution_context,
            human_approvals_pending=execution.human_approvals_pending,
            human_feedback=execution.human_feedback,
            started_at=execution.started_at,
            estimated_completion=execution.estimated_completion,
            actual_completion=execution.actual_completion,
            initiated_by=execution.initiated_by,
            agent_actions=execution.agent_actions,
            error_log=execution.error_log
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    status: Optional[str] = Query(None, description="Filter by execution status"),
    workflow_template_id: Optional[str] = Query(None, description="Filter by workflow template ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of executions to return"),
    offset: int = Query(0, ge=0, description="Number of executions to skip"),
    current_user: User = Depends(get_current_user)
):
    """
    List workflow executions with optional filtering
    """
    try:
        # Convert status string to enum if provided
        status_filter = None
        if status:
            try:
                status_filter = ExecutionStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        executions = await workflow_execution_service.list_executions(
            initiated_by=current_user.id,  # Only show user's own executions
            status=status_filter,
            workflow_template_id=workflow_template_id,
            limit=limit,
            offset=offset
        )
        
        execution_responses = []
        for execution in executions:
            # Convert tasks to response format
            task_responses = []
            for task in execution.tasks:
                task_responses.append(TaskResponse(
                    id=task.id,
                    name=task.name,
                    description=task.description,
                    objective=task.objective,
                    completion_criteria=task.completion_criteria,
                    status=task.status.value,
                    assigned_agent_id=task.assigned_agent_id,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    dependencies=task.dependencies,
                    context=task.context,
                    results=task.results,
                    human_feedback=task.human_feedback
                ))
            
            execution_responses.append(ExecutionResponse(
                id=execution.id,
                workflow_template_id=execution.workflow_template_id,
                organization_id=execution.organization_id,
                status=execution.status.value,
                current_tasks=execution.current_tasks,
                completed_tasks=execution.completed_tasks,
                failed_tasks=execution.failed_tasks,
                tasks=task_responses,
                execution_context=execution.execution_context,
                human_approvals_pending=execution.human_approvals_pending,
                human_feedback=execution.human_feedback,
                started_at=execution.started_at,
                estimated_completion=execution.estimated_completion,
                actual_completion=execution.actual_completion,
                initiated_by=execution.initiated_by,
                agent_actions=execution.agent_actions,
                error_log=execution.error_log
            ))
        
        return ExecutionListResponse(
            executions=execution_responses,
            total_count=len(execution_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific workflow execution
    """
    try:
        execution = await workflow_execution_service.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Check if user owns this execution
        if execution.initiated_by != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert tasks to response format
        task_responses = []
        for task in execution.tasks:
            task_responses.append(TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                objective=task.objective,
                completion_criteria=task.completion_criteria,
                status=task.status.value,
                assigned_agent_id=task.assigned_agent_id,
                started_at=task.started_at,
                completed_at=task.completed_at,
                dependencies=task.dependencies,
                context=task.context,
                results=task.results,
                human_feedback=task.human_feedback
            ))
        
        return ExecutionResponse(
            id=execution.id,
            workflow_template_id=execution.workflow_template_id,
            organization_id=execution.organization_id,
            status=execution.status.value,
            current_tasks=execution.current_tasks,
            completed_tasks=execution.completed_tasks,
            failed_tasks=execution.failed_tasks,
            tasks=task_responses,
            execution_context=execution.execution_context,
            human_approvals_pending=execution.human_approvals_pending,
            human_feedback=execution.human_feedback,
            started_at=execution.started_at,
            estimated_completion=execution.estimated_completion,
            actual_completion=execution.actual_completion,
            initiated_by=execution.initiated_by,
            agent_actions=execution.agent_actions,
            error_log=execution.error_log
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")


@router.post("/{execution_id}/pause")
async def pause_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Pause a running workflow execution
    """
    try:
        # Verify ownership
        execution = await workflow_execution_service.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        if execution.initiated_by != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await workflow_execution_service.pause_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to pause execution")
        
        return {"message": "Execution paused successfully", "execution_id": execution_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause execution: {str(e)}")


@router.post("/{execution_id}/resume")
async def resume_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Resume a paused workflow execution
    """
    try:
        # Verify ownership
        execution = await workflow_execution_service.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        if execution.initiated_by != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await workflow_execution_service.resume_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to resume execution")
        
        return {"message": "Execution resumed successfully", "execution_id": execution_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume execution: {str(e)}")


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a workflow execution
    """
    try:
        # Verify ownership
        execution = await workflow_execution_service.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        if execution.initiated_by != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await workflow_execution_service.cancel_execution(execution_id, "Cancelled by user")
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel execution")
        
        return {"message": "Execution cancelled successfully", "execution_id": execution_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")


@router.get("/stats/overview", response_model=ExecutionStatsResponse)
async def get_execution_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get workflow execution statistics
    """
    try:
        stats = await workflow_execution_service.get_execution_stats()
        
        return ExecutionStatsResponse(
            total_executions=stats.get('total_executions', 0),
            status_breakdown=stats.get('status_breakdown', {}),
            recent_executions=stats.get('recent_executions', 0),
            generated_at=stats.get('generated_at', '')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution stats: {str(e)}")