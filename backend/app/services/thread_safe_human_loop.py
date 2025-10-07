"""
Thread-safe human-in-the-loop functionality for dspy.React tools
Resolves async/sync boundary issues with WebSocket communication from daemon threads
"""

import threading
import time
import uuid
from typing import Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import structlog
from dataclasses import dataclass
from enum import Enum

logger = structlog.get_logger()


class HumanRequestType(Enum):
    QUESTION = "question"
    APPROVAL = "approval" 
    INFORMATION = "information"
    CLARIFICATION = "clarification"
    DECISION = "decision"


@dataclass
class HumanRequest:
    request_id: str
    request_type: HumanRequestType
    execution_id: str
    task_id: str
    agent_id: str
    prompt: str
    context: Dict[str, Any]
    timeout_seconds: int = 300
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class ThreadSafeHumanLoop:
    """
    Thread-safe human-in-the-loop implementation that works with dspy.React tools
    Uses threading events and queue-based communication to avoid blocking async operations
    """
    
    def __init__(self):
        self.pending_requests: Dict[str, HumanRequest] = {}
        self.response_events: Dict[str, threading.Event] = {}
        self.responses: Dict[str, str] = {}
        self.lock = threading.RLock()
        self.websocket_manager = None  # Will be injected
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="human-loop")
        
    def set_websocket_manager(self, websocket_manager):
        """Inject websocket manager dependency"""
        self.websocket_manager = websocket_manager
        
    def create_human_request(self, 
                           request_type: HumanRequestType,
                           execution_id: str,
                           task_id: str,
                           agent_id: str,
                           prompt: str,
                           context: Dict[str, Any] = None,
                           timeout_seconds: int = 300) -> str:
        """Create a new human interaction request"""
        
        request_id = str(uuid.uuid4())
        
        request = HumanRequest(
            request_id=request_id,
            request_type=request_type,
            execution_id=execution_id,
            task_id=task_id,
            agent_id=agent_id,
            prompt=prompt,
            context=context or {},
            timeout_seconds=timeout_seconds
        )
        
        with self.lock:
            self.pending_requests[request_id] = request
            self.response_events[request_id] = threading.Event()
            
        logger.info(
            "Created human interaction request",
            request_id=request_id,
            request_type=request_type.value,
            execution_id=execution_id,
            timeout_seconds=timeout_seconds
        )
        
        return request_id
    
    def wait_for_response(self, request_id: str) -> str:
        """
        Wait for human response using threading events (non-blocking for async operations)
        This is the key method that makes dspy.React tools work with WebSockets
        """
        
        if request_id not in self.pending_requests:
            raise ValueError(f"Request {request_id} not found")
            
        request = self.pending_requests[request_id]
        event = self.response_events[request_id]
        
        logger.info(
            "Waiting for human response",
            request_id=request_id,
            timeout_seconds=request.timeout_seconds
        )
        
        # Send request via WebSocket in background thread to avoid blocking
        self._send_websocket_request_async(request)
        
        # Wait for response using a dedicated thread to avoid blocking the async event loop
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        
        def wait_for_event():
            """Wait for the event in a separate thread"""
            return event.wait(timeout=request.timeout_seconds)
        
        # Use ThreadPoolExecutor to run the blocking wait in a separate thread
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="human-wait") as executor:
            try:
                future = executor.submit(wait_for_event)
                response_received = future.result(timeout=request.timeout_seconds + 1)  # Small buffer
            except FutureTimeoutError:
                response_received = False
        
        with self.lock:
            if response_received and request_id in self.responses:
                response = self.responses.pop(request_id)
                self._cleanup_request(request_id)
                
                logger.info(
                    "Human response received",
                    request_id=request_id,
                    response_length=len(response)
                )
                
                return response
            else:
                # Timeout or no response
                self._cleanup_request(request_id)
                
                logger.warning(
                    "Human response timeout",
                    request_id=request_id,
                    timeout_seconds=request.timeout_seconds
                )
                
                return f"[TIMEOUT] No human response received within {request.timeout_seconds} seconds. Request: {request.prompt[:100]}..."
    
    def submit_response(self, request_id: str, response: str) -> bool:
        """Submit a human response (called by WebSocket endpoint)"""
        
        with self.lock:
            if request_id not in self.pending_requests:
                logger.warning(f"Response submitted for unknown request: {request_id}")
                return False
                
            self.responses[request_id] = response
            
            # Signal the waiting thread
            if request_id in self.response_events:
                self.response_events[request_id].set()
                
            logger.info(
                "Human response submitted",
                request_id=request_id,
                response_length=len(response)
            )
            
            return True
    
    def _send_websocket_request_async(self, request: HumanRequest):
        """Send WebSocket request in background thread to avoid blocking"""
        
        def send_request():
            try:
                if not self.websocket_manager:
                    logger.error("WebSocket manager not configured")
                    return
                    
                # Format message based on request type
                formatted_message = self._format_request_message(request)
                
                # Queue the message for WebSocket delivery
                self.websocket_manager.queue_chat_message_from_thread(
                    execution_id=request.execution_id,
                    message_content=formatted_message,
                    agent_id=request.agent_id,
                    agent_name="Human-in-Loop Agent",
                    task_id=request.task_id,
                    task_name="Human Interaction Required",
                    message_type='user_request',
                    requires_response=True,
                    metadata={
                        'request_id': request.request_id,
                        'request_type': request.request_type.value,
                        'requires_user_response': True,
                        'timeout_seconds': request.timeout_seconds
                    }
                )
                
                logger.info(
                    "WebSocket request queued",
                    request_id=request.request_id,
                    execution_id=request.execution_id
                )
                
            except Exception as e:
                logger.error(
                    "Failed to send WebSocket request",
                    request_id=request.request_id,
                    error=str(e)
                )
                
                # Signal failure to waiting thread
                with self.lock:
                    if request.request_id in self.responses:
                        self.responses[request.request_id] = f"[ERROR] Failed to send request: {str(e)}"
                    if request.request_id in self.response_events:
                        self.response_events[request.request_id].set()
        
        # Execute in background thread
        self.executor.submit(send_request)
    
    def _format_request_message(self, request: HumanRequest) -> str:
        """Format human interaction request for WebSocket display"""
        
        emoji_map = {
            HumanRequestType.QUESTION: "❓",
            HumanRequestType.APPROVAL: "✋", 
            HumanRequestType.INFORMATION: "📝",
            HumanRequestType.CLARIFICATION: "🤔",
            HumanRequestType.DECISION: "⚖️"
        }
        
        emoji = emoji_map.get(request.request_type, "🤖")
        type_name = request.request_type.value.title()
        
        message = f"{emoji} **{type_name} Required**\n\n"
        message += f"{request.prompt}\n\n"
        
        if request.context:
            message += "**Context:**\n"
            for key, value in request.context.items():
                message += f"• **{key}**: {value}\n"
            message += "\n"
            
        message += f"*Please respond in the chat. Request ID: `{request.request_id[:8]}...`*"
        
        return message
        
    def _cleanup_request(self, request_id: str):
        """Clean up request resources"""
        with self.lock:
            self.pending_requests.pop(request_id, None)
            self.response_events.pop(request_id, None)
            self.responses.pop(request_id, None)
    
    def get_pending_requests(self, execution_id: str = None) -> Dict[str, HumanRequest]:
        """Get pending requests, optionally filtered by execution_id"""
        with self.lock:
            if execution_id:
                return {
                    req_id: req for req_id, req in self.pending_requests.items()
                    if req.execution_id == execution_id
                }
            return dict(self.pending_requests)
    
    def cleanup_expired_requests(self, max_age_seconds: int = 3600):
        """Clean up expired requests (older than max_age_seconds)"""
        current_time = time.time()
        expired_requests = []
        
        with self.lock:
            for req_id, request in self.pending_requests.items():
                if current_time - request.created_at > max_age_seconds:
                    expired_requests.append(req_id)
                    
            for req_id in expired_requests:
                logger.info(f"Cleaning up expired request: {req_id}")
                self._cleanup_request(req_id)
                
        return len(expired_requests)
    
    def shutdown(self):
        """Shutdown the thread pool executor"""
        self.executor.shutdown(wait=True)


# Global instance
thread_safe_human_loop = ThreadSafeHumanLoop()


def create_thread_safe_human_tools(execution_id: str, task_id: str, agent_id: str) -> Dict[str, Callable]:
    """
    Create thread-safe human-in-the-loop tools for dspy.React
    These tools work properly with WebSockets from daemon threads
    """
    
    def ask_human_question(question: str) -> str:
        """Ask human a question and wait for response"""
        request_id = thread_safe_human_loop.create_human_request(
            request_type=HumanRequestType.QUESTION,
            execution_id=execution_id,
            task_id=task_id,
            agent_id=agent_id,
            prompt=f"Question: {question}",
            context={"type": "question"},
            timeout_seconds=300
        )
        
        response = thread_safe_human_loop.wait_for_response(request_id)
        return f"Human answered: {response}"
    
    def request_human_approval(action_description: str) -> str:
        """Request human approval for an action"""
        request_id = thread_safe_human_loop.create_human_request(
            request_type=HumanRequestType.APPROVAL,
            execution_id=execution_id,
            task_id=task_id,
            agent_id=agent_id,
            prompt=f"Please approve this action: {action_description}\n\nRespond with 'approve', 'reject', or provide specific instructions.",
            context={"type": "approval", "action": action_description},
            timeout_seconds=300
        )
        
        response = thread_safe_human_loop.wait_for_response(request_id)
        
        # Process approval response
        if "[TIMEOUT]" in response or "[ERROR]" in response:
            return response
            
        response_lower = response.lower()
        if 'approve' in response_lower or 'yes' in response_lower:
            return f"APPROVED: {response}"
        elif 'reject' in response_lower or 'no' in response_lower:
            return f"REJECTED: {response}"
        else:
            return f"USER_INSTRUCTIONS: {response}"
    
    def request_missing_information(info_type: str, context_info: str = "") -> str:
        """Request missing information from human"""
        prompt = f"I need additional information: {info_type}"
        if context_info:
            prompt += f"\n\nContext: {context_info}"
            
        request_id = thread_safe_human_loop.create_human_request(
            request_type=HumanRequestType.INFORMATION,
            execution_id=execution_id,
            task_id=task_id,
            agent_id=agent_id,
            prompt=prompt,
            context={"type": "information", "info_type": info_type, "context": context_info},
            timeout_seconds=300
        )
        
        response = thread_safe_human_loop.wait_for_response(request_id)
        return f"Human provided {info_type}: {response}"
    
    def clarify_user_intent(ambiguous_request: str) -> str:
        """Ask human to clarify ambiguous request"""
        request_id = thread_safe_human_loop.create_human_request(
            request_type=HumanRequestType.CLARIFICATION,
            execution_id=execution_id,
            task_id=task_id,
            agent_id=agent_id,
            prompt=f"I need clarification on this request: {ambiguous_request}\n\nPlease provide more specific details about what you want me to do.",
            context={"type": "clarification", "original_request": ambiguous_request},
            timeout_seconds=300
        )
        
        response = thread_safe_human_loop.wait_for_response(request_id)
        return f"Human clarified: {response}"
    
    def request_human_decision(options: str) -> str:
        """Ask human to make a decision between options"""
        request_id = thread_safe_human_loop.create_human_request(
            request_type=HumanRequestType.DECISION,
            execution_id=execution_id,
            task_id=task_id,
            agent_id=agent_id,
            prompt=f"Please choose from these options:\n\n{options}\n\nWhich option would you like me to proceed with?",
            context={"type": "decision", "options": options},
            timeout_seconds=300
        )
        
        response = thread_safe_human_loop.wait_for_response(request_id)
        return f"Human decided: {response}"
    
    return {
        "ask_human_question": ask_human_question,
        "request_human_approval": request_human_approval,
        "request_missing_information": request_missing_information,
        "clarify_user_intent": clarify_user_intent,
        "request_human_decision": request_human_decision
    }