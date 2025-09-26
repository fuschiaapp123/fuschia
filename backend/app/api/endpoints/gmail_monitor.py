"""
Gmail Monitor API Endpoints
Provides REST API for managing Gmail mailbox monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.auth.auth import get_current_user
from app.models.user import User
from app.services.gmail_monitor_service import gmail_monitor_service, MonitoringConfig

router = APIRouter()


class MonitoringConfigRequest(BaseModel):
    """Request model for updating monitoring configuration"""
    enabled: bool = Field(default=False, description="Enable/disable Gmail monitoring")
    check_interval_seconds: int = Field(default=300, ge=60, le=3600, description="Check interval in seconds (1-60 minutes)")
    query_filter: str = Field(default="is:unread", description="Gmail query filter for messages")
    max_messages_per_check: int = Field(default=10, ge=1, le=50, description="Maximum messages to process per check")
    intent_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence for workflow triggering")
    auto_trigger_workflows: bool = Field(default=True, description="Automatically trigger workflows based on intent")
    excluded_senders: List[str] = Field(default_factory=list, description="Email addresses to exclude from processing")
    included_labels: List[str] = Field(default_factory=list, description="Gmail labels to include (empty = all)")


class MonitoringStatusResponse(BaseModel):
    """Response model for monitoring status"""
    is_running: bool
    config: Dict[str, Any]
    processed_messages_count: int
    gmail_server_status: bool
    intent_agent_available: bool
    last_check_time: Optional[datetime] = None


class MonitoringStatsResponse(BaseModel):
    """Response model for monitoring statistics"""
    total_emails_processed: int
    workflows_triggered: int
    intents_classified: Dict[str, int]
    confidence_distribution: Dict[str, int]
    processing_errors: int


class TestIntentRequest(BaseModel):
    """Request model for testing intent classification"""
    email_content: str = Field(..., description="Email content to test intent classification on")


@router.post("/start")
async def start_monitoring(
    config: Optional[MonitoringConfigRequest] = None,
    current_user: User = Depends(get_current_user)
):
    """Start Gmail mailbox monitoring"""
    try:
        # Initialize service if not already done
        if not gmail_monitor_service.intent_agent:
            await gmail_monitor_service.initialize()

        # Convert config if provided
        monitoring_config = None
        if config:
            monitoring_config = MonitoringConfig(
                enabled=config.enabled,
                check_interval_seconds=config.check_interval_seconds,
                query_filter=config.query_filter,
                max_messages_per_check=config.max_messages_per_check,
                intent_confidence_threshold=config.intent_confidence_threshold,
                auto_trigger_workflows=config.auto_trigger_workflows,
                excluded_senders=config.excluded_senders,
                included_labels=config.included_labels
            )

        await gmail_monitor_service.start_monitoring(monitoring_config)

        return {
            "message": "Gmail monitoring started successfully",
            "status": await gmail_monitor_service.get_monitoring_status()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/stop")
async def stop_monitoring(current_user: User = Depends(get_current_user)):
    """Stop Gmail mailbox monitoring"""
    try:
        await gmail_monitor_service.stop_monitoring()

        return {
            "message": "Gmail monitoring stopped successfully",
            "status": await gmail_monitor_service.get_monitoring_status()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(current_user: User = Depends(get_current_user)):
    """Get current Gmail monitoring status"""
    try:
        status = await gmail_monitor_service.get_monitoring_status()
        return MonitoringStatusResponse(**status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.put("/config")
async def update_monitoring_config(
    config: MonitoringConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Update Gmail monitoring configuration"""
    try:
        config_dict = {
            "enabled": config.enabled,
            "check_interval_seconds": config.check_interval_seconds,
            "query_filter": config.query_filter,
            "max_messages_per_check": config.max_messages_per_check,
            "intent_confidence_threshold": config.intent_confidence_threshold,
            "auto_trigger_workflows": config.auto_trigger_workflows,
            "excluded_senders": config.excluded_senders,
            "included_labels": config.included_labels
        }

        await gmail_monitor_service.update_config(config_dict)

        return {
            "message": "Monitoring configuration updated successfully",
            "config": config_dict,
            "status": await gmail_monitor_service.get_monitoring_status()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.get("/config")
async def get_monitoring_config(current_user: User = Depends(get_current_user)):
    """Get current Gmail monitoring configuration"""
    try:
        status = await gmail_monitor_service.get_monitoring_status()
        return {
            "config": status.get("config", {}),
            "is_running": status.get("is_running", False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/test-intent")
async def test_intent_classification(
    request: TestIntentRequest,
    current_user: User = Depends(get_current_user)
):
    """Test intent classification on provided email content"""
    try:
        # Initialize service if needed
        if not gmail_monitor_service.intent_agent:
            await gmail_monitor_service.initialize()

        # Classify intent
        intent_result = await gmail_monitor_service._classify_email_intent(request.email_content, None)

        return {
            "email_content": request.email_content,
            "intent_result": intent_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test intent classification: {str(e)}")


@router.post("/check-now")
async def check_for_emails_now(current_user: User = Depends(get_current_user)):
    """Manually trigger an immediate check for new emails"""
    try:
        # Initialize service if needed
        if not gmail_monitor_service.intent_agent:
            await gmail_monitor_service.initialize()

        # Manually check for emails
        await gmail_monitor_service._check_for_new_emails()

        return {
            "message": "Manual email check completed successfully",
            "status": await gmail_monitor_service.get_monitoring_status()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check emails: {str(e)}")


@router.get("/test-connection")
async def test_gmail_connection(current_user: User = Depends(get_current_user)):
    """Test Gmail connection and authentication"""
    try:
        # Initialize service if needed
        if not gmail_monitor_service.intent_agent:
            await gmail_monitor_service.initialize()

        # Try to fetch a small number of messages to test connection
        from app.services.gmail_mcp_server import gmail_mcp_server

        test_result = await gmail_mcp_server.call_tool("gmail_list_messages", {
            "query": "in:inbox",
            "max_results": 1
        })

        if test_result and test_result[0].get('text'):
            import json
            data = json.loads(test_result[0]['text'])
            success = data.get('success', False)

            return {
                "connection_status": "success" if success else "failed",
                "gmail_server_running": gmail_mcp_server.is_running,
                "test_result": data
            }
        else:
            return {
                "connection_status": "failed",
                "gmail_server_running": gmail_mcp_server.is_running,
                "error": "No response from Gmail API"
            }

    except Exception as e:
        return {
            "connection_status": "error",
            "gmail_server_running": getattr(gmail_monitor_service, 'gmail_mcp_server', {}).get('is_running', False),
            "error": str(e)
        }


@router.get("/available-workflows")
async def get_available_workflows(current_user: User = Depends(get_current_user)):
    """Get list of available workflow templates for email triggering"""
    try:
        from app.services.template_service import template_service

        # Get workflow templates
        templates = await template_service.get_template_names("workflow")

        workflow_list = []
        for template in templates:
            workflow_list.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "complexity": template.complexity.value if hasattr(template.complexity, 'value') else str(template.complexity)
            })

        return {
            "workflows": workflow_list,
            "total_count": len(workflow_list)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")


@router.get("/logs")
async def get_monitoring_logs(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get recent monitoring logs (placeholder - would integrate with logging system)"""
    try:
        # This is a placeholder - in a real implementation, you'd integrate with your logging system
        # to retrieve recent Gmail monitoring logs

        return {
            "message": "Log retrieval not yet implemented",
            "logs": [],
            "note": "This endpoint would return recent Gmail monitoring activity logs"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.delete("/reset")
async def reset_monitoring_state(current_user: User = Depends(get_current_user)):
    """Reset monitoring state (clear processed messages cache, etc.)"""
    try:
        # Stop monitoring if running
        if gmail_monitor_service.is_running:
            await gmail_monitor_service.stop_monitoring()

        # Clear processed messages cache
        gmail_monitor_service.processed_messages.clear()

        return {
            "message": "Monitoring state reset successfully",
            "status": await gmail_monitor_service.get_monitoring_status()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset state: {str(e)}")