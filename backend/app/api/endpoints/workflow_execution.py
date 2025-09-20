from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.auth.auth import get_current_user
from app.models.user import User
from openai import OpenAI
import os

# Initialize OpenAI client
try:
    llm_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception:
    # Warning: OpenAI client initialization failed - continuing without LLM
    llm_client = None

# Global orchestrator instance
orchestrator = WorkflowOrchestrator(llm_client=llm_client)

router = APIRouter()


class WorkflowExecutionRequest(BaseModel):
    workflow_template_id: str = Field(..., description="ID of workflow template to execute")
    organization_id: str = Field(default="default-org", description="Agent organization to use")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Initial execution context")
    priority: int = Field(default=1, ge=1, le=10, description="Execution priority")
    use_memory_enhancement: bool = Field(default=True, description="Use Graphiti memory enhancement for agents")


class WorkflowExecutionResponse(BaseModel):
    execution_id: str
    status: str
    workflow_template_id: str
    organization_id: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    task_count: int
    agent_count: int
    message: str


class ExecutionStatusResponse(BaseModel):
    execution_id: str
    status: str
    progress: Dict[str, Any]
    started_at: str
    estimated_completion: Optional[str] = None
    human_approvals_pending: int
    agent_actions_count: int
    current_phase: Optional[str] = None


class HumanInteractionResponse(BaseModel):
    interaction_id: str
    execution_id: str
    task_id: str
    agent_id: str
    interaction_type: str
    message: str
    context: Dict[str, Any]
    options: List[str]
    requested_at: datetime
    response_deadline: Optional[datetime] = None
    status: str


class HumanResponseRequest(BaseModel):
    response: str = Field(..., description="Human response text")
    choice: Optional[str] = Field(None, description="Selected choice from options")
    additional_feedback: Optional[str] = Field(None, description="Additional feedback")


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def start_workflow_execution(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Start execution of a workflow template with multi-agent coordination
    """
    try:
        # Enhanced context with memory settings
        enhanced_context = {
            **request.execution_context,
            "user_id": current_user.id,
            "user_role": current_user.role.value,
            "priority": request.priority,
            "use_memory_enhancement": request.use_memory_enhancement,
            "memory_enabled": request.use_memory_enhancement
        }
        
        # Start workflow execution with the orchestrator (which now includes Graphiti memory enhancement)
        execution = await orchestrator.initiate_workflow_execution(
            workflow_template_id=request.workflow_template_id,
            organization_id=request.organization_id,
            initiated_by=current_user.id,
            initial_context=enhanced_context
        )
        
        if request.use_memory_enhancement:
            message = f"Graphiti temporal memory-enhanced workflow execution started with {len(execution.tasks)} tasks"
        else:
            message = f"Standard workflow execution started with {len(execution.tasks)} tasks"
        
        return WorkflowExecutionResponse(
            execution_id=execution.id,
            status=execution.status,
            workflow_template_id=execution.workflow_template_id,
            organization_id=execution.organization_id,
            started_at=execution.started_at,
            estimated_completion=execution.estimated_completion,
            task_count=len(execution.tasks),
            agent_count=len(orchestrator.agent_instances),
            message=message
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow execution: {str(e)}")


@router.get("/execute/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get current status of workflow execution
    """
    try:
        status = await orchestrator.get_execution_status(execution_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return ExecutionStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")


@router.get("/execute/{execution_id}/human-interactions")
async def get_pending_human_interactions(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get pending human interactions for workflow execution
    """
    try:
        # Get execution
        execution = orchestrator.active_executions.get(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Get pending interactions
        pending_interactions = []
        for interaction_id, interaction in orchestrator.pending_human_interactions.items():
            if interaction.execution_id == execution_id:
                pending_interactions.append(HumanInteractionResponse(
                    interaction_id=interaction.id,
                    execution_id=interaction.execution_id,
                    task_id=interaction.task_id,
                    agent_id=interaction.agent_id,
                    interaction_type=interaction.interaction_type,
                    message=interaction.message,
                    context=interaction.context,
                    options=interaction.options,
                    requested_at=interaction.requested_at,
                    response_deadline=interaction.response_deadline,
                    status=interaction.status
                ))
        
        return {
            "execution_id": execution_id,
            "pending_interactions": pending_interactions,
            "total_count": len(pending_interactions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get human interactions: {str(e)}")


@router.post("/execute/{execution_id}/human-interactions/{interaction_id}/respond")
async def respond_to_human_interaction(
    execution_id: str,
    interaction_id: str,
    response_request: HumanResponseRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Respond to a human interaction request
    """
    try:
        success = await orchestrator.respond_to_human_interaction(
            interaction_id=interaction_id,
            response=response_request.response,
            choice=response_request.choice
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Interaction not found or already responded")
        
        return {
            "status": "success",
            "message": "Human response recorded successfully",
            "interaction_id": interaction_id,
            "execution_id": execution_id,
            "responded_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record human response: {str(e)}")


@router.post("/execute/{execution_id}/pause")
async def pause_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Pause workflow execution
    """
    try:
        success = await orchestrator.pause_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "status": "success",
            "message": "Workflow execution paused",
            "execution_id": execution_id,
            "paused_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause execution: {str(e)}")


@router.post("/execute/{execution_id}/resume")
async def resume_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Resume paused workflow execution
    """
    try:
        success = await orchestrator.resume_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found or not paused")
        
        return {
            "status": "success",
            "message": "Workflow execution resumed",
            "execution_id": execution_id,
            "resumed_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume execution: {str(e)}")


@router.post("/execute/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel workflow execution
    """
    try:
        success = await orchestrator.cancel_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "status": "success",
            "message": "Workflow execution cancelled",
            "execution_id": execution_id,
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")


@router.get("/execute/active")
async def get_active_executions(
    current_user: User = Depends(get_current_user)
):
    """
    Get all active workflow executions
    """
    try:
        active_executions = []
        
        for execution_id, execution in orchestrator.active_executions.items():
            # Check if user has access (admin or initiator)
            if (current_user.role.value == "admin" or 
                execution.initiated_by == current_user.id):
                
                status = await orchestrator.get_execution_status(execution_id)
                if status:
                    active_executions.append(status)
        
        return {
            "active_executions": active_executions,
            "total_count": len(active_executions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active executions: {str(e)}")


@router.get("/execute/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    Get execution logs and agent actions
    """
    try:
        execution = orchestrator.active_executions.get(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Check access permissions
        if (current_user.role.value != "admin" and 
            execution.initiated_by != current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get agent actions with pagination
        all_actions = execution.agent_actions
        paginated_actions = all_actions[offset:offset + limit]
        
        # Get human feedback
        human_feedback = execution.human_feedback
        
        # Get error log
        error_log = execution.error_log
        
        return {
            "execution_id": execution_id,
            "agent_actions": paginated_actions,
            "human_feedback": human_feedback,
            "error_log": error_log,
            "pagination": {
                "total_actions": len(all_actions),
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < len(all_actions)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution logs: {str(e)}")


@router.get("/organizations")
async def get_agent_organizations(
    current_user: User = Depends(get_current_user)
):
    """
    Get available agent organizations
    """
    try:
        # Mock implementation - in real system would query database
        organizations = [
            {
                "id": "default-org",
                "name": "Default Workflow Organization",
                "description": "Default multi-agent organization for workflow execution",
                "agent_count": 3,
                "capabilities": ["coordination", "task_execution", "validation"],
                "use_cases": ["IT Support", "HR Processes", "Customer Service"]
            },
            {
                "id": "it-support-org",
                "name": "IT Support Organization",
                "description": "Specialized organization for IT support workflows",
                "agent_count": 5,
                "capabilities": ["ticket_management", "technical_diagnosis", "user_support"],
                "use_cases": ["Password Reset", "System Issues", "Access Requests"]
            },
            {
                "id": "hr-org",
                "name": "HR Organization",
                "description": "Human Resources workflow organization",
                "agent_count": 4,
                "capabilities": ["employee_onboarding", "policy_guidance", "benefits_management"],
                "use_cases": ["Employee Onboarding", "Benefits Enrollment", "Policy Questions"]
            }
        ]
        
        return {
            "organizations": organizations,
            "total_count": len(organizations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organizations: {str(e)}")


@router.post("/execute/from-intent")
async def execute_workflow_from_intent(
    workflow_template_id: str,
    execution_context: Dict[str, Any],
    organization_id: str = "default-org",
    current_user: User = Depends(get_current_user)
):
    """
    Execute workflow from intent detection result
    """
    try:
        # Enhanced context with memory settings (defaulting to enabled for intent-based execution)
        enhanced_context = {
            **execution_context,
            "triggered_by": "intent_detection",
            "user_id": current_user.id,
            "user_role": current_user.role.value,
            "use_memory_enhancement": True,
            "memory_enabled": True
        }
        
        # Start workflow execution (memory enhancement handled by orchestrator)
        execution = await orchestrator.initiate_workflow_execution(
            workflow_template_id=workflow_template_id,
            organization_id=organization_id,
            initiated_by=current_user.id,
            initial_context=enhanced_context
        )
        
        return {
            "status": "success",
            "message": "Workflow execution started from intent detection",
            "execution_id": execution.id,
            "workflow_template_id": workflow_template_id,
            "organization_id": organization_id,
            "started_at": execution.started_at.isoformat(),
            "task_count": len(execution.tasks)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow from intent: {str(e)}")