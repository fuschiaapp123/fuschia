"""
Debug endpoints for WebSocket manager
"""

from fastapi import APIRouter
from app.services.websocket_manager import websocket_manager
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.get("/debug/websocket/status")
async def get_websocket_status():
    """Get the current status of the WebSocket manager"""
    try:
        health = websocket_manager.get_task_health()
        
        return {
            "task_health": health,
            "active_connections": {
                user_id: len(connections) 
                for user_id, connections in websocket_manager.active_connections.items()
            },
            "execution_users": dict(websocket_manager.execution_users),
            "pending_responses": {
                req_id: {
                    "execution_id": req_data.get("execution_id"),
                    "user_id": req_data.get("user_id"),
                    "question": req_data.get("question", "")[:100] + "..." if len(req_data.get("question", "")) > 100 else req_data.get("question", ""),
                    "created_at": req_data.get("created_at")
                }
                for req_id, req_data in websocket_manager.pending_responses.items()
            },
            "user_responses": list(websocket_manager.user_responses.keys()),
            "message_queue_size": websocket_manager.message_queue.qsize(),
            "processing_messages_flag": websocket_manager._processing_messages
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.post("/debug/websocket/restart-processing")
async def restart_websocket_processing():
    """Restart the WebSocket message processing task"""
    try:
        health_before = websocket_manager.get_task_health()
        
        # Stop and restart
        await websocket_manager.stop_message_processing()
        await websocket_manager.start_message_processing()
        
        health_after = websocket_manager.get_task_health()
        
        return {
            "success": True,
            "health_before": health_before,
            "health_after": health_after,
            "message": "WebSocket message processing restarted"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.post("/debug/websocket/test-message/{execution_id}")
async def test_websocket_message(execution_id: str):
    """Test sending a message through the WebSocket system"""
    try:
        # Queue a test message
        websocket_manager.queue_chat_message_from_thread(
            execution_id=execution_id,
            message_content="🔧 **Test Message from Debug Endpoint**\n\nThis is a test message to verify WebSocket message processing is working.",
            agent_id="debug-agent",
            agent_name="Debug Agent",
            task_id="debug-task",
            task_name="Debug Test",
            message_type="test_message",
            requires_response=False,
            metadata={"debug": True, "timestamp": "2025-08-20"}
        )
        
        health = websocket_manager.get_task_health()
        
        return {
            "success": True,
            "execution_id": execution_id,
            "message": "Test message queued successfully",
            "queue_size_after": websocket_manager.message_queue.qsize(),
            "task_health": health
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }