"""
Simplified MCP Tools Service
Directly exposes MCP server methods as callable DSPy tools
"""
import structlog
from typing import List, Callable, Dict, Any

logger = structlog.get_logger(__name__)


class MCPToolsService:
    """Simple service to expose MCP server methods as DSPy tools"""

    def __init__(self):
        self.mcp_servers = {}
        self.initialized = False

    async def initialize(self):
        """Initialize and connect to available MCP servers"""
        if self.initialized:
            return

        logger.info("Initializing MCP Tools Service")

        # Import and register Gmail MCP server
        try:
            from app.services.gmail_mcp_server import gmail_mcp_server
            if gmail_mcp_server.is_running:
                self.mcp_servers['gmail'] = gmail_mcp_server
                logger.info("Gmail MCP server connected", tools=len(gmail_mcp_server.tools))
        except Exception as e:
            logger.warning("Gmail MCP server not available", error=str(e))

        # Import and register HCMPro MCP server
        try:
            from app.services.hcmpro_mcp_server import hcmpro_mcp_server
            if hcmpro_mcp_server.is_running:
                self.mcp_servers['hcmpro'] = hcmpro_mcp_server
                logger.info("HCMPro MCP server connected", tools=len(hcmpro_mcp_server.tools))
        except Exception as e:
            logger.warning("HCMPro MCP server not available", error=str(e))

        self.initialized = True
        logger.info("MCP Tools Service initialized", servers=list(self.mcp_servers.keys()))

    def get_dspy_tools(self, selected_tool_names: List[str] = None) -> List[Callable]:
        """Get MCP tools as individual DSPy-compatible async functions

        Args:
            selected_tool_names: Optional list of tool names to filter (e.g., ['gmail_list_messages'])
                                If None, returns all available tools.
        """
        if not self.initialized:
            logger.warning("MCP Tools Service not initialized - returning empty tools list")
            return []

        tools = []

        for server_name, mcp_server in self.mcp_servers.items():
            if not hasattr(mcp_server, 'tools') or not mcp_server.tools:
                continue

            # MCP server tools can be dict of tool objects or dict of dicts
            for tool_name, tool_obj in mcp_server.tools.items():
                # Filter by selected tools if provided
                if selected_tool_names is not None and tool_name not in selected_tool_names:
                    logger.debug(f"Skipping MCP tool {tool_name} - not in selected tools")
                    continue

                # Extract tool info - handle both object and dict formats
                if hasattr(tool_obj, 'description'):
                    # It's a tool object (like GmailMCPTool)
                    tool_description = tool_obj.description
                elif isinstance(tool_obj, dict):
                    # It's a dict
                    tool_description = tool_obj.get('description', f'Execute {tool_name}')
                else:
                    tool_description = f'Execute {tool_name}'

                # Create a wrapper function for this specific MCP tool
                tool_func = self._create_tool_wrapper(server_name, tool_name, tool_description, mcp_server)
                tools.append(tool_func)
                logger.debug(f"Created DSPy tool: {tool_name} from {server_name}")

        logger.info(f"Created {len(tools)} MCP DSPy tools" +
                   (f" (filtered from {selected_tool_names})" if selected_tool_names else " (all available)"))
        return tools

    def _create_tool_wrapper(self, server_name: str, tool_name: str, tool_description: str, mcp_server) -> Callable:
        """Create a DSPy-compatible wrapper for an MCP tool"""

        async def mcp_tool(**kwargs) -> str:
            """Execute MCP tool"""
            try:
                logger.info(f"Executing MCP tool: {tool_name}", server=server_name, params=kwargs)

                # DSPy sometimes wraps parameters in a 'kwargs' key - unwrap if needed
                if len(kwargs) == 1 and 'kwargs' in kwargs:
                    logger.debug(f"Unwrapping nested kwargs for {tool_name}")
                    actual_params = kwargs['kwargs']
                else:
                    actual_params = kwargs

                logger.info(f"Calling MCP server with params: {actual_params}")

                # Call the MCP server's call_tool method with unwrapped params
                result = await mcp_server.call_tool(tool_name, actual_params)

                # Format result as string for DSPy
                # MCP tools return a list of content objects
                if isinstance(result, list) and len(result) > 0:
                    # Extract text from first content object
                    first_content = result[0]
                    if isinstance(first_content, dict) and 'text' in first_content:
                        return first_content['text']

                # Fallback to string representation
                return str(result)

            except Exception as e:
                error_msg = f"MCP tool {tool_name} failed: {str(e)}"
                logger.error(error_msg, server=server_name, tool=tool_name, error=str(e))
                return error_msg

        # Set function metadata for DSPy
        mcp_tool.__name__ = tool_name
        mcp_tool.__doc__ = tool_description

        return mcp_tool


# Global instance
mcp_tools_service = MCPToolsService()
