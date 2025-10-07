"""
Gmail MCP Server Implementation
Provides Gmail API access through the Model Context Protocol (MCP)
"""

import json
import logging
import os
import base64
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailMCPTool:
    """Represents a Gmail operation as an MCP tool"""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any],
                 operation_type: str):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.operation_type = operation_type  # 'list_messages', 'get_message', 'send_message', 'search_messages', etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class GmailMCPResource:
    """Represents Gmail data as an MCP resource"""

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


class GmailMCPServer:
    """
    Gmail MCP Server implementation
    Exposes Gmail API operations via MCP protocol
    """

    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose',
        'https://www.googleapis.com/auth/gmail.modify'
    ]

    def __init__(self, server_id: str = "gmail-api"):
        self.server_id = server_id
        self.name = "Gmail API Server"
        self.version = "1.0.0"
        self.tools: Dict[str, GmailMCPTool] = {}
        self.resources: Dict[str, GmailMCPResource] = {}
        self.is_running = False

        # Gmail API credentials
        self.credentials_file = os.environ.get("GMAIL_CREDENTIALS_FILE", "credentials.json")
        self.token_file = os.environ.get("GMAIL_TOKEN_FILE", "token.json")
        self.creds: Optional[Credentials] = None
        self.service = None

    async def initialize(self):
        """Initialize the Gmail MCP server with available operations"""
        logger.info(f"Initializing Gmail MCP Server: {self.server_id}")

        # Set up Gmail API authentication
        success = await self._setup_gmail_auth()
        if not success:
            logger.warning("Gmail authentication not configured, server will have limited functionality")

        # Load Gmail tools
        await self._load_gmail_tools()

        # Load Gmail resources
        await self._load_gmail_resources()

        self.is_running = True
        logger.info(f"Gmail MCP Server initialized with {len(self.tools)} tools and {len(self.resources)} resources")

    async def _setup_gmail_auth(self) -> bool:
        """Set up Gmail API authentication using OAuth2"""
        try:
            # Load existing token if available
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Gmail credentials file not found: {self.credentials_file}")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail API authentication successful")
            return True

        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False

    def _check_auth(self) -> bool:
        """Check if Gmail authentication is available"""
        return self.service is not None

    async def _load_gmail_tools(self):
        """Load Gmail API operations as MCP tools"""
        try:
            # Core Gmail operations
            core_tools = [
                {
                    "name": "gmail_list_messages",
                    "description": "List Gmail messages with optional filtering and pagination",
                    "operation_type": "list_messages",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Gmail search query (e.g., 'from:example@email.com', 'subject:urgent', 'is:unread')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of messages to return",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 500
                            },
                            "label_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of label IDs to filter by (e.g., ['INBOX', 'UNREAD'])"
                            },
                            "page_token": {
                                "type": "string",
                                "description": "Token for pagination"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "gmail_get_message",
                    "description": "Get a specific Gmail message by ID with full content",
                    "operation_type": "get_message",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message_id": {
                                "type": "string",
                                "description": "Gmail message ID"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["full", "metadata", "minimal", "raw"],
                                "description": "Message format to return",
                                "default": "full"
                            },
                            "metadata_headers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of headers to include when format is 'metadata'"
                            }
                        },
                        "required": ["message_id"]
                    }
                },
                {
                    "name": "gmail_send_message",
                    "description": "Send a new Gmail message",
                    "operation_type": "send_message",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body content"
                            },
                            "cc": {
                                "type": "string",
                                "description": "CC recipients (comma-separated)"
                            },
                            "bcc": {
                                "type": "string",
                                "description": "BCC recipients (comma-separated)"
                            },
                            "html": {
                                "type": "boolean",
                                "description": "Whether body is HTML format",
                                "default": False
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                },
                {
                    "name": "gmail_search_messages",
                    "description": "Search Gmail messages with advanced query options",
                    "operation_type": "search_messages",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Gmail search query string"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 50,
                                "maximum": 500
                            },
                            "include_spam_trash": {
                                "type": "boolean",
                                "description": "Include spam and trash in search",
                                "default": False
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "gmail_list_labels",
                    "description": "List all Gmail labels",
                    "operation_type": "list_labels",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "gmail_get_profile",
                    "description": "Get Gmail user profile information",
                    "operation_type": "get_profile",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "gmail_modify_message",
                    "description": "Modify message labels (mark as read/unread, add/remove labels)",
                    "operation_type": "modify_message",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message_id": {
                                "type": "string",
                                "description": "Gmail message ID"
                            },
                            "add_label_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Labels to add to the message"
                            },
                            "remove_label_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Labels to remove from the message"
                            }
                        },
                        "required": ["message_id"]
                    }
                },
                {
                    "name": "gmail_get_thread",
                    "description": "Get a Gmail conversation thread by ID",
                    "operation_type": "get_thread",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "thread_id": {
                                "type": "string",
                                "description": "Gmail thread ID"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["full", "metadata", "minimal"],
                                "description": "Message format within thread",
                                "default": "full"
                            }
                        },
                        "required": ["thread_id"]
                    }
                }
            ]

            # Add core tools
            for tool_def in core_tools:
                tool = GmailMCPTool(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    input_schema=tool_def["input_schema"],
                    operation_type=tool_def["operation_type"]
                )
                self.tools[tool.name] = tool

            logger.info(f"Loaded {len(self.tools)} Gmail tools")

        except Exception as e:
            logger.error(f"Error loading Gmail tools: {e}")

    async def _load_gmail_resources(self):
        """Load Gmail data as MCP resources"""
        try:
            if not self._check_auth():
                return

            # Add Gmail profile resource
            profile_resource = GmailMCPResource(
                uri="gmail://profile",
                name="Gmail Profile",
                description="Gmail user profile and account information",
                mime_type="application/json"
            )
            self.resources[profile_resource.uri] = profile_resource

            # Add Gmail labels resource
            labels_resource = GmailMCPResource(
                uri="gmail://labels",
                name="Gmail Labels",
                description="Available Gmail labels and categories",
                mime_type="application/json"
            )
            self.resources[labels_resource.uri] = labels_resource

            # Add recent messages resource
            recent_resource = GmailMCPResource(
                uri="gmail://messages/recent",
                name="Recent Messages",
                description="Recent Gmail messages summary",
                mime_type="application/json"
            )
            self.resources[recent_resource.uri] = recent_resource

            logger.info(f"Loaded {len(self.resources)} Gmail resources")

        except Exception as e:
            logger.error(f"Error loading Gmail resources: {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available Gmail MCP tools"""
        if not self.is_running:
            await self.initialize()

        return [tool.to_dict() for tool in self.tools.values()]

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available Gmail MCP resources"""
        if not self.is_running:
            await self.initialize()

        return [resource.to_dict() for resource in self.resources.values()]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a Gmail MCP tool"""
        logger.info(f"Received call to Gmail tool: {name} with arguments: {arguments}")
        if not self.is_running:
            await self.initialize()
        logger.info(f"Calling Gmail tool: {name} with arguments: {arguments}")

        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")

        if not self._check_auth():
            raise ValueError("Gmail authentication not available")

        tool = self.tools[name]

        try:
            result = await self._execute_gmail_operation(tool, arguments)

            return [{
                "type": "text",
                "text": json.dumps(result, indent=2, default=str)
            }]

        except Exception as e:
            logger.error(f"Error executing Gmail tool '{name}': {e}")
            return [{
                "type": "text",
                "text": f"Error executing Gmail operation: {str(e)}"
            }]

    async def _execute_gmail_operation(self, tool: GmailMCPTool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual Gmail API operation"""
        operation_type = tool.operation_type

        if operation_type == "list_messages":
            return await self._list_messages(arguments)

        elif operation_type == "get_message":
            return await self._get_message(arguments["message_id"], arguments.get("format", "full"), arguments.get("metadata_headers"))

        elif operation_type == "send_message":
            return await self._send_message(arguments)

        elif operation_type == "search_messages":
            return await self._search_messages(arguments)

        elif operation_type == "list_labels":
            return await self._list_labels()

        elif operation_type == "get_profile":
            return await self._get_profile()

        elif operation_type == "modify_message":
            return await self._modify_message(arguments)

        elif operation_type == "get_thread":
            return await self._get_thread(arguments["thread_id"], arguments.get("format", "full"))

        else:
            raise ValueError(f"Unknown operation type: {operation_type}")

    async def _list_messages(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List Gmail messages"""
        try:
            query_params = {}

            if arguments.get("query"):
                query_params["q"] = arguments["query"]

            if arguments.get("label_ids"):
                query_params["labelIds"] = arguments["label_ids"]

            if arguments.get("max_results"):
                query_params["maxResults"] = arguments["max_results"]

            if arguments.get("page_token"):
                query_params["pageToken"] = arguments["page_token"]

            result = self.service.users().messages().list(userId='me', **query_params).execute()

            # Debug logging
            logger.debug(f"Gmail API list_messages raw result: {result}")
            logger.debug(f"Query params used: {query_params}")

            messages = result.get('messages', [])

            # Get basic info for each message
            message_summaries = []
            for msg in messages[:10]:  # Limit to first 10 for performance
                msg_detail = self.service.users().messages().get(
                    userId='me', id=msg['id'], format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}

                message_summaries.append({
                    "id": msg['id'],
                    "thread_id": msg.get('threadId'),
                    "from": headers.get('From'),
                    "to": headers.get('To'),
                    "subject": headers.get('Subject'),
                    "date": headers.get('Date'),
                    "labels": msg_detail.get('labelIds', [])
                })

            return {
                "operation": "list_messages",
                "success": True,
                "data": message_summaries,
                "count": len(message_summaries),
                "total_count": result.get('resultSizeEstimate', 0),
                "next_page_token": result.get('nextPageToken'),
                "parameters": arguments
            }

        except HttpError as e:
            logger.error(f"Gmail API error in list_messages: {e}")
            raise ValueError(f"Gmail API error: {e}")

    async def _get_message(self, message_id: str, format: str = "full", metadata_headers: List[str] = None) -> Dict[str, Any]:
        """Get a specific Gmail message"""
        try:
            query_params = {"userId": "me", "id": message_id, "format": format}

            if format == "metadata" and metadata_headers:
                query_params["metadataHeaders"] = metadata_headers

            message = self.service.users().messages().get(**query_params).execute()

            # Extract message content based on format
            result = {
                "operation": "get_message",
                "message_id": message_id,
                "success": True,
                "data": {
                    "id": message["id"],
                    "threadId": message.get("threadId"),
                    "labelIds": message.get("labelIds", []),
                    "snippet": message.get("snippet"),
                    "internalDate": message.get("internalDate")
                }
            }

            if format in ["full", "metadata"]:
                payload = message.get("payload", {})
                headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

                result["data"].update({
                    "payload": payload,
                    "headers": headers,
                    "from": headers.get("From"),
                    "to": headers.get("To"),
                    "subject": headers.get("Subject"),
                    "date": headers.get("Date")
                })

                if format == "full":
                    # Extract message body
                    body_content = self._extract_message_body(payload)
                    result["data"]["body"] = body_content

            return result

        except HttpError as e:
            logger.error(f"Gmail API error in get_message: {e}")
            raise ValueError(f"Gmail API error: {e}")

    def _extract_message_body(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract message body from Gmail API payload"""
        body_content = {"text": "", "html": ""}

        def extract_parts(part):
            mime_type = part.get("mimeType", "")

            if mime_type == "text/plain":
                body_data = part.get("body", {}).get("data")
                if body_data:
                    body_content["text"] = base64.urlsafe_b64decode(body_data).decode('utf-8')

            elif mime_type == "text/html":
                body_data = part.get("body", {}).get("data")
                if body_data:
                    body_content["html"] = base64.urlsafe_b64decode(body_data).decode('utf-8')

            elif "parts" in part:
                for subpart in part["parts"]:
                    extract_parts(subpart)

        if "parts" in payload:
            for part in payload["parts"]:
                extract_parts(part)
        else:
            extract_parts(payload)

        return body_content

    async def _send_message(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Send a Gmail message"""
        try:
            # Create message
            if arguments.get("html", False):
                message = MIMEText(arguments["body"], "html")
            else:
                message = MIMEText(arguments["body"], "plain")

            message["to"] = arguments["to"]
            message["subject"] = arguments["subject"]

            if arguments.get("cc"):
                message["cc"] = arguments["cc"]

            if arguments.get("bcc"):
                message["bcc"] = arguments["bcc"]

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            return {
                "operation": "send_message",
                "success": True,
                "data": {
                    "message_id": result["id"],
                    "thread_id": result.get("threadId"),
                    "to": arguments["to"],
                    "subject": arguments["subject"]
                }
            }

        except HttpError as e:
            logger.error(f"Gmail API error in send_message: {e}")
            raise ValueError(f"Gmail API error: {e}")

    async def _search_messages(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search Gmail messages"""
        try:
            query_params = {
                "userId": "me",
                "q": arguments["query"],
                "maxResults": arguments.get("max_results", 50)
            }

            if arguments.get("include_spam_trash"):
                query_params["includeSpamTrash"] = True

            result = self.service.users().messages().list(**query_params).execute()

            messages = result.get("messages", [])

            # Get details for found messages
            message_details = []
            for msg in messages:
                msg_detail = self.service.users().messages().get(
                    userId='me', id=msg['id'], format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}

                message_details.append({
                    "id": msg["id"],
                    "thread_id": msg.get("threadId"),
                    "snippet": msg_detail.get("snippet"),
                    "from": headers.get("From"),
                    "to": headers.get("To"),
                    "subject": headers.get("Subject"),
                    "date": headers.get("Date"),
                    "labels": msg_detail.get("labelIds", [])
                })

            return {
                "operation": "search_messages",
                "query": arguments["query"],
                "success": True,
                "data": message_details,
                "count": len(message_details),
                "total_estimate": result.get("resultSizeEstimate", 0)
            }

        except HttpError as e:
            logger.error(f"Gmail API error in search_messages: {e}")
            raise ValueError(f"Gmail API error: {e}")

    async def _list_labels(self) -> Dict[str, Any]:
        """List Gmail labels"""
        try:
            result = self.service.users().labels().list(userId='me').execute()
            labels = result.get("labels", [])

            return {
                "operation": "list_labels",
                "success": True,
                "data": labels,
                "count": len(labels)
            }

        except HttpError as e:
            logger.error(f"Gmail API error in list_labels: {e}")
            raise ValueError(f"Gmail API error: {e}")

    async def _get_profile(self) -> Dict[str, Any]:
        """Get Gmail profile"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()

            return {
                "operation": "get_profile",
                "success": True,
                "data": profile
            }

        except HttpError as e:
            logger.error(f"Gmail API error in get_profile: {e}")
            raise ValueError(f"Gmail API error: {e}")

    async def _modify_message(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Modify message labels"""
        try:
            message_id = arguments["message_id"]

            modify_request = {}
            if arguments.get("add_label_ids"):
                modify_request["addLabelIds"] = arguments["add_label_ids"]

            if arguments.get("remove_label_ids"):
                modify_request["removeLabelIds"] = arguments["remove_label_ids"]

            result = self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=modify_request
            ).execute()

            return {
                "operation": "modify_message",
                "message_id": message_id,
                "success": True,
                "data": result
            }

        except HttpError as e:
            logger.error(f"Gmail API error in modify_message: {e}")
            raise ValueError(f"Gmail API error: {e}")

    async def _get_thread(self, thread_id: str, format: str = "full") -> Dict[str, Any]:
        """Get Gmail thread"""
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format=format
            ).execute()

            return {
                "operation": "get_thread",
                "thread_id": thread_id,
                "success": True,
                "data": thread
            }

        except HttpError as e:
            logger.error(f"Gmail API error in get_thread: {e}")
            raise ValueError(f"Gmail API error: {e}")

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a Gmail resource"""
        if not self.is_running:
            await self.initialize()

        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' not found")

        if not self._check_auth():
            raise ValueError("Gmail authentication not available")

        try:
            if uri == "gmail://profile":
                profile = await self._get_profile()
                content = profile["data"]

            elif uri == "gmail://labels":
                labels = await self._list_labels()
                content = labels["data"]

            elif uri == "gmail://messages/recent":
                recent_messages = await self._list_messages({"max_results": 10})
                content = recent_messages["data"]

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
            logger.error(f"Error reading Gmail resource '{uri}': {e}")
            raise ValueError(f"Error reading resource: {str(e)}")

    def get_server_info(self) -> Dict[str, Any]:
        """Get Gmail MCP server information"""
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
            "resources_count": len(self.resources)
        }


# Singleton instance
gmail_mcp_server = GmailMCPServer()