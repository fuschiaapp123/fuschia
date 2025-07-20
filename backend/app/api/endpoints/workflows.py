from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.template_service import template_service
from app.models.template import TemplateCreate, TemplateType, TemplateComplexity, TemplateStatus
from app.auth.auth import get_current_user
from app.models.user import User

router = APIRouter()


class WorkflowSaveRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., max_length=100)
    complexity: str = Field(default="medium")
    estimated_time: str = Field(default="Variable", max_length=50)
    tags: List[str] = Field(default_factory=list)
    preview_steps: List[str] = Field(default_factory=list)
    template_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorkflowSaveResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    template_type: str
    complexity: str
    estimated_time: str
    usage_count: int
    status: str
    created_at: datetime
    created_by: Optional[str] = None


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowSaveResponse]
    total_count: int
    categories: List[str]


@router.post("/save", response_model=WorkflowSaveResponse)
async def save_workflow(
    workflow_data: WorkflowSaveRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Save a workflow to the PostgreSQL database.
    If a workflow with the same name exists for this user, it will be updated.
    Otherwise, a new workflow will be created.
    """
    try:
        # Map complexity string to enum
        complexity_map = {
            "simple": TemplateComplexity.SIMPLE,
            "medium": TemplateComplexity.MEDIUM,
            "advanced": TemplateComplexity.ADVANCED
        }
        
        complexity = complexity_map.get(workflow_data.complexity.lower(), TemplateComplexity.MEDIUM)
        
        # Create template from workflow data
        template_create = TemplateCreate(
            name=workflow_data.name,
            description=workflow_data.description,
            category=workflow_data.category,
            template_type=TemplateType.WORKFLOW,
            complexity=complexity,
            estimated_time=workflow_data.estimated_time,
            tags=workflow_data.tags if workflow_data.tags else [workflow_data.category, "Custom"],
            preview_steps=workflow_data.preview_steps,
            template_data=workflow_data.template_data,
            metadata=workflow_data.metadata or {}
        )
        
        # Save to database (upsert: update if exists, create if new)
        saved_template = await template_service.upsert_template(
            template_data=template_create,
            created_by=current_user.id
        )
        
        # Convert to response format
        return WorkflowSaveResponse(
            id=saved_template.id,
            name=saved_template.name,
            description=saved_template.description,
            category=saved_template.category,
            template_type=saved_template.template_type.value,
            complexity=saved_template.complexity.value,
            estimated_time=saved_template.estimated_time,
            usage_count=saved_template.usage_count,
            status=saved_template.status.value,
            created_at=saved_template.created_at,
            created_by=saved_template.created_by
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save workflow: {str(e)}")


@router.get("/", response_model=WorkflowListResponse)
async def get_workflows(
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    Get workflows from the database with optional filtering
    """
    try:
        # Search for workflow templates
        search_result = await template_service.search_templates(
            template_type=TemplateType.WORKFLOW,
            category=category,
            status=TemplateStatus.ACTIVE,
            limit=limit
        )
        
        # Convert to response format
        workflows = []
        for template_match in search_result.templates[offset:offset+limit]:
            # Get full template details
            full_template = await template_service.get_template(template_match.template_id)
            if full_template:
                workflows.append(WorkflowSaveResponse(
                    id=full_template.id,
                    name=full_template.name,
                    description=full_template.description,
                    category=full_template.category,
                    template_type=full_template.template_type.value,
                    complexity=full_template.complexity.value,
                    estimated_time=full_template.estimated_time,
                    usage_count=full_template.usage_count,
                    status=full_template.status.value,
                    created_at=full_template.created_at,
                    created_by=full_template.created_by
                ))
        
        return WorkflowListResponse(
            workflows=workflows,
            total_count=search_result.total_count,
            categories=search_result.categories_found
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific workflow by ID
    """
    try:
        template = await template_service.get_template(workflow_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if template.template_type != TemplateType.WORKFLOW:
            raise HTTPException(status_code=400, detail="Template is not a workflow")
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "template_type": template.template_type.value,
            "complexity": template.complexity.value,
            "estimated_time": template.estimated_time,
            "tags": template.tags,
            "preview_steps": template.preview_steps,
            "template_data": template.template_data,
            "metadata": template.metadata,
            "usage_count": template.usage_count,
            "status": template.status.value,
            "created_at": template.created_at,
            "created_by": template.created_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")


@router.put("/{workflow_id}", response_model=WorkflowSaveResponse)
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowSaveRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing workflow
    """
    try:
        # Check if workflow exists
        existing_template = await template_service.get_template(workflow_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if existing_template.template_type != TemplateType.WORKFLOW:
            raise HTTPException(status_code=400, detail="Template is not a workflow")
        
        # Check if user owns the workflow or is admin
        if existing_template.created_by != current_user.id and current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to update this workflow")
        
        # Map complexity
        complexity_map = {
            "simple": TemplateComplexity.SIMPLE,
            "medium": TemplateComplexity.MEDIUM,
            "advanced": TemplateComplexity.ADVANCED
        }
        complexity = complexity_map.get(workflow_data.complexity.lower(), TemplateComplexity.MEDIUM)
        
        # Create update data
        template_update = TemplateCreate(
            name=workflow_data.name,
            description=workflow_data.description,
            category=workflow_data.category,
            template_type=TemplateType.WORKFLOW,
            complexity=complexity,
            estimated_time=workflow_data.estimated_time,
            tags=workflow_data.tags if workflow_data.tags else [workflow_data.category, "Updated"],
            preview_steps=workflow_data.preview_steps,
            template_data=workflow_data.template_data,
            metadata={
                **(workflow_data.metadata or {}),
                "updated": datetime.utcnow().isoformat(),
                "updated_by": current_user.id
            }
        )
        
        # Update the template in the database
        updated_template = await template_service.update_template(
            template_id=workflow_id,
            template_data=template_update,
            updated_by=current_user.id
        )
        
        return WorkflowSaveResponse(
            id=updated_template.id,
            name=updated_template.name,
            description=updated_template.description,
            category=updated_template.category,
            template_type=updated_template.template_type.value,
            complexity=updated_template.complexity.value,
            estimated_time=updated_template.estimated_time,
            usage_count=updated_template.usage_count,
            status=updated_template.status.value,
            created_at=updated_template.created_at,
            created_by=updated_template.created_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a workflow (mark as inactive)
    """
    try:
        # Check if workflow exists
        existing_template = await template_service.get_template(workflow_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if existing_template.template_type != TemplateType.WORKFLOW:
            raise HTTPException(status_code=400, detail="Template is not a workflow")
        
        # Check if user owns the workflow or is admin
        if existing_template.created_by != current_user.id and current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this workflow")
        
        # Soft delete the template
        success = await template_service.delete_template(workflow_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Workflow '{existing_template.name}' deleted successfully",
                "workflow_id": workflow_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete workflow")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")


@router.post("/{workflow_id}/use")
async def use_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Increment usage count when a workflow is used
    """
    try:
        # Update usage count
        success = await template_service.update_template_usage(workflow_id)
        
        if success:
            return {
                "status": "success",
                "message": "Workflow usage updated",
                "workflow_id": workflow_id
            }
        else:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow usage: {str(e)}")