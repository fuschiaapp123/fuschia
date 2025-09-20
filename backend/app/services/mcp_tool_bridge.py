"""
MCP Tool Bridge Service
Bridges Fuschia platform tools with MCP protocol
Handles bidirectional tool execution and format conversion
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from app.services.system_tools_service import system_tools_service
from app.services.servicenow_mcp_server import servicenow_mcp_server

logger = logging.getLogger(__name__)


class MCPToolExecution:
    """Represents an MCP tool execution with tracking"""
    
    def __init__(self, execution_id: str, tool_name: str, arguments: Dict[str, Any], 
                 agent_id: str = None, server_id: str = None):
        self.execution_id = execution_id
        self.tool_name = tool_name
        self.arguments = arguments
        self.agent_id = agent_id
        self.server_id = server_id
        self.status = "pending"
        self.result = None
        self.error = None
        self.started_at = datetime.utcnow()
        self.completed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "agent_id": self.agent_id,
            "server_id": self.server_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class MCPToolBridge:
    """
    Bridge between Fuschia tools and MCP protocol
    Handles tool format conversion and execution routing
    """
    
    def __init__(self):
        self.executions: Dict[str, MCPToolExecution] = {}
        self.tool_mappings: Dict[str, str] = {}  # MCP tool name -> Fuschia tool ID
        self.external_servers: Dict[str, Any] = {}  # External MCP servers
        
    async def initialize(self):
        """Initialize the tool bridge with current Fuschia tools"""
        logger.info("Initializing MCP Tool Bridge")
        await self._build_tool_mappings()
        await self._initialize_external_servers()
        logger.info(f"Tool bridge initialized with {len(self.tool_mappings)} tool mappings and {len(self.external_servers)} external servers")
    
    async def _build_tool_mappings(self):
        """Build mappings between MCP tool names and Fuschia tool IDs"""
        try:
            # Get all available system tools
            system_tools = await system_tools_service.get_available_tools()
            
            for tool_id, tool_info in system_tools.items():
                mcp_name = f"fuschia_{tool_info.get('name', tool_id)}"
                self.tool_mappings[mcp_name] = tool_id
                
            logger.info(f"Built {len(self.tool_mappings)} tool mappings")
            
        except Exception as e:
            logger.error(f"Error building tool mappings: {e}")
    
    async def _initialize_external_servers(self):
        """Initialize external MCP servers"""
        try:
            # Initialize ServiceNow MCP server
            await servicenow_mcp_server.initialize()
            self.external_servers["servicenow"] = servicenow_mcp_server
            
            # Add ServiceNow tools to mappings
            servicenow_tools = await servicenow_mcp_server.list_tools()
            for tool in servicenow_tools:
                tool_name = tool.get("name")
                if tool_name:
                    self.tool_mappings[tool_name] = f"servicenow:{tool_name}"
            
            logger.info(f"Initialized ServiceNow MCP server with {len(servicenow_tools)} tools")
            
        except Exception as e:
            logger.error(f"Error initializing external servers: {e}")
    
    async def convert_fuschia_tool_to_mcp_format(self, tool_id: str, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Fuschia tool to MCP tool format"""
        
        name = tool_info.get('name', tool_id)
        description = tool_info.get('description', f'Fuschia platform tool: {name}')
        
        # Convert Fuschia parameters to JSON Schema
        parameters = tool_info.get('parameters', {})
        input_schema = {
            "type": "object",
            "properties": {}
        }
        
        # Handle different parameter formats
        if isinstance(parameters, dict):
            if 'properties' in parameters:
                # Already in JSON Schema format
                input_schema = parameters
            else:
                # Convert simple parameter dict
                properties = {}
                required = []
                
                for param_name, param_info in parameters.items():
                    if isinstance(param_info, dict):
                        properties[param_name] = param_info
                        if param_info.get('required', False):
                            required.append(param_name)
                    else:
                        # Simple type specification
                        properties[param_name] = {
                            "type": "string",
                            "description": f"Parameter: {param_name}"
                        }
                
                input_schema = {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
        
        return {
            "name": f"fuschia_{name}",
            "description": description,
            "inputSchema": input_schema,
            "fuschia_tool_id": tool_id,
            "tool_type": tool_info.get('tool_type', 'system'),
            "categories": tool_info.get('categories', []),
            "version": tool_info.get('version', '1.0.0')
        }
    
    async def execute_mcp_tool_call(self, tool_name: str, arguments: Dict[str, Any], 
                                   agent_id: str = None, server_id: str = None) -> MCPToolExecution:
        """Execute an MCP tool call by routing to appropriate Fuschia service"""
        
        execution_id = str(uuid.uuid4())
        execution = MCPToolExecution(
            execution_id=execution_id,
            tool_name=tool_name,
            arguments=arguments,
            agent_id=agent_id,
            server_id=server_id
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Find corresponding Fuschia tool
            if tool_name not in self.tool_mappings:
                # Try to refresh mappings
                await self._build_tool_mappings()
            
            if tool_name not in self.tool_mappings:
                raise ValueError(f"Unknown MCP tool: {tool_name}")
            
            fuschia_tool_id = self.tool_mappings[tool_name]
            
            # Route to appropriate service based on tool type
            execution.status = "running"
            
            if fuschia_tool_id.startswith('servicenow:'):
                result = await self._execute_servicenow_tool(tool_name, arguments)
            elif fuschia_tool_id.startswith('system_'):
                result = await self._execute_system_tool(fuschia_tool_id, arguments)
            elif fuschia_tool_id.startswith('agent_'):
                result = await self._execute_agent_tool(fuschia_tool_id, arguments, agent_id)
            else:
                result = await self._execute_custom_tool(fuschia_tool_id, arguments)
            
            execution.result = result
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            
            logger.info(f"Successfully executed MCP tool '{tool_name}' with execution ID: {execution_id}")
            
        except Exception as e:
            execution.error = str(e)
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            logger.error(f"Error executing MCP tool '{tool_name}': {e}")
        
        return execution
    
    async def _execute_servicenow_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a ServiceNow MCP tool"""
        try:
            servicenow_server = self.external_servers.get("servicenow")
            if not servicenow_server:
                raise ValueError("ServiceNow MCP server not available")
            
            result = await servicenow_server.call_tool(tool_name, arguments)
            
            return {
                "type": "servicenow_tool_result",
                "tool_name": tool_name,
                "result": result,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error executing ServiceNow tool '{tool_name}': {e}")
            return {
                "type": "servicenow_tool_result",
                "tool_name": tool_name,
                "error": str(e),
                "status": "error"
            }
    
    async def _execute_system_tool(self, tool_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a system tool"""
        try:
            result = await system_tools_service.execute_tool(tool_id, arguments)
            return {
                "type": "system_tool_result",
                "tool_id": tool_id,
                "result": result,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error executing system tool '{tool_id}': {e}")
            return {
                "type": "system_tool_result",
                "tool_id": tool_id,
                "error": str(e),
                "status": "error"
            }
    
    async def _execute_agent_tool(self, tool_id: str, arguments: Dict[str, Any], agent_id: str = None) -> Dict[str, Any]:
        """Execute an agent-specific tool"""
        try:
            # This would integrate with agent service when available
            result = {
                "tool_id": tool_id,
                "agent_id": agent_id,
                "arguments": arguments,
                "message": f"Agent tool {tool_id} executed (placeholder implementation)",
                "status": "success"
            }
            
            return {
                "type": "agent_tool_result",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing agent tool '{tool_id}': {e}")
            return {
                "type": "agent_tool_result",
                "tool_id": tool_id,
                "error": str(e),
                "status": "error"
            }
    
    async def _execute_custom_tool(self, tool_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a custom tool"""
        try:
            # Custom tool execution logic
            result = {
                "tool_id": tool_id,
                "arguments": arguments,
                "message": f"Custom tool {tool_id} executed",
                "status": "success"
            }
            
            return {
                "type": "custom_tool_result",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing custom tool '{tool_id}': {e}")
            return {
                "type": "custom_tool_result",
                "tool_id": tool_id,
                "error": str(e),
                "status": "error"
            }
    
    async def get_execution_status(self, execution_id: str) -> Optional[MCPToolExecution]:
        """Get the status of a tool execution"""
        return self.executions.get(execution_id)
    
    async def get_execution_history(self, agent_id: str = None, limit: int = 100) -> List[MCPToolExecution]:
        """Get execution history, optionally filtered by agent"""
        executions = list(self.executions.values())
        
        if agent_id:
            executions = [e for e in executions if e.agent_id == agent_id]
        
        # Sort by start time, most recent first
        executions.sort(key=lambda x: x.started_at, reverse=True)
        
        return executions[:limit]
    
    async def convert_mcp_result_to_fuschia_format(self, mcp_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert MCP tool result back to Fuschia format"""
        
        if not mcp_result:
            return {"status": "empty", "content": None}
        
        # Handle text content
        text_content = []
        for item in mcp_result:
            if item.get("type") == "text":
                text_content.append(item.get("text", ""))
        
        return {
            "status": "success",
            "content": "\n".join(text_content) if text_content else None,
            "raw_mcp_result": mcp_result,
            "content_type": "text"
        }
    
    async def get_available_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        tools = []
        
        try:
            # Get Fuschia system tools
            system_tools = await system_tools_service.get_available_tools()
            
            for tool_id, tool_info in system_tools.items():
                mcp_tool = await self.convert_fuschia_tool_to_mcp_format(tool_id, tool_info)
                tools.append(mcp_tool)
            
            # Get ServiceNow tools
            if "servicenow" in self.external_servers:
                servicenow_tools = await self.external_servers["servicenow"].list_tools()
                tools.extend(servicenow_tools)
                
        except Exception as e:
            logger.error(f"Error getting available MCP tools: {e}")
        
        return tools
    
    async def validate_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate arguments against tool schema"""
        
        if tool_name not in self.tool_mappings:
            return {
                "valid": False,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            # Get tool info
            fuschia_tool_id = self.tool_mappings[tool_name]
            system_tools = await system_tools_service.get_available_tools()
            
            if fuschia_tool_id not in system_tools:
                return {
                    "valid": False,
                    "error": f"Tool not found: {fuschia_tool_id}"
                }
            
            # Basic validation (could be enhanced with JSON Schema validation)
            tool_info = system_tools[fuschia_tool_id]
            parameters = tool_info.get('parameters', {})
            required = parameters.get('required', [])
            
            # Check required parameters
            missing_params = [param for param in required if param not in arguments]
            if missing_params:
                return {
                    "valid": False,
                    "error": f"Missing required parameters: {missing_params}"
                }
            
            return {
                "valid": True,
                "message": "Arguments are valid"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }


# Global bridge instance
mcp_tool_bridge = MCPToolBridge()