"""
Test endpoints for the new thread-safe human-in-the-loop functionality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog

from app.services.thread_safe_human_loop import thread_safe_human_loop, HumanRequestType, create_thread_safe_human_tools

router = APIRouter()
logger = structlog.get_logger()


class TestHumanRequestCreate(BaseModel):
    request_type: str
    execution_id: str
    task_id: str
    agent_id: str
    prompt: str
    context: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300


class TestHumanResponse(BaseModel):
    request_id: str
    response: str


@router.post("/test/human-loop/create-request")
async def test_create_human_request(request: TestHumanRequestCreate):
    """Test endpoint to create a human interaction request"""
    try:
        request_type = HumanRequestType(request.request_type)
        
        request_id = thread_safe_human_loop.create_human_request(
            request_type=request_type,
            execution_id=request.execution_id,
            task_id=request.task_id,
            agent_id=request.agent_id,
            prompt=request.prompt,
            context=request.context or {},
            timeout_seconds=request.timeout_seconds
        )
        
        return {
            "status": "success",
            "request_id": request_id,
            "message": f"Human interaction request created for {request_type.value}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create human request: {str(e)}")


@router.post("/test/human-loop/submit-response")
async def test_submit_human_response(response: TestHumanResponse):
    """Test endpoint to submit a response to a human interaction request"""
    try:
        success = thread_safe_human_loop.submit_response(
            request_id=response.request_id,
            response=response.response
        )
        
        return {
            "status": "success" if success else "failed",
            "request_id": response.request_id,
            "message": "Response submitted" if success else "Request ID not found"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit response: {str(e)}")


@router.get("/test/human-loop/pending-requests")
async def test_get_pending_requests(execution_id: str = None):
    """Test endpoint to get pending human interaction requests"""
    try:
        pending = thread_safe_human_loop.get_pending_requests(execution_id)
        
        # Convert to serializable format
        serializable_requests = {}
        for req_id, request in pending.items():
            serializable_requests[req_id] = {
                "request_id": request.request_id,
                "request_type": request.request_type.value,
                "execution_id": request.execution_id,
                "task_id": request.task_id,
                "agent_id": request.agent_id,
                "prompt": request.prompt,
                "context": request.context,
                "timeout_seconds": request.timeout_seconds,
                "created_at": request.created_at
            }
        
        return {
            "status": "success",
            "pending_requests": serializable_requests,
            "count": len(serializable_requests)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending requests: {str(e)}")


@router.post("/test/human-loop/test-tools/{execution_id}/{task_id}/{agent_id}")
async def test_human_loop_tools(execution_id: str, task_id: str, agent_id: str):
    """Test endpoint to demonstrate the thread-safe human loop tools in action"""
    try:
        # Create the tools for this execution context
        tools = create_thread_safe_human_tools(execution_id, task_id, agent_id)
        
        async def test_tool_in_thread():
            """Test calling a human loop tool from a background thread"""
            import threading
            
            result = {"response": None, "error": None}
            
            def call_tool():
                try:
                    # Test the ask_human_question tool
                    response = tools["ask_human_question"]("This is a test question from the API. Please respond with any message to verify the system is working.")
                    result["response"] = response
                except Exception as e:
                    result["error"] = str(e)
            
            # Run in background thread to simulate dspy.React behavior
            thread = threading.Thread(target=call_tool, daemon=True)
            thread.start()
            
            # Wait for completion with timeout
            thread.join(timeout=30)  # 30 second timeout for testing
            
            if thread.is_alive():
                result["error"] = "Tool call timed out"
            
            return result
        
        # Test the tool call
        result = await test_tool_in_thread()
        
        return {
            "status": "success" if result.get("response") else "failed",
            "execution_id": execution_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "result": result,
            "message": "Tool test completed - check the result for the human response"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test human loop tools: {str(e)}")


@router.post("/test/human-loop/simulate-dspy-react")
async def simulate_dspy_react_interaction():
    """Simulate a dspy.React interaction with human-in-the-loop"""
    try:
        import threading
        import time
        
        # Test execution context
        execution_id = "test-exec-001"
        task_id = "test-task-001"
        agent_id = "test-agent-001"
        
        # Create tools
        tools = create_thread_safe_human_tools(execution_id, task_id, agent_id)
        
        results = []
        
        def simulate_react_agent():
            """Simulate a ReAct agent that needs human input"""
            try:
                # Simulate ReAct thinking process
                logger.info("ReAct Agent: Starting task analysis...")
                time.sleep(1)  # Simulate thinking time
                
                # Step 1: Ask for clarification
                logger.info("ReAct Agent: Need clarification from human...")
                response1 = tools["clarify_user_intent"]("I need to process some data, but the requirements are unclear. Should I proceed with format A or format B?")
                results.append({"step": 1, "action": "clarify_intent", "response": response1})
                
                # Step 2: Request approval for the chosen approach
                logger.info("ReAct Agent: Requesting approval for approach...")
                response2 = tools["request_human_approval"](f"Based on your clarification: '{response1}', I will proceed with the suggested approach. Do you approve?")
                results.append({"step": 2, "action": "request_approval", "response": response2})
                
                # Step 3: Ask a specific question about implementation
                logger.info("ReAct Agent: Asking implementation question...")
                response3 = tools["ask_human_question"]("What should be the timeout value for the data processing operation?")
                results.append({"step": 3, "action": "ask_question", "response": response3})
                
                logger.info("ReAct Agent: All human interactions completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"ReAct Agent failed: {str(e)}")
                results.append({"error": str(e)})
                return False
        
        # Run the simulated agent in a background thread (like dspy.React would)
        agent_result = {"success": False}
        
        def run_agent():
            agent_result["success"] = simulate_react_agent()
        
        agent_thread = threading.Thread(target=run_agent, daemon=True)
        agent_thread.start()
        
        # Wait for completion
        agent_thread.join(timeout=120)  # 2 minute timeout
        
        if agent_thread.is_alive():
            return {
                "status": "timeout",
                "message": "Simulated ReAct agent timed out - some human responses may be pending",
                "partial_results": results,
                "execution_id": execution_id
            }
        
        return {
            "status": "success" if agent_result["success"] else "failed",
            "message": "Simulated dspy.React interaction completed",
            "results": results,
            "execution_id": execution_id,
            "total_interactions": len([r for r in results if "error" not in r])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to simulate dspy.React interaction: {str(e)}")


@router.post("/test/human-loop/cleanup")
async def test_cleanup_expired_requests():
    """Test endpoint to clean up expired requests"""
    try:
        cleaned_count = thread_safe_human_loop.cleanup_expired_requests(max_age_seconds=300)  # 5 minutes
        
        return {
            "status": "success",
            "cleaned_requests": cleaned_count,
            "message": f"Cleaned up {cleaned_count} expired requests"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup requests: {str(e)}")


@router.get("/test/human-loop/health")
async def test_human_loop_health():
    """Test endpoint to check the health of the human loop system"""
    try:
        pending_requests = thread_safe_human_loop.get_pending_requests()
        
        return {
            "status": "healthy",
            "pending_requests_count": len(pending_requests),
            "websocket_manager_configured": thread_safe_human_loop.websocket_manager is not None,
            "thread_pool_active": not thread_safe_human_loop.executor._shutdown,
            "message": "Thread-safe human loop system is operational"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Thread-safe human loop system has issues"
        }