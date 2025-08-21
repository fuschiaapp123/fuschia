from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from app.auth.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/workflow-executions")
async def get_workflow_executions(current_user: User = Depends(get_current_user)):
    """Get all workflow executions (admin/process_owner view)"""
    # Mock data for now - would come from database
    return [
        {
            "id": "exec-001",
            "workflow_template_id": "wf-template-001",
            "workflow_name": "Customer Onboarding Process",
            "status": "running",
            "current_tasks": [
                {"id": "task-2", "name": "KYC Verification", "status": "in_progress"},
                {"id": "task-3", "name": "Document Review", "status": "pending"}
            ],
            "completed_tasks": [
                {"id": "task-1", "name": "Initial Application", "status": "completed"}
            ],
            "failed_tasks": [],
            "started_at": datetime.now().isoformat(),
            "initiated_by": current_user.id,
            "initiated_by_name": current_user.full_name or current_user.username
        }
    ]

@router.get("/workflow-executions/me")
async def get_my_workflow_executions(current_user: User = Depends(get_current_user)):
    """Get workflow executions for current user"""
    # Mock data for now - would filter by current user
    return [
        {
            "id": "exec-001",
            "workflow_template_id": "wf-template-001", 
            "workflow_name": "Customer Onboarding Process",
            "status": "running",
            "current_tasks": [
                {"id": "task-2", "name": "KYC Verification", "status": "in_progress"}
            ],
            "completed_tasks": [
                {"id": "task-1", "name": "Initial Application", "status": "completed"}
            ],
            "failed_tasks": [],
            "started_at": datetime.now().isoformat(),
            "initiated_by": current_user.id,
            "initiated_by_name": current_user.full_name or current_user.username
        }
    ]

@router.get("/agent-organizations")
async def get_agent_organizations(current_user: User = Depends(get_current_user)):
    """Get all agent organizations (admin/process_owner view)"""
    # Mock data for now - would come from database
    return [
        {
            "id": "org-001",
            "name": "Customer Service Bot Network",
            "description": "Multi-agent system for automated customer support",
            "status": "running",
            "agents_data": [
                {"id": "agent-1", "name": "Intake Agent", "status": "active"},
                {"id": "agent-2", "name": "Classification Agent", "status": "busy"},
                {"id": "agent-3", "name": "Response Agent", "status": "idle"}
            ],
            "connections_data": [],
            "usage_count": 142,
            "created_by": current_user.id,
            "created_by_name": current_user.full_name or current_user.username,
            "last_activity": datetime.now().isoformat()
        }
    ]

@router.get("/agent-organizations/me")
async def get_my_agent_organizations(current_user: User = Depends(get_current_user)):
    """Get agent organizations for current user"""
    # Mock data for now - would filter by current user
    return [
        {
            "id": "org-001",
            "name": "Customer Service Bot Network", 
            "description": "Multi-agent system for automated customer support",
            "status": "running",
            "agents_data": [
                {"id": "agent-1", "name": "Intake Agent", "status": "active"}
            ],
            "connections_data": [],
            "usage_count": 142,
            "created_by": current_user.id,
            "created_by_name": current_user.full_name or current_user.username,
            "last_activity": datetime.now().isoformat()
        }
    ]