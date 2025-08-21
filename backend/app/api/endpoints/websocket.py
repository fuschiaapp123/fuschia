from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.services.websocket_manager import websocket_manager
from app.services.thread_safe_human_loop import thread_safe_human_loop
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
                
                # Try to parse the message as JSON
                try:
                    message = json.loads(data)
                    message_type = message.get('type', 'unknown')
                    
                    if message_type == 'user_response':
                        # Handle user response to agent questions
                        request_id = message.get('request_id')
                        response_text = message.get('response', '')
                        
                        if request_id and response_text:
                            # Try both the original websocket manager and the new thread-safe system
                            success_original = websocket_manager.submit_user_response(request_id, response_text)
                            success_thread_safe = thread_safe_human_loop.submit_response(request_id, response_text)
                            
                            success = success_original or success_thread_safe
                            
                            await websocket.send_text(json.dumps({
                                'type': 'response_confirmation',
                                'success': success,
                                'request_id': request_id,
                                'message': 'Response received' if success else 'Invalid request ID',
                                'processed_by': 'original' if success_original else 'thread_safe' if success_thread_safe else 'none'
                            }))
                        else:
                            await websocket.send_text(json.dumps({
                                'type': 'error',
                                'message': 'Invalid user response format. Expected request_id and response fields.'
                            }))
                    
                    elif message_type == 'chat_message':
                        # Handle regular chat messages - check if they're responses to pending requests
                        content = message.get('content', '')
                        
                        # Check if this user has any pending requests
                        pending_requests = websocket_manager.get_pending_requests_for_user(user_id)
                        
                        if pending_requests:
                            # Assume this is a response to the most recent request
                            latest_request = max(pending_requests, key=lambda x: x['created_at'])
                            request_id = latest_request['request_id']
                            
                            success = websocket_manager.submit_user_response(request_id, content)
                            
                            if success:
                                await websocket.send_text(json.dumps({
                                    'type': 'response_confirmation',
                                    'success': True,
                                    'request_id': request_id,
                                    'message': 'Your response has been received and forwarded to the agent.'
                                }))
                            else:
                                # Echo back as normal chat
                                await websocket.send_text(json.dumps({
                                    'type': 'echo',
                                    'message': f'Received: {content}',
                                    'user_id': user_id
                                }))
                        else:
                            # No pending requests, echo back as normal
                            await websocket.send_text(json.dumps({
                                'type': 'echo',
                                'message': f'Received: {content}',
                                'user_id': user_id
                            }))
                    
                    else:
                        # Echo back other message types
                        await websocket.send_text(json.dumps({
                            'type': 'echo',
                            'message': f'Received: {data}',
                            'user_id': user_id
                        }))
                
                except json.JSONDecodeError:
                    # Handle plain text messages - check for pending requests
                    pending_requests = websocket_manager.get_pending_requests_for_user(user_id)
                    
                    if pending_requests:
                        # Assume this is a response to the most recent request
                        latest_request = max(pending_requests, key=lambda x: x['created_at'])
                        request_id = latest_request['request_id']
                        
                        success = websocket_manager.submit_user_response(request_id, data)
                        
                        if success:
                            await websocket.send_text(json.dumps({
                                'type': 'response_confirmation',
                                'success': True,
                                'request_id': request_id,
                                'message': 'Your response has been received and forwarded to the agent.'
                            }))
                        else:
                            # Echo back as normal
                            await websocket.send_text(json.dumps({
                                'type': 'echo',
                                'message': f'Received: {data}',
                                'user_id': user_id
                            }))
                    else:
                        # No pending requests, echo back as normal
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
        
        # Send test execution update (like Human-in-the-Loop messages)
        await websocket_manager.send_chat_message(
            execution_id="test-execution",
            message_content="🧪 **Test Message from API**\n\nThis is a test message to verify WebSocket connectivity and chat panel integration.\n\nIf you see this message, the WebSocket connection is working!",
            agent_id="test-system",
            agent_name="Test System",
            task_id="test-task-123",
            task_name="WebSocket Test",
            message_type='test_message',
            requires_response=False,
            metadata={'test': True}
        )
        
        return {"message": "Test chat message sent to WebSocket", "user_id": user_id}
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

@router.post("/update_execution_user/{execution_id}/{new_user_id}")
async def update_execution_user(execution_id: str, new_user_id: str):
    """Update the user ID for an execution (useful when user reconnects with new session)"""
    try:
        success = websocket_manager.update_execution_user(execution_id, new_user_id)
        if success:
            return {
                "message": "Execution user updated successfully",
                "execution_id": execution_id,
                "new_user_id": new_user_id
            }
        else:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    except Exception as e:
        logger.error("Failed to update execution user", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update execution user: {str(e)}")

@router.post("/test_human_loop/{user_id}")
async def test_human_in_the_loop(user_id: str, question: str = "What is your favorite color?"):
    """Test endpoint for Human-in-the-Loop functionality"""
    try:
        # Register a test execution
        execution_id = f"test-execution-{user_id}"
        websocket_manager.register_execution(execution_id, user_id)
        
        # Create a user response request
        request_id = await websocket_manager.create_user_response_request(
            execution_id=execution_id,
            task_id="test-task-123",
            question=question,
            timeout_seconds=60  # 1 minute timeout for testing
        )
        
        logger.info(f"Created test Human-in-the-Loop request: {request_id}")
        
        return {
            "message": "Human-in-the-Loop test request created",
            "request_id": request_id,
            "execution_id": execution_id,
            "question": question,
            "instructions": "Send a WebSocket message with type 'user_response' or just send a plain text message to respond"
        }
        
    except Exception as e:
        logger.error("Failed to create test Human-in-the-Loop request", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create test request: {str(e)}")

@router.get("/pending_requests/{user_id}")
async def get_pending_requests(user_id: str):
    """Get pending user response requests for a user"""
    try:
        pending_requests = websocket_manager.get_pending_requests_for_user(user_id)
        return {
            "user_id": user_id,
            "pending_requests": pending_requests,
            "count": len(pending_requests)
        }
    except Exception as e:
        logger.error("Failed to get pending requests", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get pending requests: {str(e)}")