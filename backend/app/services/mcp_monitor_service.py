"""
MCP Monitor Service
Monitors and manages multiple MCP services (Gmail, HCMPro, etc.)
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class MCPServiceConfig:
    """Configuration for an MCP service"""
    service_id: str
    service_name: str
    enabled: bool = True
    auto_start: bool = False


class MCPMonitorService:
    """Service for monitoring and managing multiple MCP services"""

    def __init__(self):
        self.logger = logger.bind(service="MCPMonitorService")
        self.services_config: Dict[str, MCPServiceConfig] = {}
        self.initialized = False

    async def initialize(self):
        """Initialize the MCP monitor service"""
        try:
            self.logger.info("Initializing MCP Monitor Service")

            # Register available MCP services
            self.services_config = {
                "gmail": MCPServiceConfig(
                    service_id="gmail",
                    service_name="Gmail API",
                    enabled=True,
                    auto_start=False
                ),
                "hcmpro": MCPServiceConfig(
                    service_id="hcmpro",
                    service_name="HCMPro API",
                    enabled=True,
                    auto_start=False
                )
            }

            self.initialized = True
            self.logger.info("MCP Monitor Service initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize MCP Monitor Service", error=str(e))
            raise

    async def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get status of a specific MCP service"""
        try:
            if service_id == "gmail":
                from app.services.gmail_mcp_server import gmail_mcp_server
                return {
                    "service_id": "gmail",
                    "service_name": "Gmail API",
                    "is_running": gmail_mcp_server.is_running,
                    "status": "running" if gmail_mcp_server.is_running else "stopped",
                    "capabilities": ["gmail_list_messages", "gmail_get_message", "gmail_send_message"],
                    "config": self.services_config.get("gmail", {}).__dict__ if "gmail" in self.services_config else {}
                }
            elif service_id == "hcmpro":
                from app.services.hcmpro_mcp_server import hcmpro_mcp_server
                return {
                    "service_id": "hcmpro",
                    "service_name": "HCMPro API",
                    "is_running": hcmpro_mcp_server.is_running,
                    "status": "running" if hcmpro_mcp_server.is_running else "stopped",
                    "capabilities": ["hcmpro_list_job_offers", "hcmpro_get_job_offer"],
                    "config": self.services_config.get("hcmpro", {}).__dict__ if "hcmpro" in self.services_config else {}
                }
            else:
                return {
                    "service_id": service_id,
                    "service_name": f"Unknown Service ({service_id})",
                    "is_running": False,
                    "status": "unknown",
                    "capabilities": [],
                    "config": {}
                }

        except Exception as e:
            self.logger.error(f"Error getting status for service {service_id}", error=str(e))
            return {
                "service_id": service_id,
                "service_name": f"Service {service_id}",
                "is_running": False,
                "status": "error",
                "error": str(e),
                "capabilities": [],
                "config": {}
            }

    async def get_all_services_status(self) -> List[Dict[str, Any]]:
        """Get status of all MCP services"""
        services_status = []
        for service_id in self.services_config.keys():
            status = await self.get_service_status(service_id)
            services_status.append(status)
        return services_status

    async def start_service(self, service_id: str) -> Dict[str, Any]:
        """Start a specific MCP service"""
        try:
            if service_id == "gmail":
                from app.services.gmail_mcp_server import gmail_mcp_server
                if not gmail_mcp_server.is_running:
                    await gmail_mcp_server.initialize()
                return {"success": True, "message": f"Gmail MCP service started successfully"}
            elif service_id == "hcmpro":
                from app.services.hcmpro_mcp_server import hcmpro_mcp_server
                if not hcmpro_mcp_server.is_running:
                    await hcmpro_mcp_server.initialize()
                return {"success": True, "message": f"HCMPro MCP service started successfully"}
            else:
                return {"success": False, "message": f"Unknown service: {service_id}"}

        except Exception as e:
            self.logger.error(f"Error starting service {service_id}", error=str(e))
            return {"success": False, "message": f"Failed to start service: {str(e)}"}

    async def stop_service(self, service_id: str) -> Dict[str, Any]:
        """Stop a specific MCP service"""
        try:
            if service_id == "gmail":
                from app.services.gmail_mcp_server import gmail_mcp_server
                if gmail_mcp_server.is_running:
                    await gmail_mcp_server.cleanup()
                return {"success": True, "message": f"Gmail MCP service stopped successfully"}
            elif service_id == "hcmpro":
                from app.services.hcmpro_mcp_server import hcmpro_mcp_server
                if hcmpro_mcp_server.is_running:
                    await hcmpro_mcp_server.cleanup()
                return {"success": True, "message": f"HCMPro MCP service stopped successfully"}
            else:
                return {"success": False, "message": f"Unknown service: {service_id}"}

        except Exception as e:
            self.logger.error(f"Error stopping service {service_id}", error=str(e))
            return {"success": False, "message": f"Failed to stop service: {str(e)}"}

    async def test_service_connection(self, service_id: str) -> Dict[str, Any]:
        """Test connection to a specific MCP service"""
        try:
            if service_id == "gmail":
                from app.services.gmail_mcp_server import gmail_mcp_server

                if not gmail_mcp_server.is_running:
                    return {
                        "success": False,
                        "service_id": service_id,
                        "message": "Gmail MCP server is not running"
                    }

                # Test by listing messages
                test_result = await gmail_mcp_server.call_tool("gmail_list_messages", {
                    "query": "in:inbox",
                    "max_results": 1
                })

                if test_result and test_result[0].get('text'):
                    data = json.loads(test_result[0]['text'])
                    success = data.get('success', False)
                    return {
                        "success": success,
                        "service_id": service_id,
                        "message": "Connection successful" if success else "Connection failed",
                        "test_result": data
                    }
                else:
                    return {
                        "success": False,
                        "service_id": service_id,
                        "message": "No response from Gmail API"
                    }

            elif service_id == "hcmpro":
                from app.services.hcmpro_mcp_server import hcmpro_mcp_server

                if not hcmpro_mcp_server.is_running:
                    return {
                        "success": False,
                        "service_id": service_id,
                        "message": "HCMPro MCP server is not running"
                    }

                # Test by listing job offers
                test_result = await hcmpro_mcp_server.call_tool("hcmpro_list_job_offers", {
                    "max_results": 1
                })

                if test_result and test_result[0].get('text'):
                    data = json.loads(test_result[0]['text'])
                    success = data.get('success', False)
                    return {
                        "success": success,
                        "service_id": service_id,
                        "message": "Connection successful" if success else "Connection failed",
                        "test_result": data
                    }
                else:
                    return {
                        "success": False,
                        "service_id": service_id,
                        "message": "No response from HCMPro API"
                    }
            else:
                return {
                    "success": False,
                    "service_id": service_id,
                    "message": f"Unknown service: {service_id}"
                }

        except Exception as e:
            self.logger.error(f"Error testing service {service_id}", error=str(e))
            return {
                "success": False,
                "service_id": service_id,
                "message": f"Connection test failed: {str(e)}"
            }

    async def update_service_config(self, service_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration for a specific MCP service"""
        try:
            if service_id in self.services_config:
                # Update configuration
                for key, value in config.items():
                    if hasattr(self.services_config[service_id], key):
                        setattr(self.services_config[service_id], key, value)

                self.logger.info(f"Updated configuration for service {service_id}", config=config)
                return {"success": True, "message": f"Configuration updated for {service_id}"}
            else:
                return {"success": False, "message": f"Unknown service: {service_id}"}

        except Exception as e:
            self.logger.error(f"Error updating config for service {service_id}", error=str(e))
            return {"success": False, "message": f"Failed to update config: {str(e)}"}


# Global instance
mcp_monitor_service = MCPMonitorService()
