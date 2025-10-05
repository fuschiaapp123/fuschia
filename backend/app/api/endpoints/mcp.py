"""
MCP (Model Context Protocol) API Endpoints
Provides REST API interface for MCP server management and tool execution
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from app.services.mcp_server_service import mcp_server_manager
from app.services.mcp_tool_bridge import mcp_tool_bridge
from app.services.servicenow_mcp_server import servicenow_mcp_server
from app.services.gmail_mcp_server import gmail_mcp_server
from app.services.hcmpro_mcp_server import hcmpro_mcp_server
from app.auth.auth import get_current_user
from app.models.user import User
from app.db.postgres import (
    AsyncSessionLocal, MCPServerTable, MCPToolTable, MCPResourceTable, 
    MCPToolExecutionTable
)
from sqlalchemy import select, and_, desc
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for API requests/responses
class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    command: str = Field(..., min_length=1)
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    capabilities: Dict[str, bool] = Field(default_factory=lambda: {
        "tools": True,
        "resources": True, 
        "prompts": False
    })
    auto_start: bool = Field(default=False)


class MCPServerResponse(BaseModel):
    """Response model for MCP server information"""
    id: str
    name: str
    description: Optional[str]
    command: str
    args: List[str]
    capabilities: Dict[str, Any]
    status: str
    auto_start: bool
    process_id: Optional[str]
    last_error: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class MCPToolResponse(BaseModel):
    """Response model for MCP tool information"""
    id: str
    server_id: str
    tool_name: str
    description: Optional[str]
    input_schema: Dict[str, Any]
    fuschia_tool_id: Optional[str]
    is_active: bool
    categories: List[str]
    version: str
    created_at: datetime


class MCPToolExecutionRequest(BaseModel):
    """Request model for MCP tool execution"""
    tool_name: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)


class MCPToolExecutionResponse(BaseModel):
    """Response model for MCP tool execution"""
    execution_id: str
    tool_name: str
    status: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]


class MCPResourceResponse(BaseModel):
    """Response model for MCP resource information"""
    id: str
    server_id: str
    uri: str
    name: str
    description: Optional[str]
    mime_type: Optional[str]
    is_active: bool
    last_accessed: Optional[datetime]
    created_at: datetime


# MCP Server Management Endpoints

@router.post("/servers", response_model=MCPServerResponse)
async def create_mcp_server(
    server_config: MCPServerConfig,
    current_user: User = Depends(get_current_user)
):
    """Create a new MCP server configuration"""
    try:
        server_id = server_config.id or str(uuid.uuid4())
        
        async with AsyncSessionLocal() as session:
            # Check if server with same ID or name already exists
            existing = await session.execute(
                select(MCPServerTable).where(
                    (MCPServerTable.id == server_id) | 
                    (MCPServerTable.name == server_config.name)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400, 
                    detail=f"MCP server with ID '{server_id}' or name '{server_config.name}' already exists"
                )
            
            # Create new server record
            db_server = MCPServerTable(
                id=server_id,
                name=server_config.name,
                description=server_config.description,
                command=server_config.command,
                args=server_config.args,
                env=server_config.env,
                capabilities=server_config.capabilities,
                auto_start=server_config.auto_start,
                status="inactive",
                created_by=current_user.id
            )
            
            session.add(db_server)
            await session.commit()
            await session.refresh(db_server)
            
            return MCPServerResponse(
                id=db_server.id,
                name=db_server.name,
                description=db_server.description,
                command=db_server.command,
                args=db_server.args,
                capabilities=db_server.capabilities,
                status=db_server.status,
                auto_start=db_server.auto_start,
                process_id=db_server.process_id,
                last_error=db_server.last_error,
                created_by=db_server.created_by,
                created_at=db_server.created_at,
                updated_at=db_server.updated_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create MCP server: {str(e)}")


@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List all MCP servers"""
    try:
        async with AsyncSessionLocal() as session:
            query = select(MCPServerTable)
            
            if status:
                query = query.where(MCPServerTable.status == status)
            
            query = query.order_by(desc(MCPServerTable.created_at))
            
            result = await session.execute(query)
            servers = result.scalars().all()
            
            return [
                MCPServerResponse(
                    id=server.id,
                    name=server.name,
                    description=server.description,
                    command=server.command,
                    args=server.args,
                    capabilities=server.capabilities,
                    status=server.status,
                    auto_start=server.auto_start,
                    process_id=server.process_id,
                    last_error=server.last_error,
                    created_by=server.created_by,
                    created_at=server.created_at,
                    updated_at=server.updated_at
                )
                for server in servers
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list MCP servers: {str(e)}")


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific MCP server"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(MCPServerTable).where(MCPServerTable.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
            
            return MCPServerResponse(
                id=server.id,
                name=server.name,
                description=server.description,
                command=server.command,
                args=server.args,
                capabilities=server.capabilities,
                status=server.status,
                auto_start=server.auto_start,
                process_id=server.process_id,
                last_error=server.last_error,
                created_by=server.created_by,
                created_at=server.created_at,
                updated_at=server.updated_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MCP server: {str(e)}")


@router.post("/servers/{server_id}/start")
async def start_mcp_server(
    server_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Start an MCP server"""
    try:
        # Start the server using the manager
        success = await mcp_server_manager.start_server(server_id)
        
        if success:
            # Update database status
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MCPServerTable).where(MCPServerTable.id == server_id)
                )
                server = result.scalar_one_or_none()
                
                if server:
                    server.status = "active"
                    server.last_error = None
                    flag_modified(server, 'status')
                    await session.commit()
            
            return {"status": "success", "message": f"MCP server '{server_id}' started successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to start MCP server '{server_id}'")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting MCP server: {str(e)}")


@router.post("/servers/{server_id}/stop")
async def stop_mcp_server(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stop an MCP server"""
    try:
        success = await mcp_server_manager.stop_server(server_id)
        
        if success:
            # Update database status
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MCPServerTable).where(MCPServerTable.id == server_id)
                )
                server = result.scalar_one_or_none()
                
                if server:
                    server.status = "inactive"
                    server.process_id = None
                    flag_modified(server, 'status')
                    await session.commit()
            
            return {"status": "success", "message": f"MCP server '{server_id}' stopped successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to stop MCP server '{server_id}'")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping MCP server: {str(e)}")


@router.delete("/servers/{server_id}")
async def delete_mcp_server(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an MCP server configuration"""
    try:
        async with AsyncSessionLocal() as session:
            # Stop server if running
            await mcp_server_manager.stop_server(server_id)
            
            # Delete from database
            result = await session.execute(
                select(MCPServerTable).where(MCPServerTable.id == server_id)
            )
            server = result.scalar_one_or_none()
            
            if not server:
                raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
            
            await session.delete(server)
            await session.commit()
            
            return {"status": "success", "message": f"MCP server '{server_id}' deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete MCP server: {str(e)}")


# MCP Tools Endpoints

@router.get("/servers/{server_id}/tools", response_model=List[MCPToolResponse])
async def list_mcp_tools(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """List tools available from an MCP server"""
    try:
        # Get server instance and list tools
        server = await mcp_server_manager.get_server(server_id)
        tools = await server.list_tools()
        
        # Convert to response format
        tool_responses = []
        for tool in tools:
            tool_responses.append(MCPToolResponse(
                id=f"{server_id}_{tool['name']}",
                server_id=server_id,
                tool_name=tool['name'],
                description=tool.get('description'),
                input_schema=tool.get('inputSchema', {}),
                fuschia_tool_id=None,  # Will be populated from database if exists
                is_active=True,
                categories=[],
                version="1.0.0",
                created_at=datetime.utcnow()
            ))
        
        return tool_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list MCP tools: {str(e)}")


@router.post("/tools/execute", response_model=MCPToolExecutionResponse)
async def execute_mcp_tool(
    execution_request: MCPToolExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute an MCP tool"""
    try:
        # Initialize tool bridge if needed
        await mcp_tool_bridge.initialize()
        
        # Execute the tool
        execution = await mcp_tool_bridge.execute_mcp_tool_call(
            tool_name=execution_request.tool_name,
            arguments=execution_request.arguments,
            agent_id=execution_request.agent_id
        )
        
        # Store execution in database
        async with AsyncSessionLocal() as session:
            db_execution = MCPToolExecutionTable(
                id=execution.execution_id,
                tool_id=f"mcp_{execution_request.tool_name}",  # Temporary tool ID
                server_id="fuschia-platform",  # Default server
                agent_id=execution_request.agent_id,
                user_id=current_user.id,
                tool_name=execution_request.tool_name,
                arguments=execution_request.arguments,
                result=execution.result,
                error_message=execution.error,
                status=execution.status,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                workflow_execution_id=execution_request.workflow_execution_id,
                context_data=execution_request.context_data
            )
            
            # Calculate execution time if completed
            if execution.completed_at and execution.started_at:
                execution_time = (execution.completed_at - execution.started_at).total_seconds() * 1000
                db_execution.execution_time_ms = int(execution_time)
            
            session.add(db_execution)
            await session.commit()
        
        return MCPToolExecutionResponse(
            execution_id=execution.execution_id,
            tool_name=execution.tool_name,
            status=execution.status,
            result=execution.result,
            error_message=execution.error,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            execution_time_ms=db_execution.execution_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute MCP tool: {str(e)}")


@router.get("/tools/executions", response_model=List[MCPToolExecutionResponse])
async def list_tool_executions(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """List MCP tool executions"""
    try:
        async with AsyncSessionLocal() as session:
            query = select(MCPToolExecutionTable).where(
                MCPToolExecutionTable.user_id == current_user.id
            )
            
            if agent_id:
                query = query.where(MCPToolExecutionTable.agent_id == agent_id)
            
            if status:
                query = query.where(MCPToolExecutionTable.status == status)
            
            query = query.order_by(desc(MCPToolExecutionTable.started_at)).limit(limit)
            
            result = await session.execute(query)
            executions = result.scalars().all()
            
            return [
                MCPToolExecutionResponse(
                    execution_id=exec.id,
                    tool_name=exec.tool_name,
                    status=exec.status,
                    result=exec.result,
                    error_message=exec.error_message,
                    started_at=exec.started_at,
                    completed_at=exec.completed_at,
                    execution_time_ms=exec.execution_time_ms
                )
                for exec in executions
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tool executions: {str(e)}")


@router.get("/tools/executions/{execution_id}", response_model=MCPToolExecutionResponse)
async def get_tool_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific tool execution"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(MCPToolExecutionTable).where(
                    and_(
                        MCPToolExecutionTable.id == execution_id,
                        MCPToolExecutionTable.user_id == current_user.id
                    )
                )
            )
            execution = result.scalar_one_or_none()
            
            if not execution:
                raise HTTPException(status_code=404, detail=f"Tool execution '{execution_id}' not found")
            
            return MCPToolExecutionResponse(
                execution_id=execution.id,
                tool_name=execution.tool_name,
                status=execution.status,
                result=execution.result,
                error_message=execution.error_message,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                execution_time_ms=execution.execution_time_ms
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tool execution: {str(e)}")


# MCP Resources Endpoints

@router.get("/servers/{server_id}/resources", response_model=List[MCPResourceResponse])
async def list_mcp_resources(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """List resources available from an MCP server"""
    try:
        server = await mcp_server_manager.get_server(server_id)
        resources = await server.list_resources()
        
        # Convert to response format
        resource_responses = []
        for resource in resources:
            resource_responses.append(MCPResourceResponse(
                id=f"{server_id}_{hash(resource['uri'])}",
                server_id=server_id,
                uri=resource['uri'],
                name=resource['name'],
                description=resource.get('description'),
                mime_type=resource.get('mimeType'),
                is_active=True,
                last_accessed=None,
                created_at=datetime.utcnow()
            ))
        
        return resource_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list MCP resources: {str(e)}")


@router.get("/servers/{server_id}/resources/{resource_uri:path}")
async def read_mcp_resource(
    server_id: str,
    resource_uri: str,
    current_user: User = Depends(get_current_user)
):
    """Read content from an MCP resource"""
    try:
        server = await mcp_server_manager.get_server(server_id)
        content = await server.read_resource(resource_uri)
        
        return {
            "server_id": server_id,
            "resource_uri": resource_uri,
            "content": content,
            "accessed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read MCP resource: {str(e)}")


# Status and Health Endpoints

@router.get("/status")
async def get_mcp_status(current_user: User = Depends(get_current_user)):
    """Get overall MCP system status"""
    try:
        servers = await mcp_server_manager.list_servers()
        
        active_servers = len([s for s in servers if s.get('is_running', False)])
        total_servers = len(servers)
        
        # Get tool execution statistics
        async with AsyncSessionLocal() as session:
            # Count recent executions
            recent_executions = await session.execute(
                select(MCPToolExecutionTable).where(
                    MCPToolExecutionTable.started_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                )
            )
            daily_executions = len(recent_executions.scalars().all())
        
        return {
            "status": "active" if active_servers > 0 else "inactive",
            "servers": {
                "total": total_servers,
                "active": active_servers,
                "inactive": total_servers - active_servers
            },
            "executions": {
                "today": daily_executions
            },
            "bridge_status": "active",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MCP status: {str(e)}")


@router.post("/servers/predefined")
async def register_predefined_servers(
    current_user: User = Depends(get_current_user)
):
    """Register predefined MCP servers (ServiceNow, filesystem, etc.)"""
    try:
        registered_servers = []
        
        # Register ServiceNow MCP server
        servicenow_server_config = {
            "id": "servicenow-api",
            "name": "ServiceNow API Server", 
            "description": "ServiceNow API access through MCP protocol",
            "command": "internal",  # Internal server, not external process
            "args": [],
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False
            },
            "auto_start": True,
            "status": "active"
        }
        
        async with AsyncSessionLocal() as session:
            # Check if ServiceNow server already exists
            existing = await session.execute(
                select(MCPServerTable).where(MCPServerTable.id == "servicenow-api")
            )
            if not existing.scalar_one_or_none():
                # Create ServiceNow server entry
                servicenow_db_server = MCPServerTable(
                    id="servicenow-api",
                    name="ServiceNow API Server",
                    description="ServiceNow API access through MCP protocol",
                    command="internal",
                    args=[],
                    capabilities={
                        "tools": True,
                        "resources": True,
                        "prompts": False
                    },
                    status="active",
                    auto_start=True,
                    created_by=current_user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(servicenow_db_server)
                
                # Initialize ServiceNow server
                await servicenow_mcp_server.initialize()
                
                # Add ServiceNow tools to database
                servicenow_tools = await servicenow_mcp_server.list_tools()
                for tool in servicenow_tools:
                    tool_db_entry = MCPToolTable(
                        id=str(uuid.uuid4()),
                        server_id="servicenow-api",
                        tool_name=tool.get("name"),
                        description=tool.get("description"),
                        input_schema=tool.get("inputSchema", {}),
                        is_active=True,
                        categories=["servicenow", "api"],
                        version="1.0.0",
                        created_at=datetime.utcnow()
                    )
                    session.add(tool_db_entry)
                
                # Add ServiceNow resources to database
                servicenow_resources = await servicenow_mcp_server.list_resources()
                for resource in servicenow_resources:
                    resource_db_entry = MCPResourceTable(
                        id=str(uuid.uuid4()),
                        server_id="servicenow-api",
                        uri=resource.get("uri"),
                        name=resource.get("name"),
                        description=resource.get("description"),
                        mime_type=resource.get("mimeType", "application/json"),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    session.add(resource_db_entry)
                
                await session.commit()
                registered_servers.append(servicenow_server_config)

            # Register Gmail MCP server
            gmail_server_config = {
                "id": "gmail-api",
                "name": "Gmail API Server",
                "description": "Gmail API access through MCP protocol",
                "command": "internal",
                "args": [],
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "prompts": False
                },
                "auto_start": True,
                "status": "active"
            }

            # Check if Gmail server already exists
            existing_gmail = await session.execute(
                select(MCPServerTable).where(MCPServerTable.id == "gmail-api")
            )
            if not existing_gmail.scalar_one_or_none():
                # Create Gmail server entry
                gmail_db_server = MCPServerTable(
                    id="gmail-api",
                    name="Gmail API Server",
                    description="Gmail API access through MCP protocol",
                    command="internal",
                    args=[],
                    capabilities={
                        "tools": True,
                        "resources": True,
                        "prompts": False
                    },
                    status="active",
                    auto_start=True,
                    created_by=current_user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(gmail_db_server)

                # Initialize Gmail server
                await gmail_mcp_server.initialize()

                # Add Gmail tools to database
                gmail_tools = await gmail_mcp_server.list_tools()
                for tool in gmail_tools:
                    tool_db_entry = MCPToolTable(
                        id=str(uuid.uuid4()),
                        server_id="gmail-api",
                        tool_name=tool.get("name"),
                        description=tool.get("description"),
                        input_schema=tool.get("inputSchema", {}),
                        is_active=True,
                        categories=["gmail", "email", "api"],
                        version="1.0.0",
                        created_at=datetime.utcnow()
                    )
                    session.add(tool_db_entry)

                # Add Gmail resources to database
                gmail_resources = await gmail_mcp_server.list_resources()
                for resource in gmail_resources:
                    resource_db_entry = MCPResourceTable(
                        id=str(uuid.uuid4()),
                        server_id="gmail-api",
                        uri=resource.get("uri"),
                        name=resource.get("name"),
                        description=resource.get("description"),
                        mime_type=resource.get("mimeType", "application/json"),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    session.add(resource_db_entry)

                await session.commit()
                registered_servers.append(gmail_server_config)

            # Register HCM Pro MCP server
            hcmpro_server_config = {
                "id": "hcmpro-api",
                "name": "HCM Pro Job Offer API Server",
                "description": "HCM Pro Job Offer API access through MCP protocol",
                "command": "internal",
                "args": [],
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "prompts": False
                },
                "auto_start": True,
                "status": "active"
            }

            # Check if HCM Pro server already exists
            existing_hcmpro = await session.execute(
                select(MCPServerTable).where(MCPServerTable.id == "hcmpro-api")
            )
            if not existing_hcmpro.scalar_one_or_none():
                # Create HCM Pro server entry
                hcmpro_db_server = MCPServerTable(
                    id="hcmpro-api",
                    name="HCM Pro Job Offer API Server",
                    description="HCM Pro Job Offer API access through MCP protocol",
                    command="internal",
                    args=[],
                    capabilities={
                        "tools": True,
                        "resources": True,
                        "prompts": False
                    },
                    status="active",
                    auto_start=True,
                    created_by=current_user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(hcmpro_db_server)

                # Initialize HCM Pro server
                await hcmpro_mcp_server.initialize()

                # Add HCM Pro tools to database
                hcmpro_tools = await hcmpro_mcp_server.list_tools()
                for tool in hcmpro_tools:
                    tool_db_entry = MCPToolTable(
                        id=str(uuid.uuid4()),
                        server_id="hcmpro-api",
                        tool_name=tool.get("name"),
                        description=tool.get("description"),
                        input_schema=tool.get("inputSchema", {}),
                        is_active=True,
                        categories=["hcmpro", "hr", "job-offers", "api"],
                        version="1.0.0",
                        created_at=datetime.utcnow()
                    )
                    session.add(tool_db_entry)

                # Add HCM Pro resources to database
                hcmpro_resources = await hcmpro_mcp_server.list_resources()
                for resource in hcmpro_resources:
                    resource_db_entry = MCPResourceTable(
                        id=str(uuid.uuid4()),
                        server_id="hcmpro-api",
                        uri=resource.get("uri"),
                        name=resource.get("name"),
                        description=resource.get("description"),
                        mime_type=resource.get("mimeType", "application/json"),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    session.add(resource_db_entry)

                await session.commit()
                registered_servers.append(hcmpro_server_config)

        # Initialize the tool bridge to include all tools
        await mcp_tool_bridge.initialize()

        return {
            "message": f"Successfully registered {len(registered_servers)} predefined MCP servers",
            "servers": registered_servers,
            "servicenow_tools_count": len(servicenow_tools) if 'servicenow_tools' in locals() else 0,
            "servicenow_resources_count": len(servicenow_resources) if 'servicenow_resources' in locals() else 0,
            "gmail_tools_count": len(gmail_tools) if 'gmail_tools' in locals() else 0,
            "gmail_resources_count": len(gmail_resources) if 'gmail_resources' in locals() else 0,
            "hcmpro_tools_count": len(hcmpro_tools) if 'hcmpro_tools' in locals() else 0,
            "hcmpro_resources_count": len(hcmpro_resources) if 'hcmpro_resources' in locals() else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register predefined servers: {str(e)}")


@router.get("/tools/all", response_model=List[dict])
async def get_all_mcp_tools_for_selection(
    current_user: User = Depends(get_current_user)
):
    """Get all MCP tools from all servers formatted for tool selection interface"""
    try:
        all_mcp_tools = []

        # Directly test known working servers to avoid manager issues
        known_servers = [
            ("gmail-api", gmail_mcp_server, "gmail", ["mcp", "gmail", "email"]),
            ("hcmpro-api", hcmpro_mcp_server, "hcmpro", ["mcp", "hcmpro", "hr", "job-offers"]),
            ("servicenow-api", servicenow_mcp_server, "servicenow", ["mcp", "servicenow", "itsm"])
        ]

        for server_id, server, category_suffix, tags in known_servers:
            try:
                # Initialize server if not running
                if not server.is_running:
                    await server.initialize()

                # Skip if still not running after initialization
                if not server.is_running:
                    continue

                tools = await server.list_tools()
                logger.info(f"Got {len(tools)} tools from {server_id}")

                # Convert to format compatible with tool selector
                for tool in tools:
                    category = f"mcp_{category_suffix}"

                    # Use the original tool name from MCP server, not the constructed ID
                    original_tool_name = tool['name']

                    formatted_tool = {
                        "id": f"mcp_{server_id}_{original_tool_name}",
                        "name": original_tool_name,  # ✅ FIX: Use original tool name
                        "description": tool.get('description', ''),
                        "category": category,
                        "status": "active",
                        "parameters": [],  # MCP tools have dynamic parameters via inputSchema
                        "tags": tags,
                        "tool_type": "mcp",
                        "version": "1.0.0",
                        "requires_auth": True,
                        "server_id": server_id,
                        "input_schema": tool.get('inputSchema', {})
                    }
                    all_mcp_tools.append(formatted_tool)

            except Exception as e:
                logger.warning(f"Failed to get tools from MCP server '{server_id}': {e}")
                continue

        logger.info("Retrieved MCP tools for selection",
                   count=len(all_mcp_tools),
                   user_id=current_user.id)
        return all_mcp_tools

    except Exception as e:
        logger.error("Failed to get MCP tools for selection", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get MCP tools: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for MCP services"""
    try:
        # Test tool bridge
        await mcp_tool_bridge.initialize()
        
        # Test default server
        server_info = mcp_server_manager.default_server.get_server_info()
        
        # Test ServiceNow server
        servicenow_status = "active" if servicenow_mcp_server.is_running else "inactive"

        # Test Gmail server
        gmail_status = "active" if gmail_mcp_server.is_running else "inactive"

        # Test HCM Pro server
        hcmpro_status = "active" if hcmpro_mcp_server.is_running else "inactive"

        return {
            "status": "healthy",
            "components": {
                "mcp_server_manager": "healthy",
                "mcp_tool_bridge": "healthy",
                "default_server": "healthy" if server_info.get('is_running') else "inactive",
                "servicenow_server": servicenow_status,
                "gmail_server": gmail_status,
                "hcmpro_server": hcmpro_status
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }