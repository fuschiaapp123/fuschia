"""
HCM Pro MCP Server Implementation
Provides HCM Pro Job Offer API access through the Model Context Protocol (MCP)
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class HCMProMCPTool:
    """Represents an HCM Pro operation as an MCP tool"""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any],
                 operation_type: str):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.operation_type = operation_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class HCMProMCPResource:
    """Represents HCM Pro data as an MCP resource"""

    def __init__(self, uri: str, name: str, description: Optional[str] = None, mime_type: str = "application/json"):
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


class HCMProMCPServer:
    """
    HCM Pro MCP Server implementation
    Exposes HCM Pro Job Offer API operations via MCP protocol
    """

    def __init__(self, server_id: str = "hcmpro-api"):
        self.server_id = server_id
        self.name = "HCM Pro Job Offer API Server"
        self.version = "1.0.0"
        self.tools: Dict[str, HCMProMCPTool] = {}
        self.resources: Dict[str, HCMProMCPResource] = {}
        self.is_running = False

        # HCM Pro API configuration
        self.base_url = os.environ.get("HCMPRO_BASE_URL", "http://localhost:3101")
        self.admin_email = os.environ.get("HCMPRO_ADMIN_EMAIL", "admin@acme.com")
        self.admin_password = os.environ.get("HCMPRO_ADMIN_PASSWORD", "any_password")
        self.jwt_token: Optional[str] = None
        self.client = httpx.AsyncClient()

    async def initialize(self) -> None:
        """Initialize the HCM Pro MCP server with available operations"""
        logger.info(f"Initializing HCM Pro MCP Server: {self.server_id}")

        # Authenticate to get JWT token
        success = await self._authenticate()
        if not success:
            logger.warning("HCM Pro authentication failed, server will have limited functionality")

        # Load HCM Pro tools
        await self._load_hcmpro_tools()

        # Load HCM Pro resources
        await self._load_hcmpro_resources()

        self.is_running = True
        logger.info(f"HCM Pro MCP Server initialized with {len(self.tools)} tools and {len(self.resources)} resources")

    async def _authenticate(self) -> bool:
        """Authenticate with HCM Pro API to get JWT token"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "email": self.admin_email,
                    "password": self.admin_password
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                auth_data = response.json()
                self.jwt_token = auth_data.get("token") or auth_data.get("access_token")
                logger.info("HCM Pro authentication successful")
                return True
            else:
                logger.error(f"HCM Pro authentication failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"HCM Pro authentication error: {e}")
            return False

    def _check_auth(self) -> bool:
        """Check if authentication is available"""
        return self.jwt_token is not None

    def _get_headers(self) -> Dict[str, str]:
        """Get authenticated request headers"""
        headers = {"Content-Type": "application/json"}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers

    async def _load_hcmpro_tools(self) -> None:
        """Load HCM Pro Job Offer API operations as MCP tools"""
        try:
            # Core HCM Pro Job Offer operations
            core_tools: List[Dict[str, Any]] = [
                {
                    "name": "hcmpro_list_job_offers",
                    "description": "List job offers with optional filtering and pagination",
                    "operation_type": "list_job_offers",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "Filter by offer status (DRAFT, SENT, APPROVED, ACCEPTED, etc.)"
                            },
                            "departmentId": {
                                "type": "string",
                                "description": "Filter by department ID"
                            },
                            "employmentType": {
                                "type": "string",
                                "description": "Filter by employment type (FULL_TIME, PART_TIME, CONTRACT, etc.)"
                            },
                            "search": {
                                "type": "string",
                                "description": "Search in candidate name, email, or job title"
                            },
                            "page": {
                                "type": "integer",
                                "description": "Page number for pagination",
                                "default": 1,
                                "minimum": 1
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of results per page",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100
                            },
                            "sortBy": {
                                "type": "string",
                                "description": "Sort field (createdAt, salary, startDate)",
                                "enum": ["createdAt", "salary", "startDate"]
                            },
                            "sortOrder": {
                                "type": "string",
                                "description": "Sort direction",
                                "enum": ["asc", "desc"],
                                "default": "desc"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "hcmpro_get_job_offer",
                    "description": "Get a specific job offer by ID",
                    "operation_type": "get_job_offer",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Job offer ID"
                            }
                        },
                        "required": ["id"]
                    }
                },
                {
                    "name": "hcmpro_create_job_offer",
                    "description": "Create a new job offer",
                    "operation_type": "create_job_offer",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "positionId": {
                                "type": "string",
                                "description": "Position UUID"
                            },
                            "candidateName": {
                                "type": "string",
                                "description": "Candidate's full name"
                            },
                            "candidateEmail": {
                                "type": "string",
                                "description": "Candidate's email address"
                            },
                            "candidatePhone": {
                                "type": "string",
                                "description": "Candidate's phone number"
                            },
                            "jobTitle": {
                                "type": "string",
                                "description": "Job title for the offer"
                            },
                            "departmentId": {
                                "type": "string",
                                "description": "Department UUID"
                            },
                            "managerId": {
                                "type": "string",
                                "description": "Manager UUID"
                            },
                            "employmentType": {
                                "type": "string",
                                "description": "Employment type",
                                "enum": ["FULL_TIME", "PART_TIME", "CONTRACT", "TEMPORARY"]
                            },
                            "workLocation": {
                                "type": "string",
                                "description": "Work location type",
                                "enum": ["REMOTE", "ONSITE", "HYBRID"]
                            },
                            "startDate": {
                                "type": "string",
                                "description": "Start date in ISO format (e.g., 2024-02-01T00:00:00.000Z)"
                            },
                            "salary": {
                                "type": "number",
                                "description": "Salary amount"
                            },
                            "currency": {
                                "type": "string",
                                "description": "Currency code (e.g., USD, EUR)",
                                "default": "USD"
                            },
                            "expirationDate": {
                                "type": "string",
                                "description": "Offer expiration date in ISO format"
                            }
                        },
                        "required": ["positionId", "candidateName", "candidateEmail", "jobTitle", "departmentId", "managerId", "employmentType", "workLocation", "startDate", "salary", "expirationDate"]
                    }
                },
                {
                    "name": "hcmpro_update_job_offer",
                    "description": "Update an existing job offer",
                    "operation_type": "update_job_offer",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Job offer ID to update"
                            },
                            "salary": {
                                "type": "number",
                                "description": "Updated salary amount"
                            },
                            "startDate": {
                                "type": "string",
                                "description": "Updated start date in ISO format"
                            },
                            "expirationDate": {
                                "type": "string",
                                "description": "Updated expiration date in ISO format"
                            },
                            "workLocation": {
                                "type": "string",
                                "description": "Updated work location",
                                "enum": ["REMOTE", "ONSITE", "HYBRID"]
                            },
                            "employmentType": {
                                "type": "string",
                                "description": "Updated employment type",
                                "enum": ["FULL_TIME", "PART_TIME", "CONTRACT", "TEMPORARY"]
                            }
                        },
                        "required": ["id"]
                    }
                },
                {
                    "name": "hcmpro_send_job_offer",
                    "description": "Send job offer to candidate",
                    "operation_type": "send_job_offer",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Job offer ID to send"
                            }
                        },
                        "required": ["id"]
                    }
                },
                {
                    "name": "hcmpro_approve_job_offer",
                    "description": "Approve job offer",
                    "operation_type": "approve_job_offer",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Job offer ID to approve"
                            }
                        },
                        "required": ["id"]
                    }
                },
                {
                    "name": "hcmpro_accept_job_offer",
                    "description": "Accept job offer (candidate response)",
                    "operation_type": "accept_job_offer",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Job offer ID to accept"
                            }
                        },
                        "required": ["id"]
                    }
                },
                {
                    "name": "hcmpro_reject_job_offer",
                    "description": "Reject job offer",
                    "operation_type": "reject_job_offer",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Job offer ID to reject"
                            },
                            "rejectionReason": {
                                "type": "string",
                                "description": "Reason for rejection"
                            }
                        },
                        "required": ["id", "rejectionReason"]
                    }
                },
                {
                    "name": "hcmpro_convert_to_employee",
                    "description": "Convert accepted job offer to employee record",
                    "operation_type": "convert_to_employee",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Job offer ID to convert to employee"
                            }
                        },
                        "required": ["id"]
                    }
                }
            ]

            # Add core tools
            for tool_def in core_tools:
                tool = HCMProMCPTool(
                    name=str(tool_def["name"]),
                    description=str(tool_def["description"]),
                    input_schema=tool_def["input_schema"],
                    operation_type=str(tool_def["operation_type"])
                )
                self.tools[tool.name] = tool

            logger.info(f"Loaded {len(self.tools)} HCM Pro tools")

        except Exception as e:
            logger.error(f"Error loading HCM Pro tools: {e}")

    async def _load_hcmpro_resources(self) -> None:
        """Load HCM Pro data as MCP resources"""
        try:
            if not self._check_auth():
                return

            # Add job offers summary resource
            offers_resource = HCMProMCPResource(
                uri="hcmpro://job-offers/summary",
                name="Job Offers Summary",
                description="Summary of all job offers in the system",
                mime_type="application/json"
            )
            self.resources[offers_resource.uri] = offers_resource

            # Add job offer statistics resource
            stats_resource = HCMProMCPResource(
                uri="hcmpro://job-offers/statistics",
                name="Job Offer Statistics",
                description="Statistics and metrics for job offers",
                mime_type="application/json"
            )
            self.resources[stats_resource.uri] = stats_resource

            # Add departments resource
            departments_resource = HCMProMCPResource(
                uri="hcmpro://departments",
                name="Departments",
                description="Available departments in the organization",
                mime_type="application/json"
            )
            self.resources[departments_resource.uri] = departments_resource

            logger.info(f"Loaded {len(self.resources)} HCM Pro resources")

        except Exception as e:
            logger.error(f"Error loading HCM Pro resources: {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available HCM Pro MCP tools"""
        if not self.is_running:
            await self.initialize()

        return [tool.to_dict() for tool in self.tools.values()]

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available HCM Pro MCP resources"""
        if not self.is_running:
            await self.initialize()

        return [resource.to_dict() for resource in self.resources.values()]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute an HCM Pro MCP tool"""
        if not self.is_running:
            await self.initialize()

        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")

        if not self._check_auth():
            raise ValueError("HCM Pro authentication not available")

        tool = self.tools[name]

        try:
            result = await self._execute_hcmpro_operation(tool, arguments)

            return [{
                "type": "text",
                "text": json.dumps(result, indent=2, default=str)
            }]

        except Exception as e:
            logger.error(f"Error executing HCM Pro tool '{name}': {e}")
            return [{
                "type": "text",
                "text": f"Error executing HCM Pro operation: {str(e)}"
            }]

    async def _execute_hcmpro_operation(self, tool: HCMProMCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual HCM Pro API operation"""
        operation_type = tool.operation_type

        if operation_type == "list_job_offers":
            return await self._list_job_offers(arguments)

        elif operation_type == "get_job_offer":
            return await self._get_job_offer(arguments["id"])

        elif operation_type == "create_job_offer":
            return await self._create_job_offer(arguments)

        elif operation_type == "update_job_offer":
            return await self._update_job_offer(arguments["id"], arguments)

        elif operation_type == "send_job_offer":
            return await self._send_job_offer(arguments["id"])

        elif operation_type == "approve_job_offer":
            return await self._approve_job_offer(arguments["id"])

        elif operation_type == "accept_job_offer":
            return await self._accept_job_offer(arguments["id"])

        elif operation_type == "reject_job_offer":
            return await self._reject_job_offer(arguments["id"], arguments["rejectionReason"])

        elif operation_type == "convert_to_employee":
            return await self._convert_to_employee(arguments["id"])

        else:
            raise ValueError(f"Unknown operation type: {operation_type}")

    async def _list_job_offers(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List job offers with optional filtering and pagination"""
        try:
            params = {}

            # Add query parameters
            for key in ["status", "departmentId", "employmentType", "search", "page", "limit", "sortBy", "sortOrder"]:
                if arguments.get(key) is not None:
                    params[key] = arguments[key]

            response = await self.client.get(
                f"{self.base_url}/api/job-offers",
                params=params,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "list_job_offers",
                    "success": True,
                    "data": data,
                    "parameters": arguments
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in list_job_offers: {e}")
            raise

    async def _get_job_offer(self, offer_id: str) -> Dict[str, Any]:
        """Get a specific job offer by ID"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/job-offers/{offer_id}",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "get_job_offer",
                    "offer_id": offer_id,
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in get_job_offer: {e}")
            raise

    async def _create_job_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job offer"""
        try:
            # Remove the 'id' field if present since it's for creation
            creation_data = {k: v for k, v in offer_data.items() if k != "id"}

            response = await self.client.post(
                f"{self.base_url}/api/job-offers",
                json=creation_data,
                headers=self._get_headers()
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "operation": "create_job_offer",
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in create_job_offer: {e}")
            raise

    async def _update_job_offer(self, offer_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing job offer"""
        try:
            # Remove the 'id' field from update data
            update_payload = {k: v for k, v in update_data.items() if k != "id"}

            response = await self.client.put(
                f"{self.base_url}/api/job-offers/{offer_id}",
                json=update_payload,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "update_job_offer",
                    "offer_id": offer_id,
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in update_job_offer: {e}")
            raise

    async def _send_job_offer(self, offer_id: str) -> Dict[str, Any]:
        """Send job offer to candidate"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job-offers/{offer_id}/send",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "send_job_offer",
                    "offer_id": offer_id,
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in send_job_offer: {e}")
            raise

    async def _approve_job_offer(self, offer_id: str) -> Dict[str, Any]:
        """Approve job offer"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job-offers/{offer_id}/approve",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "approve_job_offer",
                    "offer_id": offer_id,
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in approve_job_offer: {e}")
            raise

    async def _accept_job_offer(self, offer_id: str) -> Dict[str, Any]:
        """Accept job offer (candidate response)"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job-offers/{offer_id}/accept",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "accept_job_offer",
                    "offer_id": offer_id,
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in accept_job_offer: {e}")
            raise

    async def _reject_job_offer(self, offer_id: str, rejection_reason: str) -> Dict[str, Any]:
        """Reject job offer"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job-offers/{offer_id}/reject",
                json={"rejectionReason": rejection_reason},
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "reject_job_offer",
                    "offer_id": offer_id,
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in reject_job_offer: {e}")
            raise

    async def _convert_to_employee(self, offer_id: str) -> Dict[str, Any]:
        """Convert accepted job offer to employee record"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job-offers/{offer_id}/convert-to-employee",
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "operation": "convert_to_employee",
                    "offer_id": offer_id,
                    "success": True,
                    "data": data
                }
            else:
                raise ValueError(f"API request failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in convert_to_employee: {e}")
            raise

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read an HCM Pro resource"""
        if not self.is_running:
            await self.initialize()

        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' not found")

        if not self._check_auth():
            raise ValueError("HCM Pro authentication not available")

        try:
            if uri == "hcmpro://job-offers/summary":
                # Get summary of all job offers
                summary_result = await self._list_job_offers({"limit": 100})
                content = {
                    "total_offers": len(summary_result["data"].get("jobOffers", [])),
                    "summary": summary_result["data"]
                }

            elif uri == "hcmpro://job-offers/statistics":
                # Get statistics about job offers
                all_offers = await self._list_job_offers({"limit": 1000})
                offers = all_offers["data"].get("jobOffers", [])

                status_counts: Dict[str, int] = {}
                for offer in offers:
                    status = offer.get("status", "UNKNOWN")
                    status_counts[status] = status_counts.get(status, 0) + 1

                content = {
                    "total_offers": len(offers),
                    "status_distribution": status_counts,
                    "generated_at": datetime.utcnow().isoformat()
                }

            elif uri == "hcmpro://departments":
                # Mock departments data (would be fetched from API if available)
                content = {
                    "departments": [
                        {"id": "dept-eng", "name": "Engineering"},
                        {"id": "dept-sales", "name": "Sales"},
                        {"id": "dept-hr", "name": "Human Resources"},
                        {"id": "dept-finance", "name": "Finance"}
                    ]
                }

            else:
                raise ValueError(f"Unknown resource URI: {uri}")

            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(content, indent=2, default=str)
                }]
            }

        except Exception as e:
            logger.error(f"Error reading HCM Pro resource '{uri}': {e}")
            raise ValueError(f"Error reading resource: {str(e)}")

    def get_server_info(self) -> Dict[str, Any]:
        """Get HCM Pro MCP server information"""
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
            "authenticated": self._check_auth(),
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "base_url": self.base_url
        }

    async def __aenter__(self) -> "HCMProMCPServer":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.client.aclose()


# Singleton instance
hcmpro_mcp_server = HCMProMCPServer()