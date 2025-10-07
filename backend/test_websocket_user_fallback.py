#!/usr/bin/env python3
"""
Test script to verify WebSocket user ID fallback functionality
"""

import requests

def test_websocket_user_fallback():
    """Test that anonymous chat requests use active WebSocket user IDs"""
    
    print("🧪 Testing WebSocket User ID Fallback")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # First, check active WebSocket connections
        print("1️⃣ Checking active WebSocket connections...")
        ws_status_url = f"{base_url}/api/v1/debug/debug/websocket/status"
        ws_response = requests.get(ws_status_url)
        
        if ws_response.status_code == 200:
            ws_data = ws_response.json()
            active_connections = ws_data.get('active_connections', {})
            
            print(f"   Active connections: {len(active_connections)}")
            for user_id, count in active_connections.items():
                print(f"   👤 User: {user_id[:8]}... ({count} connections)")
            
            if not active_connections:
                print("⚠️ No active WebSocket connections found!")
                print("   Please open the frontend and go to the monitoring tab to establish a connection")
                return
        else:
            print(f"❌ Failed to get WebSocket status: {ws_response.status_code}")
            return
        
        # Now test the enhanced chat endpoint 
        print("\n2️⃣ Testing enhanced chat endpoint with workflow trigger...")
        chat_url = f"{base_url}/api/v1/chat/enhanced"
        chat_request = {
            "messages": [{"role": "user", "content": "Create a workflow for customer onboarding process"}],
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "user_role": "admin",
            "current_module": "workflow",
            "current_tab": "designer"
        }
        
        headers = {"Content-Type": "application/json"}
        
        chat_response = requests.post(chat_url, json=chat_request, headers=headers)
        
        print(f"   Status Code: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            print("✅ Chat request successful")
            result = chat_response.json()
            print(f"   Response preview: {result.get('response', 'No response')[:100]}...")
            
            # Check if workflow was triggered
            if result.get('workflow_result', {}).get('workflow_triggered'):
                print("🚀 Workflow was triggered!")
                
                # Check execution users mapping
                print("\n3️⃣ Checking execution user mappings...")
                ws_response2 = requests.get(ws_status_url)
                if ws_response2.status_code == 200:
                    ws_data2 = ws_response2.json()
                    execution_users = ws_data2.get('execution_users', {})
                    
                    print(f"   Execution mappings: {len(execution_users)}")
                    for exec_id, user_id in execution_users.items():
                        if exec_id != 'test-execution':  # Skip test executions
                            has_connection = user_id in active_connections
                            status = "✅ Connected" if has_connection else "❌ No WebSocket"
                            print(f"   🚀 Execution: {exec_id[:8]}... → User: {user_id[:8]}... {status}")
                            
                            if has_connection:
                                print("✅ SUCCESS: Execution is mapped to a user with active WebSocket!")
                            else:
                                print("❌ FAILED: Execution mapped to user without WebSocket connection")
            else:
                print("ℹ️ No workflow was triggered (intent didn't match workflow criteria)")
        else:
            print(f"❌ Chat request failed: {chat_response.status_code}")
            print(f"   Response: {chat_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Backend server is not running")
        print("   Please start the backend server with: uvicorn main:app --reload --port 8000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_websocket_user_fallback()