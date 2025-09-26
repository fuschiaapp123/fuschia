"""
Gmail Mailbox Monitoring Service
Monitors Gmail inbox for new messages and triggers workflows based on intent classification
"""

import asyncio
import json
import logging
import os
import time
import hashlib
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

import structlog
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import sessionmaker

from app.db.postgres import AsyncSessionLocal, Base
from app.services.gmail_mcp_server import gmail_mcp_server
from app.services.intent_agent import create_intent_agent
from app.services.workflow_execution_service import WorkflowExecutionService
from app.services.template_service import template_service

logger = structlog.get_logger()


@dataclass
class EmailMessage:
    """Represents an email message for processing"""
    message_id: str
    thread_id: str
    subject: str
    sender: str
    recipient: str
    body_text: str
    body_html: str
    received_time: datetime
    labels: List[str]
    snippet: str


@dataclass
class MonitoringConfig:
    """Configuration for Gmail monitoring"""
    enabled: bool = False
    check_interval_seconds: int = 300  # 5 minutes default
    query_filter: str = "is:unread"  # Only unread emails by default
    max_messages_per_check: int = 10
    intent_confidence_threshold: float = 0.7
    auto_trigger_workflows: bool = True
    excluded_senders: List[str] = None
    included_labels: List[str] = None

    def __post_init__(self):
        if self.excluded_senders is None:
            self.excluded_senders = []
        if self.included_labels is None:
            self.included_labels = []


class GmailMonitorService:
    """Service for monitoring Gmail inbox and triggering workflows"""

    def __init__(self):
        self.logger = logger.bind(service="GmailMonitorService")
        self.workflow_execution_service = WorkflowExecutionService()
        self.intent_agent = None
        self.is_running = False
        self.monitoring_task = None
        self.processed_messages: Set[str] = set()  # Cache of processed message IDs
        self.config = MonitoringConfig()

    async def initialize(self):
        """Initialize the monitoring service"""
        try:
            self.logger.info("Initializing Gmail Monitor Service")

            # Initialize Gmail MCP server
            if not gmail_mcp_server.is_running:
                await gmail_mcp_server.initialize()

            # Initialize intent agent
            self.intent_agent = create_intent_agent()

            self.logger.info("Gmail Monitor Service initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize Gmail Monitor Service", error=str(e))
            raise

    async def start_monitoring(self, config: Optional[MonitoringConfig] = None):
        """Start monitoring Gmail inbox"""
        if config:
            self.config = config

        if not self.config.enabled:
            self.logger.warning("Gmail monitoring is disabled in configuration")
            return

        if self.is_running:
            self.logger.warning("Gmail monitoring is already running")
            return

        self.logger.info("Starting Gmail monitoring",
                        interval=self.config.check_interval_seconds,
                        query=self.config.query_filter)

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop monitoring Gmail inbox"""
        self.logger.info("Stopping Gmail monitoring")
        self.is_running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None

    async def _monitoring_loop(self):
        """Main monitoring loop that checks for new emails"""
        while self.is_running:
            try:
                await self._check_for_new_emails()
                await asyncio.sleep(self.config.check_interval_seconds)

            except asyncio.CancelledError:
                self.logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error("Error in monitoring loop", error=str(e))
                # Wait a bit before retrying to avoid spam
                await asyncio.sleep(60)

    async def _check_for_new_emails(self):
        """Check Gmail for new emails and process them"""
        try:
            self.logger.debug("Checking for new emails")

            # Get recent emails from Gmail
            messages = await self._fetch_recent_emails()

            if not messages:
                self.logger.debug("No new messages found")
                return

            self.logger.info(f"Found {len(messages)} new messages to process")

            # Process each message
            for message in messages:
                if message.message_id not in self.processed_messages:
                    await self._process_email_message(message)
                    self.processed_messages.add(message.message_id)

            # Clean up old processed messages (keep only last 1000)
            if len(self.processed_messages) > 1000:
                # Convert to list, sort by recent processing, keep last 1000
                # For simplicity, just clear and start fresh periodically
                self.processed_messages.clear()

        except Exception as e:
            self.logger.error("Error checking for new emails", error=str(e))

    async def _fetch_recent_emails(self) -> List[EmailMessage]:
        """Fetch recent emails from Gmail using MCP server"""
        try:
            # Use Gmail MCP server to list messages
            self.logger.debug("Fetching recent emails from Gmail")
            list_result = await gmail_mcp_server.call_tool("gmail_list_messages", {
                "query": self.config.query_filter,
                "max_results": self.config.max_messages_per_check
            })

            if not list_result or not list_result[0].get('text'):
                return []

            messages_data = json.loads(list_result[0]['text'])

            if not messages_data.get('success') or not messages_data.get('data'):
                return []

            email_messages = []

            # Get full content for each message
            for msg_summary in messages_data['data']:
                message_id = msg_summary.get('id')
                if not message_id:
                    continue

                # Get full message content
                full_message_result = await gmail_mcp_server.call_tool("gmail_get_message", {
                    "message_id": message_id,
                    "format": "full"
                })

                if full_message_result and full_message_result[0].get('text'):
                    full_message_data = json.loads(full_message_result[0]['text'])

                    if full_message_data.get('success'):
                        email_msg = self._parse_gmail_message(full_message_data['data'])
                        if email_msg and self._should_process_message(email_msg):
                            email_messages.append(email_msg)

            return email_messages

        except Exception as e:
            self.logger.error("Error fetching emails from Gmail", error=str(e))
            return []

    def _parse_gmail_message(self, gmail_data: Dict[str, Any]) -> Optional[EmailMessage]:
        """Parse Gmail API message data into EmailMessage object"""
        try:
            headers = {h['name']: h['value'] for h in gmail_data.get('payload', {}).get('headers', [])}

            # Extract text content
            body_text = ""
            body_html = ""

            payload = gmail_data.get('payload', {})
            if payload.get('parts'):
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                        body_text = self._decode_base64_content(part['body']['data'])
                    elif part.get('mimeType') == 'text/html' and part.get('body', {}).get('data'):
                        body_html = self._decode_base64_content(part['body']['data'])
            elif payload.get('body', {}).get('data'):
                if payload.get('mimeType') == 'text/plain':
                    body_text = self._decode_base64_content(payload['body']['data'])
                elif payload.get('mimeType') == 'text/html':
                    body_html = self._decode_base64_content(payload['body']['data'])

            # Parse received time
            received_time = datetime.fromtimestamp(int(gmail_data.get('internalDate', 0)) / 1000)

            return EmailMessage(
                message_id=gmail_data.get('id', ''),
                thread_id=gmail_data.get('threadId', ''),
                subject=headers.get('Subject', ''),
                sender=headers.get('From', ''),
                recipient=headers.get('To', ''),
                body_text=body_text,
                body_html=body_html,
                received_time=received_time,
                labels=gmail_data.get('labelIds', []),
                snippet=gmail_data.get('snippet', '')
            )

        except Exception as e:
            self.logger.error("Error parsing Gmail message", error=str(e))
            return None

    def _decode_base64_content(self, content: str) -> str:
        """Decode base64 URL-safe content"""
        try:
            import base64
            # Add padding if needed
            missing_padding = len(content) % 4
            if missing_padding:
                content += '=' * (4 - missing_padding)

            return base64.urlsafe_b64decode(content).decode('utf-8', errors='ignore')
        except Exception:
            return ""

    def _should_process_message(self, message: EmailMessage) -> bool:
        """Check if message should be processed based on filters"""
        # Check excluded senders
        for excluded_sender in self.config.excluded_senders:
            if excluded_sender.lower() in message.sender.lower():
                return False

        # Check included labels (if specified)
        if self.config.included_labels:
            has_included_label = any(label in message.labels for label in self.config.included_labels)
            if not has_included_label:
                return False

        # Skip very old messages (older than 1 hour)
        if message.received_time < datetime.now() - timedelta(hours=1):
            return False

        return True

    async def _process_email_message(self, message: EmailMessage):
        """Process a single email message with intent classification"""
        try:
            self.logger.info("Processing email message",
                           message_id=message.message_id,
                           subject=message.subject,
                           sender=message.sender)

            # Prepare message content for intent classification
            email_content = self._prepare_email_content(message)

            # Classify intent
            intent_result = await self._classify_email_intent(email_content, message)

            if not intent_result or not intent_result.get('requires_workflow'):
                self.logger.info("Email does not require workflow triggering",
                               message_id=message.message_id,
                               intent=intent_result.get('detected_intent') if intent_result else 'unknown')
                return

            # Check confidence threshold
            confidence = intent_result.get('confidence', 0.0)
            if confidence < self.config.intent_confidence_threshold:
                self.logger.info("Intent confidence below threshold",
                               message_id=message.message_id,
                               confidence=confidence,
                               threshold=self.config.intent_confidence_threshold)
                return

            # Trigger workflow if auto-triggering is enabled
            if self.config.auto_trigger_workflows:
                await self._trigger_workflow_from_intent(message, intent_result)
            else:
                self.logger.info("Auto-triggering disabled, workflow not triggered",
                               message_id=message.message_id,
                               workflow_template_id=intent_result.get('workflow_template_id'))

        except Exception as e:
            self.logger.error("Error processing email message",
                            message_id=message.message_id,
                            error=str(e))

    def _prepare_email_content(self, message: EmailMessage) -> str:
        """Prepare email content for intent classification"""
        # Combine subject and body for analysis
        content_parts = []

        if message.subject:
            content_parts.append(f"Subject: {message.subject}")

        if message.body_text:
            content_parts.append(f"Body: {message.body_text[:1000]}")  # Limit body length
        elif message.snippet:
            content_parts.append(f"Body: {message.snippet}")

        if message.sender:
            content_parts.append(f"From: {message.sender}")

        return "\n".join(content_parts)

    async def _classify_email_intent(self, email_content: str, message: EmailMessage) -> Optional[Dict[str, Any]]:
        """Classify email intent using the intent agent"""
        try:
            if not self.intent_agent:
                self.logger.error("Intent agent not initialized")
                return None

            # Use intent classification with email context
            intent_result = await self.intent_agent.detect_intent_with_context(
                message=email_content,
                user_role="email_user",
                current_module="email_monitor",
                current_tab="inbox"
            )

            self.logger.info("Email intent classified",
                           message_id=message.message_id,
                           intent=intent_result.get('detected_intent'),
                           confidence=intent_result.get('confidence'),
                           workflow_template_id=intent_result.get('workflow_template_id'))

            return intent_result

        except Exception as e:
            self.logger.error("Error classifying email intent",
                            message_id=message.message_id,
                            error=str(e))
            return None

    async def _trigger_workflow_from_intent(self, message: EmailMessage, intent_result: Dict[str, Any]):
        """Trigger a workflow based on the classified intent"""
        try:
            workflow_template_id = intent_result.get('workflow_template_id')
            if not workflow_template_id:
                self.logger.warning("No workflow template ID in intent result",
                                  message_id=message.message_id)
                return

            # Prepare execution context with email data
            execution_context = {
                "trigger_source": "email_monitor",
                "email_message_id": message.message_id,
                "email_subject": message.subject,
                "email_sender": message.sender,
                "email_recipient": message.recipient,
                "email_received_time": message.received_time.isoformat(),
                "intent_classification": intent_result,
                "email_content_snippet": message.snippet
            }

            # Create workflow execution
            execution = await self.workflow_execution_service.create_execution(
                workflow_template_id=workflow_template_id,
                initiated_by="gmail_monitor",
                execution_context=execution_context,
                priority=2  # Email-triggered workflows get higher priority
            )

            self.logger.info("Workflow triggered from email",
                           message_id=message.message_id,
                           workflow_template_id=workflow_template_id,
                           execution_id=execution.id,
                           intent=intent_result.get('detected_intent'))

        except Exception as e:
            self.logger.error("Error triggering workflow from email",
                            message_id=message.message_id,
                            error=str(e))

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics"""
        return {
            "is_running": self.is_running,
            "config": {
                "enabled": self.config.enabled,
                "check_interval_seconds": self.config.check_interval_seconds,
                "query_filter": self.config.query_filter,
                "max_messages_per_check": self.config.max_messages_per_check,
                "intent_confidence_threshold": self.config.intent_confidence_threshold,
                "auto_trigger_workflows": self.config.auto_trigger_workflows
            },
            "processed_messages_count": len(self.processed_messages),
            "gmail_server_status": gmail_mcp_server.is_running,
            "intent_agent_available": self.intent_agent is not None
        }

    async def update_config(self, new_config: Dict[str, Any]):
        """Update monitoring configuration"""
        try:
            # Update configuration
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            self.logger.info("Monitoring configuration updated", config=new_config)

            # Restart monitoring if it was running
            if self.is_running:
                await self.stop_monitoring()
                await self.start_monitoring()

        except Exception as e:
            self.logger.error("Error updating monitoring configuration", error=str(e))
            raise


# Global instance
gmail_monitor_service = GmailMonitorService()