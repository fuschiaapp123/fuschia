import asyncio
import json
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
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info("WebSocket connected", user_id=user_id)
        
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
        logger.info("WebSocket disconnected", user_id=user_id)
    
    def register_execution(self, execution_id: str, user_id: str):
        """Register which user initiated a workflow execution"""
        self.execution_users[execution_id] = user_id
        logger.info("Registered execution", execution_id=execution_id, user_id=user_id, 
                   active_connections=list(self.active_connections.keys()))
        
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

# Global instance
websocket_manager = WebSocketManager()