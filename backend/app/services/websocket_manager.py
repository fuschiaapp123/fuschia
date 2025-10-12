import asyncio
import json
import queue
import threading
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import structlog
from datetime import datetime

logger = structlog.get_logger()

class WebSocketManager:
    """Manages WebSocket connections for real-time task updates"""
    
    def __init__(self):
        # Store active connections by user/session
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store execution-to-user mappings
        self.execution_users: Dict[str, str] = {}
        # Store pending user response requests: {request_id: {execution_id, task_id, question, timeout}}
        self.pending_responses: Dict[str, Dict[str, Any]] = {}
        # Store user responses: {request_id: response}
        self.user_responses: Dict[str, str] = {}
        # Thread-safe message queue for daemon thread communication
        self.message_queue: queue.Queue = queue.Queue()
        # Flag to control background processing
        self._processing_messages = False
        # Store task reference to prevent garbage collection
        self._message_processing_task = None
        # Track last activity for health monitoring
        self._last_queue_activity = None
        
    def queue_chat_message_from_thread(self, execution_id: str, message_content: str, agent_id: str, agent_name: str, task_id: str = None, task_name: str = None, message_type: str = "agent_message", requires_response: bool = False, metadata: Dict[str, Any] = None):
        """Queue a chat message from a daemon thread to be sent via WebSocket"""
        message_data = {
            'type': 'chat_message',
            'execution_id': execution_id,
            'message_content': message_content,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'task_id': task_id,
            'task_name': task_name,
            'message_type': message_type,
            'requires_response': requires_response,
            'metadata': metadata or {}
        }
        
        try:
            # Check if message processing is running and try to restart if needed
            health = self.get_task_health()
            logger.info("Message processing health check", 
                       health=health, 
                       execution_id=execution_id, 
                       message_type=message_type)
            
            if health['status'] not in ['running']:
                logger.warning("Message processing task is not running when queueing message", 
                             health=health, execution_id=execution_id, message_type=message_type)
                
                # Try to restart message processing in background
                try:
                    asyncio.create_task(self.ensure_message_processing_running())
                    logger.info("Initiated message processing restart attempt")
                except Exception as restart_error:
                    logger.error("Failed to initiate message processing restart", error=str(restart_error))
            
            self.message_queue.put_nowait(message_data)
            logger.info("Message queued for WebSocket delivery", 
                       execution_id=execution_id,
                       message_type=message_type,
                       queue_size=self.message_queue.qsize(),
                       processing_status=health['status'])
        except queue.Full:
            logger.error("Message queue is full, dropping message", 
                        execution_id=execution_id,
                        message_type=message_type)
    
    async def start_message_processing(self):
        """Start the background message processing task"""
        if not self._processing_messages:
            self._processing_messages = True
            # Store task reference to prevent garbage collection
            self._message_processing_task = asyncio.create_task(self._process_message_queue())
            
            # Add callback to handle task completion/failure
            self._message_processing_task.add_done_callback(self._on_task_done)
            
            logger.info("Started WebSocket message processing", 
                       task_id=id(self._message_processing_task))
    
    async def stop_message_processing(self):
        """Stop the background message processing"""
        self._processing_messages = False
        
        # Cancel the task if it exists
        if self._message_processing_task and not self._message_processing_task.done():
            self._message_processing_task.cancel()
            try:
                await self._message_processing_task
            except asyncio.CancelledError:
                logger.info("Message processing task cancelled successfully")
        
        self._message_processing_task = None
        logger.info("Stopped WebSocket message processing")
    
    async def _process_message_queue(self):
        """Background task to process queued messages from daemon threads"""
        logger.info("Starting message queue processing task")
        print("====> MESSAGE PROCESSING TASK STARTED <====")
        
        last_health_check = datetime.utcnow()
        health_check_interval = 30  # seconds
        
        while self._processing_messages:
            # print(f"----> Processing message queue, current size: {self.message_queue.qsize()}")  

            try:
                # Periodic health check to ensure we're still running
                current_time = datetime.utcnow()
                if (current_time - last_health_check).total_seconds() > health_check_interval:
                    # logger.debug("Message processing health check", 
                    #          queue_size=self.message_queue.qsize(),
                    #          processing_flag=self._processing_messages)
                    last_health_check = current_time
                # Check for messages with a short timeout
                try:
                    message_data = self.message_queue.get_nowait()
                    logger.info("Processing queued message", 
                               message_type=message_data.get('type'),
                               execution_id=message_data.get('execution_id'),
                               queue_size=self.message_queue.qsize())
                except queue.Empty:
                    # No messages, sleep briefly and continue
                    await asyncio.sleep(0.1)
                    continue
                
                # Process the message
                if message_data['type'] == 'chat_message':
                    try:
                        await self.send_chat_message(
                            execution_id=message_data['execution_id'],
                            message_content=message_data['message_content'],
                            agent_id=message_data['agent_id'],
                            agent_name=message_data['agent_name'],
                            task_id=message_data['task_id'],
                            task_name=message_data['task_name'],
                            message_type=message_data['message_type'],
                            requires_response=message_data['requires_response'],
                            metadata=message_data['metadata']
                        )
                        logger.info("Successfully processed queued message", 
                                   execution_id=message_data['execution_id'],
                                   message_type=message_data['message_type'])
                    except Exception as send_error:
                        logger.error("Failed to send queued message", 
                                   execution_id=message_data.get('execution_id'),
                                   message_type=message_data.get('message_type'),
                                   error=str(send_error),
                                   error_type=type(send_error).__name__)
                else:
                    logger.warning("Unknown message type in queue", 
                                 message_type=message_data.get('type'),
                                 execution_id=message_data.get('execution_id'))
                
                # Note: Removed task_done() call as it's not needed with get_nowait()
                
            except asyncio.CancelledError:
                logger.info("Message queue processing task was cancelled")
                break
            except Exception as e:
                logger.error("Unexpected error in message queue processing", error=str(e))
                # Continue processing despite errors
                await asyncio.sleep(0.1)
        
        logger.info("Message queue processing task ended")
        print("====> MESSAGE PROCESSING TASK ENDED <====")
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        # Limit connections per user to prevent accumulation
        MAX_CONNECTIONS_PER_USER = 2
        
        # If user already has max connections, close the oldest ones
        if len(self.active_connections[user_id]) >= MAX_CONNECTIONS_PER_USER:
            logger.warning("User has too many connections, closing oldest ones", 
                         user_id=user_id, 
                         current_connections=len(self.active_connections[user_id]))
            
            # Close oldest connections (keep only the most recent one)
            connections_to_close = self.active_connections[user_id][:-1]
            for old_websocket in connections_to_close:
                try:
                    await old_websocket.close(code=1008, reason="Too many connections")
                    logger.info("Closed old WebSocket connection", user_id=user_id)
                except Exception as e:
                    logger.error("Error closing old WebSocket", user_id=user_id, error=str(e))
            
            # Keep only the most recent connection
            self.active_connections[user_id] = self.active_connections[user_id][-1:]
        
        self.active_connections[user_id].append(websocket)
        logger.info("WebSocket connected", user_id=user_id, 
                   total_connections=len(self.active_connections[user_id]))
        
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            # Remove the specific websocket
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info("WebSocket removed from active connections", user_id=user_id,
                           remaining_connections=len(self.active_connections[user_id]))
            else:
                logger.warning("WebSocket not found in active connections during disconnect", 
                             user_id=user_id)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                logger.info("All WebSocket connections closed for user", user_id=user_id)
        else:
            logger.warning("User not found in active connections during disconnect", user_id=user_id)
                
        logger.info("WebSocket disconnected", user_id=user_id)
    
    async def force_disconnect_user(self, user_id: str):
        """Force disconnect all WebSocket connections for a user"""
        if user_id not in self.active_connections:
            logger.info("No connections to force disconnect", user_id=user_id)
            return
        
        connections = self.active_connections[user_id][:]  # Make a copy
        logger.info("Force disconnecting all connections", user_id=user_id, count=len(connections))
        
        for websocket in connections:
            try:
                await websocket.close(code=1000, reason="Force disconnect")
                logger.info("Force closed WebSocket connection", user_id=user_id)
            except Exception as e:
                logger.error("Error force closing WebSocket", user_id=user_id, error=str(e))
        
        # Clear the connections list
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info("Cleared all connections for user", user_id=user_id)
    
    def register_execution(self, execution_id: str, user_id: str):
        """Register which user initiated a workflow execution"""
        self.execution_users[execution_id] = user_id
        logger.info("Registered execution", execution_id=execution_id, user_id=user_id, 
                   active_connections=list(self.active_connections.keys()))
    
    def update_execution_user(self, execution_id: str, new_user_id: str):
        """Update the user ID for an existing execution (useful for session reconnects)"""
        if execution_id in self.execution_users:
            old_user_id = self.execution_users[execution_id]
            self.execution_users[execution_id] = new_user_id
            logger.info("Updated execution user mapping", 
                       execution_id=execution_id, 
                       old_user_id=old_user_id, 
                       new_user_id=new_user_id)
            return True
        return False
    
    def find_execution_for_user(self, old_user_id: str) -> List[str]:
        """Find all executions that were registered to a specific user"""
        return [exec_id for exec_id, user_id in self.execution_users.items() if user_id == old_user_id]
        
    async def send_task_result(self, execution_id: str, task_result: Dict[str, Any]):
        """Send task result to the user who initiated the execution"""
        user_id = self.execution_users.get(execution_id)
        logger.info("Attempting to send task result", 
                   execution_id=execution_id, 
                   user_id=user_id,
                   task_result=task_result,
                   has_user_connections=user_id in self.active_connections if user_id else False,
                   active_connections=list(self.active_connections.keys()))
        
        if not user_id:
            logger.warning("No user ID found for execution", execution_id=execution_id)
            return
            
        if user_id not in self.active_connections:
            logger.warning("User has no active WebSocket connections", user_id=user_id, execution_id=execution_id)
            return
            
        # Format message for chat interface
        message = self._format_task_result_message(task_result)
        
        # Send to all user's connections
        connections_to_remove = []
        for websocket in self.active_connections[user_id]:
            try:
                logger.info("Sending WebSocket message", user_id=user_id, message_type=message.get('type'))
                await websocket.send_text(json.dumps(message))
                logger.info("WebSocket message sent successfully", user_id=user_id)
            except Exception as e:
                logger.error("Failed to send WebSocket message", 
                           user_id=user_id, error=str(e))
                connections_to_remove.append(websocket)
        
        # Clean up broken connections
        for websocket in connections_to_remove:
            await self.disconnect(websocket, user_id)
    
    async def send_execution_update(self, execution_id: str, update: Dict[str, Any]):
        """Send general execution updates"""
        user_id = self.execution_users.get(execution_id)
        logger.info("Attempting to send execution update", 
                   execution_id=execution_id, 
                   user_id=user_id,
                   update=update,
                   has_user_connections=user_id in self.active_connections if user_id else False)
        
        if not user_id:
            logger.warning("No user ID found for execution update", execution_id=execution_id)
            return
            
        if user_id not in self.active_connections:
            logger.warning("User has no active connections for execution update", user_id=user_id)
            return
            
        message = {
            'type': 'execution_update',
            'execution_id': execution_id,
            'data': update,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        connections_to_remove = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error("Failed to send execution update", 
                           user_id=user_id, error=str(e))
                connections_to_remove.append(websocket)
        
        for websocket in connections_to_remove:
            await self.disconnect(websocket, user_id)
    
    async def send_chat_message(self, execution_id: str, message_content: str, agent_id: str, agent_name: str, task_id: str = None, task_name: str = None, message_type: str = "agent_message", requires_response: bool = False, metadata: Dict[str, Any] = None):
        """Send a chat message from an agent to the user"""
        user_id = self.execution_users.get(execution_id)
        logger.info("Attempting to send chat message", 
                   execution_id=execution_id, 
                   user_id=user_id,
                   agent_id=agent_id,
                   message_type=message_type,
                   has_user_connections=user_id in self.active_connections if user_id else False)
        
        if not user_id:
            logger.warning("No user ID found for chat message", execution_id=execution_id)
            return
            
        if user_id not in self.active_connections:
            logger.warning("User has no active connections for chat message", 
                          user_id=user_id,
                          active_connections=list(self.active_connections.keys()))
            
            # Fallback: Try to send to any connected user (for development/testing)
            if self.active_connections:
                fallback_user = list(self.active_connections.keys())[0]
                logger.info("EXECUTING FALLBACK: Attempting fallback to connected user", 
                           original_user=user_id, 
                           fallback_user=fallback_user,
                           execution_id=execution_id)
                
                # Update the execution mapping to the connected user
                update_success = self.update_execution_user(execution_id, fallback_user)
                logger.info("Fallback execution user update result", 
                           success=update_success,
                           execution_id=execution_id,
                           new_user=fallback_user)
                user_id = fallback_user
            else:
                logger.error("No active connections available for fallback", 
                            active_connections_count=len(self.active_connections))
                return
        
        # Format message for chat interface using execution_update format for frontend compatibility
        # Match exact ExecutionUpdate interface from frontend
        message = {
            'type': 'execution_update',
            'execution_id': execution_id,
            'data': {
                'status': 'running',
                'message': message_content
                # Only include fields that match the frontend ExecutionUpdate interface
                # Additional metadata can be included in root level if needed
            },
            'timestamp': datetime.utcnow().isoformat()
            # Store additional info in root level, not in data object
            # 'agent_id': agent_id,
            # 'agent_name': agent_name,
            # 'task_id': task_id,
            # 'message_type': message_type,
            # 'requires_response': requires_response,
            # 'metadata': metadata or {}
        }
        
        connections_to_remove = []
        for websocket in self.active_connections[user_id]:
            try:
                logger.info("Sending chat message via WebSocket", 
                           user_id=user_id, 
                           message_type=message_type,
                           message_content=message_content[:100] + "..." if len(message_content) > 100 else message_content)
                
                # Debug: Log the exact message being sent
                logger.info("WebSocket message payload", 
                           user_id=user_id,
                           message_type=message['type'],
                           execution_id=message['execution_id'],
                           data_status=message['data']['status'],
                           data_message_length=len(message['data']['message']),
                           timestamp=message['timestamp'])
                
                await websocket.send_text(json.dumps(message))
                logger.info("Chat message sent successfully via WebSocket", user_id=user_id)
            except Exception as e:
                logger.error("Failed to send chat message via WebSocket", 
                           user_id=user_id, error=str(e))
                connections_to_remove.append(websocket)
        
        for websocket in connections_to_remove:
            await self.disconnect(websocket, user_id)
    
    async def send_task_result_as_agent_thought(
        self, 
        execution_id: str, 
        task_result: Dict[str, Any],
        agent_name: str,
        workflow_name: str
    ):
        """Send task result as an agent thought to the monitoring console"""
        user_id = self.execution_users.get(execution_id)
        logger.info("Attempting to send task result as agent thought", 
                   execution_id=execution_id, 
                   user_id=user_id,
                   task_result=task_result,
                   has_user_connections=user_id in self.active_connections if user_id else False,
                   active_connections=list(self.active_connections.keys()))
        
        if not user_id:
            logger.warning("No user ID found for execution", execution_id=execution_id)
            return
            
        if user_id not in self.active_connections:
            logger.warning("User has no active WebSocket connections", user_id=user_id, execution_id=execution_id)
            return

        # Convert task result to agent thought format
        task_id = task_result.get('task_id', 'Unknown')
        status = task_result.get('status', 'Unknown')
        agent_id = task_result.get('agent_id', 'Unknown Agent')
        execution_time = task_result.get('execution_time')

        # Determine thought type and message based on task status
        if status in ['completed', 'COMPLETED']:
            thought_type = 'observation'
            results = task_result.get('results', {})
            message = f"Task '{task_id}' completed successfully"
            if execution_time:
                message += f" in {execution_time:.2f}s"
            if results and isinstance(results, dict):
                if results.get('success'):
                    message += f". Result: {results.get('execution_summary', 'Task executed successfully')}"
        elif status in ['failed', 'FAILED']:
            thought_type = 'error'
            error = task_result.get('error', 'Unknown error')
            message = f"Task '{task_id}' failed: {error}"
        elif status in ['waiting_approval', 'WAITING_APPROVAL']:
            thought_type = 'decision'
            message = f"Task '{task_id}' requires human approval to proceed"
        else:
            thought_type = 'observation'
            message = f"Task '{task_id}' status updated to: {status}"

        # Create metadata
        metadata = {
            'task_id': task_id,
            'status': status,
            'agent_id': agent_id,
            'execution_time': execution_time,
            'task_results': task_result.get('results', {})
        }

        # Send as agent thought
        await self.send_agent_thought(
            user_id=user_id,
            agent_id=agent_id,
            agent_name=agent_name,
            workflow_id=execution_id,
            workflow_name=workflow_name,
            thought_type=thought_type,
            message=message,
            metadata=metadata
        )

    async def send_agent_thought(
        self, 
        user_id: str,
        agent_id: str,
        agent_name: str,
        workflow_id: str,
        workflow_name: str,
        thought_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Send agent thought/action message to user's WebSocket connections"""
        logger.info("Attempting to send agent thought", 
                   user_id=user_id,
                   agent_id=agent_id,
                   thought_type=thought_type,
                   has_user_connections=user_id in self.active_connections)
        
        if user_id not in self.active_connections:
            logger.warning("User has no active connections for agent thought", user_id=user_id)
            return
            
        thought_message = {
            'type': 'agent_thought',
            'id': f"thought-{datetime.utcnow().timestamp()}-{agent_id}",
            'timestamp': datetime.utcnow().isoformat(),
            'agentId': agent_id,
            'agentName': agent_name,
            'workflowId': workflow_id,
            'workflowName': workflow_name,
            'thoughtType': thought_type,
            'message': message,
            'metadata': metadata or {}
        }
        
        connections_to_remove = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(json.dumps(thought_message))
                logger.info("Agent thought sent successfully", user_id=user_id, agent_id=agent_id)
            except Exception as e:
                logger.error("Failed to send agent thought", 
                           user_id=user_id, agent_id=agent_id, error=str(e))
                connections_to_remove.append(websocket)
        
        for websocket in connections_to_remove:
            await self.disconnect(websocket, user_id)
            
    async def broadcast_agent_thought(
        self,
        agent_id: str,
        agent_name: str,
        workflow_id: str,
        workflow_name: str,
        thought_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Broadcast agent thought to all connected users (for system-wide visibility)"""
        logger.info("Broadcasting agent thought to all users", 
                   agent_id=agent_id,
                   thought_type=thought_type,
                   connected_users=list(self.active_connections.keys()))
        
        thought_message = {
            'type': 'agent_thought',
            'id': f"thought-{datetime.utcnow().timestamp()}-{agent_id}",
            'timestamp': datetime.utcnow().isoformat(),
            'agentId': agent_id,
            'agentName': agent_name,
            'workflowId': workflow_id,
            'workflowName': workflow_name,
            'thoughtType': thought_type,
            'message': message,
            'metadata': metadata or {}
        }
        
        # Send to all connected users
        for user_id, connections in self.active_connections.items():
            connections_to_remove = []
            for websocket in connections:
                try:
                    await websocket.send_text(json.dumps(thought_message))
                except Exception as e:
                    logger.error("Failed to broadcast agent thought", 
                               user_id=user_id, error=str(e))
                    connections_to_remove.append(websocket)
            
            for websocket in connections_to_remove:
                await self.disconnect(websocket, user_id)
    
    def _format_task_result_message(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format task result as a chat message"""
        task_id = task_result.get('task_id', 'Unknown')
        status = task_result.get('status', 'Unknown')
        agent_id = task_result.get('agent_id', 'Unknown Agent')
        
        # Create human-readable message based on task status
        if status == 'completed':
            results = task_result.get('results', {})
            execution_time = task_result.get('execution_time')
            
            content = f"✅ **Task Completed**: {task_id}\n"
            content += f"**Agent**: {agent_id}\n"
            
            if execution_time:
                content += f"**Duration**: {execution_time:.2f}s\n"
            
            if results:
                content += f"**Results**: {self._format_results(results)}"
                
        elif status == 'failed':
            error = task_result.get('error', 'Unknown error')
            content = f"❌ **Task Failed**: {task_id}\n"
            content += f"**Agent**: {agent_id}\n"
            content += f"**Error**: {error}"
            
        elif status == 'waiting_approval':
            content = f"⏳ **Task Awaiting Approval**: {task_id}\n"
            content += f"**Agent**: {agent_id}\n"
            content += f"Human approval required to proceed."
            
        else:
            content = f"🔄 **Task Update**: {task_id}\n"
            content += f"**Status**: {status}\n"
            content += f"**Agent**: {agent_id}"
        
        return {
            'type': 'task_result',
            'task_id': task_id,
            'content': content,
            'status': status,
            'agent_id': agent_id,
            'timestamp': datetime.utcnow().isoformat(),
            'is_user': False,
            'sender': 'workflow_system'
        }
    
    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format task results for display"""
        if not results:
            return "No specific results"
            
        formatted = []
        for key, value in results.items():
            if isinstance(value, (dict, list)):
                formatted.append(f"- **{key}**: {json.dumps(value, indent=2)}")
            else:
                formatted.append(f"- **{key}**: {value}")
        
        return "\n".join(formatted)
    
    async def create_user_response_request(self, execution_id: str, task_id: str, question: str, timeout_seconds: int = 300) -> str:
        """Create a user response request and return the request ID"""
        import uuid
        request_id = str(uuid.uuid4())
        
        user_id = self.execution_users.get(execution_id)
        if not user_id:
            raise ValueError(f"No user found for execution {execution_id}")
        
        # Store the pending request
        self.pending_responses[request_id] = {
            'execution_id': execution_id,
            'task_id': task_id,
            'question': question,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'timeout_seconds': timeout_seconds
        }
        
        # Send the question to the user via chat
        await self.send_chat_message(
            execution_id=execution_id,
            message_content=f"🤔 **Question from Agent**\n\n{question}\n\n*Please provide your response in the chat.*",
            agent_id="system",
            agent_name="Human-in-the-Loop System",
            task_id=task_id,
            task_name=f"User Response Request",
            message_type='user_request',
            requires_response=True,
            metadata={
                'request_id': request_id,
                'requires_user_response': True,
                'timeout_seconds': timeout_seconds
            }
        )
        
        logger.info(
            "Created user response request - message sent to chat",
            request_id=request_id,
            execution_id=execution_id,
            task_id=task_id,
            user_id=user_id,
            question=question[:100] + "..." if len(question) > 100 else question,
            has_active_connections=user_id in self.active_connections,
            active_connections_count=len(self.active_connections.get(user_id, []))
        )
        
        return request_id
    
    async def wait_for_user_response(self, request_id: str, timeout_seconds: int = 300) -> str:
        """Wait for user response to a specific request"""
        import asyncio
        
        if request_id not in self.pending_responses:
            raise ValueError(f"Request {request_id} not found")
        
        # Wait for response with timeout
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            if request_id in self.user_responses:
                response = self.user_responses.pop(request_id)
                self.pending_responses.pop(request_id, None)
                
                logger.info(
                    "User response received",
                    request_id=request_id,
                    response=response[:100] + "..." if len(response) > 100 else response
                )
                
                return response
            
            # Check every 100ms
            await asyncio.sleep(0.1)
        
        # Timeout reached
        self.pending_responses.pop(request_id, None)
        raise TimeoutError(f"User response timeout after {timeout_seconds} seconds")
    
    def submit_user_response(self, request_id: str, response: str) -> bool:
        """Submit a user response for a pending request"""
        if request_id not in self.pending_responses:
            logger.warning(f"No pending request found for ID: {request_id}")
            return False
        
        # Get the pending request data
        request_data = self.pending_responses[request_id]
        
        # Check if this is an async request (new pattern)
        if 'async_request' in request_data:
            async_request = request_data['async_request']
            try:
                # Resolve the async request with the user's response
                async_request.set_response(response)
                logger.info("Resolved async human interaction request", 
                          request_id=request_id,
                          response=response[:100] + "..." if len(response) > 100 else response)
            except Exception as e:
                logger.error("Failed to resolve async request", 
                           request_id=request_id, 
                           error=str(e))
                return False
        else:
            # Legacy pattern - store in user_responses dict
            self.user_responses[request_id] = response
            logger.info("Stored user response (legacy pattern)", 
                       request_id=request_id,
                       response=response[:100] + "..." if len(response) > 100 else response)
        
        # Clean up the pending request
        self.pending_responses.pop(request_id, None)
        
        return True
    
    def get_pending_requests_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all pending response requests for a user"""
        return [
            {
                'request_id': request_id,
                'question': request_data['question'],
                'task_id': request_data['task_id'],
                'created_at': request_data['created_at']
            }
            for request_id, request_data in self.pending_responses.items()
            if request_data.get('user_id') == user_id
        ]
    
    def _on_task_done(self, task):
        """Callback when the message processing task completes or fails"""
        try:
            if task.cancelled():
                logger.warning("Message processing task was cancelled")
                # Reset processing flag if task was cancelled
                self._processing_messages = False
                self._message_processing_task = None
            elif task.exception():
                logger.error("Message processing task failed with exception", 
                           error=str(task.exception()))
                # Reset task reference and restart if still supposed to be processing
                self._message_processing_task = None
                if self._processing_messages:
                    logger.info("Automatically restarting message processing task")
                    asyncio.create_task(self._restart_message_processing())
            else:
                logger.info("Message processing task completed normally")
                # Reset task reference if completed normally
                self._message_processing_task = None
                self._processing_messages = False
        except Exception as e:
            logger.error("Error in task completion callback", error=str(e))
    
    async def _restart_message_processing(self):
        """Restart the message processing task"""
        try:
            # Small delay before restart
            await asyncio.sleep(1.0)
            
            if self._processing_messages:
                self._message_processing_task = asyncio.create_task(self._process_message_queue())
                self._message_processing_task.add_done_callback(self._on_task_done)
                logger.info("Message processing task restarted", 
                           task_id=id(self._message_processing_task))
        except Exception as e:
            logger.error("Failed to restart message processing task", error=str(e))
    
    def get_task_health(self):
        """Get health status of the message processing task"""
        if not self._processing_messages:
            return {'status': 'stopped', 'task_exists': False}
        
        task_exists = self._message_processing_task is not None
        task_done = self._message_processing_task.done() if task_exists else True
        task_cancelled = self._message_processing_task.cancelled() if task_exists else False
        
        return {
            'status': 'running' if task_exists and not task_done else 'failed',
            'task_exists': task_exists,
            'task_done': task_done,
            'task_cancelled': task_cancelled,
            'queue_size': self.message_queue.qsize(),
            'processing_flag': self._processing_messages,
            'queue_maxsize': self.message_queue.maxsize,
            'queue_empty': self.message_queue.empty(),
            'queue_full': self.message_queue.full()
        }
    
    async def ensure_message_processing_running(self):
        """Ensure message processing task is running, restart if needed"""
        health = self.get_task_health()
        
        if health['status'] == 'stopped' or health['status'] == 'failed':
            logger.warning("Message processing task is not running, attempting to restart", health=health)
            try:
                # Clean up any stale task references
                if self._message_processing_task and self._message_processing_task.done():
                    self._message_processing_task = None
                
                await self.start_message_processing()
                logger.info("Message processing task restarted successfully")
                return True
            except Exception as e:
                logger.error("Failed to restart message processing task", error=str(e))
                return False
        
        return True

# Global instance
websocket_manager = WebSocketManager()

# Function to initialize message processing (call this from FastAPI startup)
async def initialize_websocket_manager():
    """Initialize the WebSocket manager and start message processing"""
    await websocket_manager.start_message_processing()
    
    # Initialize thread-safe human loop integration
    try:
        from app.services.thread_safe_human_loop import thread_safe_human_loop
        thread_safe_human_loop.set_websocket_manager(websocket_manager)
        logger.info("Thread-safe human loop configured with WebSocket manager")
    except Exception as e:
        logger.error("Failed to configure thread-safe human loop", error=str(e))
    
    logger.info("WebSocket manager initialized with message processing")