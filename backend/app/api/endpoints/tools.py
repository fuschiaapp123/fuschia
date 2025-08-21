"""
API endpoints for Tool Registry management
"""

import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer
import structlog

from app.models.tool_registry import (
    ToolFunction,
    ToolRegistryRequest,
    ToolRegistryResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolCategory,
    ToolStatus
)
from app.services.tool_registry_service import tool_registry_service
from app.auth.auth import get_current_active_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter(prefix="/tools", tags=["tools"])
security = HTTPBearer()


@router.post("/register", response_model=ToolRegistryResponse)
async def register_tool(
    request: ToolRegistryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Register a new tool function"""
    try:
        logger.info("Registering new tool", tool_name=request.name, user_id=current_user.id)
        
        response = tool_registry_service.register_tool(request, created_by=current_user.id)
        
        if response.success:
            logger.info("Tool registered successfully", tool_name=request.name, tool_id=response.tool.id if response.tool else None)
        else:
            logger.warning("Tool registration failed", tool_name=request.name, errors=response.errors)
        
        return response
        
    except Exception as e:
        logger.error("Failed to register tool", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to register tool: {str(e)}")


@router.get("/", response_model=List[ToolFunction])
async def list_tools(
    category: Optional[ToolCategory] = Query(None, description="Filter by category"),
    status: Optional[ToolStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user)
):
    """List all tools with optional filtering"""
    try:
        tools = tool_registry_service.get_tools(category=category, status=status)
        logger.info("Retrieved tools list", count=len(tools), user_id=current_user.id)
        return tools
        
    except Exception as e:
        logger.error("Failed to list tools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.get("/{tool_id}", response_model=ToolFunction)
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific tool by ID"""
    try:
        tool = tool_registry_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
        
        logger.info("Retrieved tool", tool_id=tool_id, tool_name=tool.name, user_id=current_user.id)
        return tool
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get tool", tool_id=tool_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get tool: {str(e)}")


@router.put("/{tool_id}", response_model=ToolRegistryResponse)
async def update_tool(
    tool_id: str,
    request: ToolRegistryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing tool"""
    try:
        # Check if tool exists
        tool = tool_registry_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
        
        # Check permissions (only creator or admin can update)
        if tool.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        logger.info("Updating tool", tool_id=tool_id, tool_name=request.name, user_id=current_user.id)
        
        response = tool_registry_service.update_tool(tool_id, request, updated_by=current_user.id)
        
        if response.success:
            logger.info("Tool updated successfully", tool_id=tool_id, tool_name=request.name, version=response.tool.version if response.tool else None)
        else:
            logger.warning("Tool update failed", tool_id=tool_id, errors=response.errors)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update tool", tool_id=tool_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a tool"""
    try:
        # Check if tool exists
        tool = tool_registry_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
        
        # Check permissions (only creator or admin can delete)
        if tool.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Permission denied")
        
        success = tool_registry_service.delete_tool(tool_id)
        if success:
            logger.info("Tool deleted", tool_id=tool_id, user_id=current_user.id)
            return {"message": "Tool deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete tool")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete tool", tool_id=tool_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Execute a tool function"""
    try:
        logger.info("Executing tool", tool_id=request.tool_id, user_id=current_user.id)
        
        response = tool_registry_service.execute_tool(request)
        
        if response.success:
            logger.info("Tool executed successfully", 
                       tool_id=request.tool_id, 
                       execution_time_ms=response.execution_time_ms)
        else:
            logger.warning("Tool execution failed", 
                          tool_id=request.tool_id, 
                          error=response.error_message)
        
        return response
        
    except Exception as e:
        logger.error("Failed to execute tool", tool_id=request.tool_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {str(e)}")


@router.post("/agents/{agent_id}/associate/{tool_id}")
async def associate_tool_with_agent(
    agent_id: str,
    tool_id: str,
    enabled: bool = True,
    priority: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """Associate a tool with an agent"""
    try:
        success = tool_registry_service.associate_tool_with_agent(
            agent_id=agent_id,
            tool_id=tool_id,
            enabled=enabled,
            priority=priority
        )
        
        if success:
            logger.info("Tool associated with agent", 
                       agent_id=agent_id, 
                       tool_id=tool_id, 
                       user_id=current_user.id)
            return {"message": "Tool associated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to associate tool")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to associate tool with agent", 
                    agent_id=agent_id, 
                    tool_id=tool_id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to associate tool: {str(e)}")


@router.get("/agents/{agent_id}/tools", response_model=List[ToolFunction])
async def get_agent_tools(
    agent_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get tools associated with an agent"""
    try:
        tools = tool_registry_service.get_agent_tools(agent_id)
        logger.info("Retrieved agent tools", 
                   agent_id=agent_id, 
                   count=len(tools), 
                   user_id=current_user.id)
        return tools
        
    except Exception as e:
        logger.error("Failed to get agent tools", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get agent tools: {str(e)}")


@router.get("/dspy/tools")
async def get_dspy_tools(
    agent_id: Optional[str] = Query(None, description="Agent ID to filter tools"),
    current_user: User = Depends(get_current_active_user)
):
    """Get tools formatted for DSPy function calling"""
    try:
        tools = tool_registry_service.get_tools_for_dspy(agent_id=agent_id)
        logger.info("Retrieved DSPy tools", 
                   agent_id=agent_id, 
                   count=len(tools), 
                   user_id=current_user.id)
        return {"tools": tools}
        
    except Exception as e:
        logger.error("Failed to get DSPy tools", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get DSPy tools: {str(e)}")


@router.get("/categories/")
async def get_tool_categories():
    """Get available tool categories"""
    return {
        "categories": [
            {"value": category.value, "label": category.value.replace("_", " ").title()}
            for category in ToolCategory
        ]
    }


@router.get("/stats/")
async def get_tool_stats(current_user: User = Depends(get_current_active_user)):
    """Get tool registry statistics"""
    try:
        all_tools = tool_registry_service.get_tools()
        
        stats = {
            "total_tools": len(all_tools),
            "active_tools": len([t for t in all_tools if t.status == ToolStatus.ACTIVE]),
            "categories": {},
            "recent_executions": len([
                log for log in tool_registry_service.execution_logs 
                if (log.timestamp.timestamp() > (time.time() - 86400))  # Last 24 hours
            ])
        }
        
        # Count by category
        for tool in all_tools:
            category = tool.category.value
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get tool stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get tool stats: {str(e)}")