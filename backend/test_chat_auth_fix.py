#!/usr/bin/env python3
"""
Test script to verify the enhanced chat endpoint authentication fix
"""

import requests

def test_enhanced_chat_endpoint():
    """Test the enhanced chat endpoint with and without authentication"""
    
    print("🧪 Testing Enhanced Chat Endpoint Authentication Fix")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    chat_url = f"{base_url}/api/v1/chat/enhanced"
    
    # Test payload
    chat_request = {
        "messages": [{"role": "user", "content": "Hello, can you help me with a simple task?"}],
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "user_role": "admin",
        "current_module": "workflow",
        "current_tab": "designer"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("📡 Testing enhanced chat endpoint without authentication...")
        
        response = requests.post(chat_url, json=chat_request, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Enhanced chat endpoint works without authentication")
            result = response.json()
            print(f"Response: {result.get('response', 'No response')[:100]}...")
            print(f"Agent: {result.get('agent_label', 'Unknown')}")
        elif response.status_code == 403:
            print("❌ FAILED: Still getting 403 Forbidden - authentication fix not working")
            print(f"Response: {response.text}")
        else:
            print(f"⚠️  UNEXPECTED: Got status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Backend server is not running")
        print("   Please start the backend server with: uvicorn main:app --reload --port 8000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_enhanced_chat_endpoint()