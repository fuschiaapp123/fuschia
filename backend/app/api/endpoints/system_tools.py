"""
REST API endpoints for System Tools management and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import structlog
from datetime import datetime

from app.services.system_tools_service import (
    system_tools_service, 
    SystemToolCategory,
    SystemToolMetadata
)

router = APIRouter()
logger = structlog.get_logger()


class SystemToolInfo(BaseModel):
    name: str
    category: str
    description: str
    version: str
    requires_auth: bool
    async_capable: bool
    dependencies: List[str]
    initialized: bool


class SystemToolsStatus(BaseModel):
    total_tools: int
    initialized_tools: int
    failed_tools: int
    categories: Dict[str, int]
    tools: List[SystemToolInfo]
    last_updated: datetime


class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolExecutionResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float


@router.get("/system-tools/status", response_model=SystemToolsStatus)
async def get_system_tools_status():
    """Get status and information about all system tools"""
    try:
        # Initialize if not already done
        if not system_tools_service.initialized:
            await system_tools_service.initialize()
        
        tools = system_tools_service.get_all_tools()
        
        # Count tools by category and status
        category_counts = {}
        initialized_count = 0
        failed_count = 0
        tool_infos = []
        
        for tool_name, tool in tools.items():
            # Count by category
            category = tool.metadata.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count by status
            if tool.initialized:
                initialized_count += 1
            else:
                failed_count += 1
            
            # Create tool info
            tool_info = SystemToolInfo(
                name=tool.metadata.name,
                category=tool.metadata.category.value,
                description=tool.metadata.description,
                version=tool.metadata.version,
                requires_auth=tool.metadata.requires_auth,
                async_capable=tool.metadata.async_capable,
                dependencies=tool.metadata.dependencies,
                initialized=tool.initialized
            )
            tool_infos.append(tool_info)
        
        return SystemToolsStatus(
            total_tools=len(tools),
            initialized_tools=initialized_count,
            failed_tools=failed_count,
            categories=category_counts,
            tools=tool_infos,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Failed to get system tools status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system tools status: {str(e)}")


@router.get("/system-tools/list")
async def list_system_tools():
    """List all available system tools with their metadata"""
    try:
        if not system_tools_service.initialized:
            await system_tools_service.initialize()
            
        tools = system_tools_service.get_all_tools()
        
        tools_list = []
        for tool_name, tool in tools.items():
            tool_data = {
                "name": tool.metadata.name,
                "category": tool.metadata.category.value,
                "description": tool.metadata.description,
                "version": tool.metadata.version,
                "requires_auth": tool.metadata.requires_auth,
                "async_capable": tool.metadata.async_capable,
                "dependencies": tool.metadata.dependencies,
                "initialized": tool.initialized
            }
            tools_list.append(tool_data)
        
        return {
            "tools": tools_list,
            "total": len(tools_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to list system tools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list system tools: {str(e)}")


@router.get("/system-tools/categories")
async def get_system_tool_categories():
    """Get all system tool categories with tool counts"""
    try:
        if not system_tools_service.initialized:
            await system_tools_service.initialize()
            
        categories = {}
        tools = system_tools_service.get_all_tools()
        
        # Count tools in each category
        for tool in tools.values():
            category = tool.metadata.category.value
            if category not in categories:
                categories[category] = {
                    "name": category,
                    "description": f"Tools in {category.replace('_', ' ').title()} category",
                    "tool_count": 0,
                    "tools": []
                }
            
            categories[category]["tool_count"] += 1
            categories[category]["tools"].append({
                "name": tool.metadata.name,
                "description": tool.metadata.description,
                "initialized": tool.initialized
            })
        
        return {
            "categories": list(categories.values()),
            "total_categories": len(categories),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get system tool categories", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system tool categories: {str(e)}")


@router.post("/system-tools/execute", response_model=ToolExecutionResponse)
async def execute_system_tool(request: ToolExecutionRequest):
    """Execute a system tool with given parameters"""
    try:
        if not system_tools_service.initialized:
            await system_tools_service.initialize()
        
        tool = system_tools_service.get_tool(request.tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"System tool '{request.tool_name}' not found")
        
        if not tool.initialized:
            raise HTTPException(status_code=400, detail=f"System tool '{request.tool_name}' is not initialized")
        
        # Record start time
        start_time = datetime.utcnow()
        
        # Execute the tool
        try:
            result = await tool.execute(**request.parameters)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return ToolExecutionResponse(
                success=True,
                result=result,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            # Calculate execution time for failed executions
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            logger.error("System tool execution failed", 
                        tool=request.tool_name, error=str(e))
            
            return ToolExecutionResponse(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute system tool", 
                    tool=request.tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute system tool: {str(e)}")


@router.post("/system-tools/reinitialize")
async def reinitialize_system_tools():
    """Reinitialize all system tools"""
    try:
        await system_tools_service.initialize()
        
        tools = system_tools_service.get_all_tools()
        initialized_count = sum(1 for tool in tools.values() if tool.initialized)
        
        return {
            "message": "System tools reinitialized",
            "total_tools": len(tools),
            "initialized_tools": initialized_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to reinitialize system tools", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to reinitialize system tools: {str(e)}")


@router.get("/system-tools/{tool_name}")
async def get_system_tool_details(tool_name: str):
    """Get detailed information about a specific system tool"""
    try:
        if not system_tools_service.initialized:
            await system_tools_service.initialize()
            
        tool = system_tools_service.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"System tool '{tool_name}' not found")
        
        return {
            "name": tool.metadata.name,
            "category": tool.metadata.category.value,
            "description": tool.metadata.description,
            "version": tool.metadata.version,
            "requires_auth": tool.metadata.requires_auth,
            "async_capable": tool.metadata.async_capable,
            "dependencies": tool.metadata.dependencies,
            "initialized": tool.initialized,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get system tool details", tool=tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system tool details: {str(e)}")


@router.post("/system-tools/{tool_name}/test")
async def test_system_tool(tool_name: str):
    """Test a system tool with default parameters"""
    try:
        if not system_tools_service.initialized:
            await system_tools_service.initialize()
            
        tool = system_tools_service.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"System tool '{tool_name}' not found")
            
        if not tool.initialized:
            raise HTTPException(status_code=400, detail=f"System tool '{tool_name}' is not initialized")
        
        # Define test parameters for different tools
        test_params = {
            "rag_knowledge_search": {"query": "test search query", "max_results": 3},
            "mcp_service_call": {"service": "knowledge", "method": "health", "parameters": {}},
            "enhance_context": {"task_description": "test task for context enhancement"}
        }
        
        params = test_params.get(tool_name, {})
        
        # Record start time
        start_time = datetime.utcnow()
        
        try:
            result = await tool.execute(**params)
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "tool_name": tool_name,
                "test_parameters": params,
                "result": result,
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return {
                "success": False,
                "tool_name": tool_name,
                "test_parameters": params,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to test system tool", tool=tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to test system tool: {str(e)}")