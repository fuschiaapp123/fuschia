"""
MCP Monitor API Endpoints
Provides REST API for managing and monitoring MCP services
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.auth.auth import get_current_user
from app.models.user import User
from app.services.mcp_monitor_service import mcp_monitor_service

router = APIRouter()


class ServiceConfigRequest(BaseModel):
    """Request model for updating service configuration"""
    enabled: bool = Field(default=True, description="Enable/disable the service")
    auto_start: bool = Field(default=False, description="Auto-start service on initialization")


class ServiceStatusResponse(BaseModel):
    """Response model for service status"""
    service_id: str
    service_name: str
    is_running: bool
    status: str
    capabilities: List[str]
    config: Dict[str, Any]


class ServiceActionResponse(BaseModel):
    """Response model for service actions"""
    success: bool
    message: str


@router.get("/services", response_model=List[ServiceStatusResponse])
async def get_all_services(current_user: User = Depends(get_current_user)):
    """Get status of all MCP services"""
    try:
        # Initialize service if not already done
        if not mcp_monitor_service.initialized:
            await mcp_monitor_service.initialize()

        services = await mcp_monitor_service.get_all_services_status()
        return services

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get services status: {str(e)}")


@router.get("/services/{service_id}", response_model=ServiceStatusResponse)
async def get_service_status(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a specific MCP service"""
    try:
        # Initialize service if not already done
        if not mcp_monitor_service.initialized:
            await mcp_monitor_service.initialize()

        status = await mcp_monitor_service.get_service_status(service_id)
        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")


@router.post("/services/{service_id}/start", response_model=ServiceActionResponse)
async def start_service(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Start a specific MCP service"""
    try:
        # Initialize service if not already done
        if not mcp_monitor_service.initialized:
            await mcp_monitor_service.initialize()

        result = await mcp_monitor_service.start_service(service_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to start service"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start service: {str(e)}")


@router.post("/services/{service_id}/stop", response_model=ServiceActionResponse)
async def stop_service(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stop a specific MCP service"""
    try:
        # Initialize service if not already done
        if not mcp_monitor_service.initialized:
            await mcp_monitor_service.initialize()

        result = await mcp_monitor_service.stop_service(service_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to stop service"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop service: {str(e)}")


@router.post("/services/{service_id}/test")
async def test_service_connection(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Test connection to a specific MCP service"""
    try:
        # Initialize service if not already done
        if not mcp_monitor_service.initialized:
            await mcp_monitor_service.initialize()

        result = await mcp_monitor_service.test_service_connection(service_id)
        return result

    except Exception as e:
        return {
            "success": False,
            "service_id": service_id,
            "message": f"Connection test failed: {str(e)}"
        }


@router.put("/services/{service_id}/config", response_model=ServiceActionResponse)
async def update_service_config(
    service_id: str,
    config: ServiceConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Update configuration for a specific MCP service"""
    try:
        # Initialize service if not already done
        if not mcp_monitor_service.initialized:
            await mcp_monitor_service.initialize()

        config_dict = {
            "enabled": config.enabled,
            "auto_start": config.auto_start
        }

        result = await mcp_monitor_service.update_service_config(service_id, config_dict)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to update config"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")
