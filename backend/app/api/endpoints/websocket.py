from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.services.websocket_manager import websocket_manager
import structlog
import json

router = APIRouter()
logger = structlog.get_logger()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time workflow updates"""
    logger.info("WebSocket connection attempt", user_id=user_id)
    
    try:
        await websocket_manager.connect(websocket, user_id)
        logger.info("WebSocket connected successfully", user_id=user_id)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            'type': 'connection',
            'message': 'Connected to workflow updates',
            'user_id': user_id
        }))
        
        while True:
            # Keep connection alive and handle any incoming messages
            try:
                data = await websocket.receive_text()
                logger.debug("WebSocket message received", user_id=user_id, data=data)
                
                # Echo back received messages (for testing)
                await websocket.send_text(json.dumps({
                    'type': 'echo',
                    'message': f'Received: {data}',
                    'user_id': user_id
                }))
                
            except Exception as e:
                logger.error("Error processing WebSocket message", user_id=user_id, error=str(e))
                break
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected", user_id=user_id)
    except Exception as e:
        logger.error("WebSocket connection error", user_id=user_id, error=str(e))
    finally:
        await websocket_manager.disconnect(websocket, user_id)

@router.get("/test/{user_id}")
async def test_websocket(user_id: str):
    """Test endpoint to send a message via WebSocket"""
    try:
        websocket_manager.register_execution("test-execution", user_id)
        
        # Send test task result
        await websocket_manager.send_task_result("test-execution", {
            'task_id': 'test-task-123',
            'status': 'completed', 
            'agent_id': 'test-agent',
            'results': {'message': 'Hello from workflow!'},
            'execution_time': 2.5
        })
        
        return {"message": "Test message sent to WebSocket", "user_id": user_id}
    except Exception as e:
        logger.error("Failed to send test message", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to send test message: {str(e)}")

@router.get("/connections")
async def get_websocket_connections():
    """Debug endpoint to see active WebSocket connections"""
    return {
        "active_connections": {
            user_id: len(connections) for user_id, connections in websocket_manager.active_connections.items()
        },
        "execution_users": dict(websocket_manager.execution_users)
    }