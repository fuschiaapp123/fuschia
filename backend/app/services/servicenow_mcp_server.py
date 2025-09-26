"""
ServiceNow MCP Server Implementation
Provides ServiceNow API access through the Model Context Protocol (MCP)
"""

import json
import logging
import os
import httpx
from typing import Dict, List, Any

from app.api.endpoints.servicenow import (
    get_servicenow_data, 
    get_servicenow_tables_safely,
    flatten_dict
)

logger = logging.getLogger(__name__)


class ServiceNowMCPTool:
    """Represents a ServiceNow operation as an MCP tool"""
    
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], 
                 operation_type: str, table_name: str = None):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.operation_type = operation_type  # 'list_tables', 'list_records', 'get_record', 'create_record', 'update_record'
        self.table_name = table_name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class ServiceNowMCPResource:
    """Represents ServiceNow data as an MCP resource"""
    
    def __init__(self, uri: str, name: str, description: str = None, mime_type: str = "application/json"):
        self.uri = uri
        self.name = name
        self.description = description
        self.mime_type = mime_type
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "uri": self.uri,
            "name": self.name,
            "mimeType": self.mime_type
        }
        if self.description:
            result["description"] = self.description
        return result


class ServiceNowMCPServer:
    """
    ServiceNow MCP Server implementation
    Exposes ServiceNow API operations via MCP protocol
    """
    
    def __init__(self, server_id: str = "servicenow-api"):
        self.server_id = server_id
        self.name = "ServiceNow API Server"
        self.version = "1.0.0"
        self.tools: Dict[str, ServiceNowMCPTool] = {}
        self.resources: Dict[str, ServiceNowMCPResource] = {}
        self.is_running = False
        
        # ServiceNow connection details
        self.instance_url = os.environ.get("SERVICENOW_INSTANCE_URL")
        self.username = os.environ.get("SERVICENOW_INSTANCE_USERNAME")
        self.password = os.environ.get("SERVICENOW_INSTANCE_PASSWORD")
        
    async def initialize(self):
        """Initialize the ServiceNow MCP server with available operations"""
        logger.info(f"Initializing ServiceNow MCP Server: {self.server_id}")
        
        # Check ServiceNow connection
        if not self._check_credentials():
            logger.warning("ServiceNow credentials not configured, server will have limited functionality")
        
        # Load ServiceNow tools
        await self._load_servicenow_tools()
        
        # Load ServiceNow resources
        await self._load_servicenow_resources()
        
        self.is_running = True
        logger.info(f"ServiceNow MCP Server initialized with {len(self.tools)} tools and {len(self.resources)} resources")
    
    def _check_credentials(self) -> bool:
        """Check if ServiceNow credentials are configured"""
        return bool(
            self.instance_url and self.instance_url.strip() and
            self.username and self.username.strip() and
            self.password and self.password.strip()
        )
    
    async def _load_servicenow_tools(self):
        """Load ServiceNow API operations as MCP tools"""
        try:
            # Core ServiceNow operations
            core_tools = [
                {
                    "name": "servicenow_list_tables",
                    "description": "List all available ServiceNow tables",
                    "operation_type": "list_tables",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "servicenow_get_table_records",
                    "description": "Get records from a ServiceNow table with optional filtering",
                    "operation_type": "list_records",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string",
                                "description": "ServiceNow table name (e.g., 'incident', 'change_request')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of records to return",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 1000
                            },
                            "fields": {
                                "type": "string",
                                "description": "Comma-separated list of fields to return"
                            },
                            "filters": {
                                "type": "string",
                                "description": "ServiceNow query filters (e.g., 'state=1^active=true')"
                            },
                            "sort_field": {
                                "type": "string",
                                "description": "Field to sort by"
                            },
                            "sort_order": {
                                "type": "string",
                                "enum": ["asc", "desc"],
                                "description": "Sort order",
                                "default": "asc"
                            }
                        },
                        "required": ["table"]
                    }
                },
                {
                    "name": "servicenow_get_record",
                    "description": "Get a specific ServiceNow record by sys_id",
                    "operation_type": "get_record",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string",
                                "description": "ServiceNow table name"
                            },
                            "sys_id": {
                                "type": "string",
                                "description": "ServiceNow record sys_id"
                            },
                            "fields": {
                                "type": "string",
                                "description": "Comma-separated list of fields to return"
                            }
                        },
                        "required": ["table", "sys_id"]
                    }
                },
                {
                    "name": "servicenow_create_record",
                    "description": "Create a new record in a ServiceNow table",
                    "operation_type": "create_record",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string",
                                "description": "ServiceNow table name"
                            },
                            "data": {
                                "type": "object",
                                "description": "Record data as key-value pairs"
                            }
                        },
                        "required": ["table", "data"]
                    }
                },
                {
                    "name": "servicenow_update_record",
                    "description": "Update an existing ServiceNow record",
                    "operation_type": "update_record",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string",
                                "description": "ServiceNow table name"
                            },
                            "sys_id": {
                                "type": "string",
                                "description": "ServiceNow record sys_id"
                            },
                            "data": {
                                "type": "object",
                                "description": "Updated record data as key-value pairs"
                            }
                        },
                        "required": ["table", "sys_id", "data"]
                    }
                },
                {
                    "name": "servicenow_delete_record",
                    "description": "Delete a ServiceNow record",
                    "operation_type": "delete_record",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string",
                                "description": "ServiceNow table name"
                            },
                            "sys_id": {
                                "type": "string",
                                "description": "ServiceNow record sys_id"
                            }
                        },
                        "required": ["table", "sys_id"]
                    }
                }
            ]
            
            # Add core tools
            for tool_def in core_tools:
                tool = ServiceNowMCPTool(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    input_schema=tool_def["input_schema"],
                    operation_type=tool_def["operation_type"]
                )
                self.tools[tool.name] = tool
            
            # Add table-specific tools if credentials are available
            if self._check_credentials():
                await self._load_table_specific_tools()
                
            logger.info(f"Loaded {len(self.tools)} ServiceNow tools")
            
        except Exception as e:
            logger.error(f"Error loading ServiceNow tools: {e}")
    
    async def _load_table_specific_tools(self):
        """Load table-specific ServiceNow tools"""
        try:
            # Get available tables
            tables = get_servicenow_tables_safely()
            
            # Add quick access tools for common tables
            common_tables = ['incident', 'change_request', 'problem', 'sys_user']
            
            for table_info in tables:
                table_name = table_info.get('name', '')
                table_label = table_info.get('label', table_name)
                
                if table_name in common_tables:
                    # Add quick list tool for this table
                    quick_tool = ServiceNowMCPTool(
                        name=f"servicenow_list_{table_name}",
                        description=f"List {table_label} records with common filters",
                        input_schema={
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of records",
                                    "default": 10,
                                    "maximum": 100
                                },
                                "active_only": {
                                    "type": "boolean",
                                    "description": "Show only active records",
                                    "default": True
                                },
                                "state": {
                                    "type": "string",
                                    "description": "Filter by state (for tickets)"
                                }
                            },
                            "required": []
                        },
                        operation_type="list_records",
                        table_name=table_name
                    )
                    self.tools[quick_tool.name] = quick_tool
                    
        except Exception as e:
            logger.error(f"Error loading table-specific tools: {e}")
    
    async def _load_servicenow_resources(self):
        """Load ServiceNow data as MCP resources"""
        try:
            if not self._check_credentials():
                return
                
            # Add table schema resources
            tables = get_servicenow_tables_safely()
            
            for table_info in tables:
                table_name = table_info.get('name', '')
                table_label = table_info.get('label', table_name)
                
                resource = ServiceNowMCPResource(
                    uri=f"servicenow://table/{table_name}",
                    name=f"ServiceNow {table_label} Table",
                    description=f"Schema and data access for {table_label} table",
                    mime_type="application/json"
                )
                self.resources[resource.uri] = resource
                
            logger.info(f"Loaded {len(self.resources)} ServiceNow resources")
            
        except Exception as e:
            logger.error(f"Error loading ServiceNow resources: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available ServiceNow MCP tools"""
        if not self.is_running:
            await self.initialize()
        
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available ServiceNow MCP resources"""
        if not self.is_running:
            await self.initialize()
        
        return [resource.to_dict() for resource in self.resources.values()]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a ServiceNow MCP tool"""
        if not self.is_running:
            await self.initialize()
        
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        
        tool = self.tools[name]
        
        try:
            result = await self._execute_servicenow_operation(tool, arguments)
            
            return [{
                "type": "text",
                "text": json.dumps(result, indent=2, default=str)
            }]
            
        except Exception as e:
            logger.error(f"Error executing ServiceNow tool '{name}': {e}")
            return [{
                "type": "text", 
                "text": f"Error executing ServiceNow operation: {str(e)}"
            }]
    
    async def _execute_servicenow_operation(self, tool: ServiceNowMCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual ServiceNow API operation"""
        operation_type = tool.operation_type
        
        if operation_type == "list_tables":
            return await self._list_tables()
        
        elif operation_type == "list_records":
            table = arguments.get("table") or tool.table_name
            if not table:
                raise ValueError("Table name is required")
            return await self._list_records(table, arguments)
        
        elif operation_type == "get_record":
            return await self._get_record(arguments["table"], arguments["sys_id"], arguments.get("fields"))
        
        elif operation_type == "create_record":
            return await self._create_record(arguments["table"], arguments["data"])
        
        elif operation_type == "update_record":
            return await self._update_record(arguments["table"], arguments["sys_id"], arguments["data"])
        
        elif operation_type == "delete_record":
            return await self._delete_record(arguments["table"], arguments["sys_id"])
        
        else:
            raise ValueError(f"Unknown operation type: {operation_type}")
    
    async def _list_tables(self) -> Dict[str, Any]:
        """List ServiceNow tables"""
        tables = get_servicenow_tables_safely()
        return {
            "operation": "list_tables",
            "success": True,
            "data": tables,
            "count": len(tables)
        }
    
    async def _list_records(self, table: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List records from ServiceNow table"""
        params = {
            'sysparm_limit': arguments.get('limit', 10),
            'sysparm_display_value': 'all'
        }
        
        # Handle filters
        filters = []
        if arguments.get('filters'):
            filters.append(arguments['filters'])
        
        # Handle common parameters for table-specific tools
        if arguments.get('active_only'):
            filters.append('active=true')
        
        if arguments.get('state'):
            filters.append(f"state={arguments['state']}")
        
        if filters:
            params['sysparm_query'] = '^'.join(filters)
        
        if arguments.get('fields'):
            params['sysparm_fields'] = arguments['fields']
        
        if arguments.get('sort_field'):
            sort_order = arguments.get('sort_order', 'asc')
            if sort_order == 'desc':
                params['sysparm_order_by'] = f"{arguments['sort_field']}^DESC"
            else:
                params['sysparm_order_by'] = arguments['sort_field']
        
        data = get_servicenow_data(table, params)
        flattened_data = [flatten_dict(record) for record in data]
        
        return {
            "operation": "list_records",
            "table": table,
            "success": True,
            "data": flattened_data,
            "count": len(flattened_data),
            "parameters": arguments
        }
    
    async def _get_record(self, table: str, sys_id: str, fields: str = None) -> Dict[str, Any]:
        """Get a specific ServiceNow record"""
        params = {'sysparm_display_value': 'all'}
        if fields:
            params['sysparm_fields'] = fields
        
        # Use ServiceNow API to get specific record
        endpoint = f"{self.instance_url}/api/now/table/{table}/{sys_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                auth=(self.username, self.password),
                headers={"Accept": "application/json"},
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            record = data.get('result', {})
            flattened_record = flatten_dict(record)
            
            return {
                "operation": "get_record",
                "table": table,
                "sys_id": sys_id,
                "success": True,
                "data": flattened_record
            }
    
    async def _create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ServiceNow record"""
        endpoint = f"{self.instance_url}/api/now/table/{table}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            record = result.get('result', {})
            flattened_record = flatten_dict(record)
            
            return {
                "operation": "create_record",
                "table": table,
                "success": True,
                "data": flattened_record,
                "sys_id": flattened_record.get('sys_id')
            }
    
    async def _update_record(self, table: str, sys_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a ServiceNow record"""
        endpoint = f"{self.instance_url}/api/now/table/{table}/{sys_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                endpoint,
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            record = result.get('result', {})
            flattened_record = flatten_dict(record)
            
            return {
                "operation": "update_record",
                "table": table,
                "sys_id": sys_id,
                "success": True,
                "data": flattened_record
            }
    
    async def _delete_record(self, table: str, sys_id: str) -> Dict[str, Any]:
        """Delete a ServiceNow record"""
        endpoint = f"{self.instance_url}/api/now/table/{table}/{sys_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                endpoint,
                auth=(self.username, self.password),
                headers={"Accept": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            
            return {
                "operation": "delete_record",
                "table": table,
                "sys_id": sys_id,
                "success": True,
                "message": "Record deleted successfully"
            }
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a ServiceNow resource"""
        if not self.is_running:
            await self.initialize()
        
        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' not found")
        
        # Parse the URI to determine what data to return
        if uri.startswith("servicenow://table/"):
            table_name = uri.replace("servicenow://table/", "")
            
            # Return table schema and sample data
            params = {
                'sysparm_limit': 5,
                'sysparm_display_value': 'all'
            }
            
            sample_data = get_servicenow_data(table_name, params)
            flattened_data = [flatten_dict(record) for record in sample_data]
            
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "table": table_name,
                        "description": f"ServiceNow {table_name} table data",
                        "sample_records": flattened_data,
                        "record_count": len(flattened_data)
                    }, indent=2, default=str)
                }]
            }
        
        else:
            raise ValueError(f"Unknown resource URI format: {uri}")

    def get_server_info(self) -> Dict[str, Any]:
        """Get ServiceNow MCP server information"""
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
            "resources_count": len(self.resources),
            "instance_url": self.instance_url if self.instance_url else "Not configured"
        }


# Singleton instance
servicenow_mcp_server = ServiceNowMCPServer()