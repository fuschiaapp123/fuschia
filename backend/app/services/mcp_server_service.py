"""
MCP (Model Context Protocol) Server Service for Fuschia Platform
Provides MCP server functionality to expose Fuschia tools and resources to MCP clients
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from app.services.system_tools_service import system_tools_service
from app.services.tool_registry_service import tool_registry_service

logger = logging.getLogger(__name__)


class MCPTool:
    """Represents an MCP tool with standardized interface"""
    
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], 
                 fuschia_tool_id: str = None, server_id: str = None):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.fuschia_tool_id = fuschia_tool_id
        self.server_id = server_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class MCPResource:
    """Represents an MCP resource"""
    
    def __init__(self, uri: str, name: str, description: str = None, mime_type: str = None):
        self.uri = uri
        self.name = name
        self.description = description
        self.mime_type = mime_type
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "uri": self.uri,
            "name": self.name
        }
        if self.description:
            result["description"] = self.description
        if self.mime_type:
            result["mimeType"] = self.mime_type
        return result


class FuschiaMCPServer:
    """
    Fuschia MCP Server implementation
    Exposes Fuschia platform capabilities via MCP protocol
    """
    
    def __init__(self, server_id: str = "fuschia-platform"):
        self.server_id = server_id
        self.name = "Fuschia Intelligent Automation Platform"
        self.version = "1.0.0"
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.is_running = False
        
    async def initialize(self):
        """Initialize the MCP server with Fuschia tools and resources"""
        logger.info(f"Initializing Fuschia MCP Server: {self.server_id}")
        
        # Load Fuschia tools into MCP format
        await self._load_fuschia_tools()
        
        # Load Fuschia resources
        await self._load_fuschia_resources()
        
        self.is_running = True
        logger.info(f"MCP Server initialized with {len(self.tools)} tools and {len(self.resources)} resources")
    
    async def _load_fuschia_tools(self):
        """Load Fuschia system tools and convert to MCP format"""
        try:
            # Get system tools
            system_tools = await system_tools_service.get_available_tools()
            
            for tool_id, tool_info in system_tools.items():
                mcp_tool = self._convert_fuschia_tool_to_mcp(tool_id, tool_info)
                self.tools[mcp_tool.name] = mcp_tool
                
            logger.info(f"Loaded {len(system_tools)} system tools into MCP server")
            
        except Exception as e:
            logger.error(f"Error loading Fuschia tools: {e}")
    
    def _convert_fuschia_tool_to_mcp(self, tool_id: str, tool_info: Dict[str, Any]) -> MCPTool:
        """Convert Fuschia tool format to MCP Tool format"""
        
        # Extract tool information
        name = tool_info.get('name', tool_id)
        description = tool_info.get('description', f'Fuschia tool: {name}')
        
        # Convert parameters to JSON Schema format
        parameters = tool_info.get('parameters', {})
        input_schema = {
            "type": "object",
            "properties": parameters.get('properties', {}),
            "required": parameters.get('required', [])
        }
        
        return MCPTool(
            name=f"fuschia_{name}",
            description=description,
            input_schema=input_schema,
            fuschia_tool_id=tool_id
        )
    
    async def _load_fuschia_resources(self):
        """Load Fuschia knowledge resources"""
        try:
            # Add knowledge graph as a resource
            knowledge_resource = MCPResource(
                uri="fuschia://knowledge/graph",
                name="Knowledge Graph",
                description="Fuschia platform knowledge graph with entities and relationships",
                mime_type="application/json"
            )
            self.resources[knowledge_resource.uri] = knowledge_resource
            
            # Add agent templates as resources
            templates_resource = MCPResource(
                uri="fuschia://templates/agents",
                name="Agent Templates",
                description="Available agent templates and configurations",
                mime_type="application/json"
            )
            self.resources[templates_resource.uri] = templates_resource
            
            # Add workflow templates as resources
            workflows_resource = MCPResource(
                uri="fuschia://templates/workflows",
                name="Workflow Templates",
                description="Available workflow templates and configurations",
                mime_type="application/json"
            )
            self.resources[workflows_resource.uri] = workflows_resource
            
            logger.info(f"Loaded {len(self.resources)} resources into MCP server")
            
        except Exception as e:
            logger.error(f"Error loading Fuschia resources: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Handle MCP list_tools request"""
        if not self.is_running:
            await self.initialize()
        
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle MCP call_tool request"""
        if not self.is_running:
            await self.initialize()
        
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        
        tool = self.tools[name]
        
        try:
            # Execute the Fuschia tool
            result = await self._execute_fuschia_tool(tool, arguments)
            
            # Return result in MCP format
            return [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
            
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return [{
                "type": "text", 
                "text": f"Error executing tool: {str(e)}"
            }]
    
    async def _execute_fuschia_tool(self, tool: MCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Fuschia tool and return the result"""
        
        if tool.fuschia_tool_id:
            # Execute system tool
            if tool.fuschia_tool_id.startswith('system_'):
                result = await system_tools_service.execute_tool(
                    tool.fuschia_tool_id, 
                    arguments
                )
                return {
                    "tool_id": tool.fuschia_tool_id,
                    "result": result,
                    "status": "success",
                    "executed_at": datetime.utcnow().isoformat()
                }
        
        # Default execution
        return {
            "tool_id": tool.fuschia_tool_id,
            "arguments": arguments,
            "status": "executed",
            "message": f"Tool {tool.name} executed with arguments",
            "executed_at": datetime.utcnow().isoformat()
        }
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """Handle MCP list_resources request"""
        if not self.is_running:
            await self.initialize()
        
        return [resource.to_dict() for resource in self.resources.values()]
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Handle MCP read_resource request"""
        if not self.is_running:
            await self.initialize()
        
        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' not found")
        
        resource = self.resources[uri]
        
        try:
            # Get resource content based on URI
            content = await self._get_resource_content(uri)
            
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": resource.mime_type or "application/json",
                    "text": json.dumps(content, indent=2)
                }]
            }
            
        except Exception as e:
            logger.error(f"Error reading resource '{uri}': {e}")
            raise ValueError(f"Error reading resource: {str(e)}")
    
    async def _get_resource_content(self, uri: str) -> Dict[str, Any]:
        """Get content for a specific resource URI"""
        
        if uri == "fuschia://knowledge/graph":
            # Return knowledge graph summary
            return {
                "type": "knowledge_graph",
                "nodes": [],  # Would be populated from Neo4j
                "edges": [],
                "metadata": {
                    "total_nodes": 0,
                    "total_edges": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
        
        elif uri == "fuschia://templates/agents":
            # Return agent templates summary
            return {
                "type": "agent_templates",
                "templates": [],  # Would be populated from database
                "categories": [],
                "total_count": 0
            }
        
        elif uri == "fuschia://templates/workflows":
            # Return workflow templates summary
            return {
                "type": "workflow_templates", 
                "templates": [],  # Would be populated from database
                "categories": [],
                "total_count": 0
            }
        
        else:
            return {"error": f"Unknown resource URI: {uri}"}
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information"""
        return {
            "name": self.name,
            "version": self.version,
            "server_id": self.server_id,
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False
            },
            "is_running": self.is_running,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources)
        }


# Global server instance
fuschia_mcp_server = FuschiaMCPServer()


class MCPServerManager:
    """Manages multiple MCP server instances"""
    
    def __init__(self):
        self.servers: Dict[str, FuschiaMCPServer] = {}
        self.default_server = fuschia_mcp_server
        self.servers["fuschia-platform"] = self.default_server
    
    async def get_server(self, server_id: str) -> FuschiaMCPServer:
        """Get or create MCP server instance"""
        if server_id not in self.servers:
            server = FuschiaMCPServer(server_id)
            await server.initialize()
            self.servers[server_id] = server
        
        return self.servers[server_id]
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all available MCP servers"""
        return [server.get_server_info() for server in self.servers.values()]
    
    async def start_server(self, server_id: str) -> bool:
        """Start a specific MCP server"""
        try:
            server = await self.get_server(server_id)
            if not server.is_running:
                await server.initialize()
            return True
        except Exception as e:
            logger.error(f"Error starting MCP server '{server_id}': {e}")
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop a specific MCP server"""
        try:
            if server_id in self.servers:
                self.servers[server_id].is_running = False
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping MCP server '{server_id}': {e}")
            return False


# Global manager instance
mcp_server_manager = MCPServerManager()