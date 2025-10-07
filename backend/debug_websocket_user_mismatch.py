#!/usr/bin/env python3
"""
Debug script to help identify and fix WebSocket user ID mismatches
"""

import asyncio
import requests

async def check_websocket_connections():
    """Check current WebSocket connections and identify user mismatches"""
    
    try:
        # Get WebSocket status
        response = requests.get("http://localhost:8000/api/v1/debug/debug/websocket/status")
        if response.status_code != 200:
            print(f"❌ Failed to get WebSocket status: {response.status_code}")
            return
            
        data = response.json()
        
        print("🔍 WebSocket Connection Analysis")
        print("=" * 50)
        
        active_connections = data.get("active_connections", {})
        execution_users = data.get("execution_users", {})
        
        print(f"📡 Active WebSocket Connections: {len(active_connections)}")
        for user_id, connection_count in active_connections.items():
            print(f"   👤 User: {user_id[:8]}... ({connection_count} connections)")
        
        print(f"\n🔧 Registered Executions: {len(execution_users)}")
        for execution_id, user_id in execution_users.items():
            has_connection = user_id in active_connections
            status = "✅ Connected" if has_connection else "❌ No WebSocket"
            print(f"   🚀 Execution: {execution_id[:8]}... → User: {user_id[:8]}... {status}")
        
        # Identify mismatches
        mismatched_executions = []
        for execution_id, user_id in execution_users.items():
            if user_id not in active_connections:
                mismatched_executions.append((execution_id, user_id))
        
        if mismatched_executions:
            print(f"\n⚠️  Found {len(mismatched_executions)} execution(s) with user ID mismatches:")
            for execution_id, user_id in mismatched_executions:
                print(f"   🔴 Execution {execution_id[:8]}... has no WebSocket for user {user_id[:8]}...")
                
                # Try to update the execution user to a connected user
                if active_connections:
                    connected_user_id = list(active_connections.keys())[0]
                    print(f"   🔄 Attempting to remap to connected user {connected_user_id[:8]}...")
                    
                    try:
                        update_response = requests.post(
                            f"http://localhost:8000/api/v1/ws/update_execution_user/{execution_id}/{connected_user_id}"
                        )
                        if update_response.status_code == 200:
                            print("   ✅ Successfully remapped execution to connected user")
                        else:
                            print(f"   ❌ Failed to remap: {update_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ Error remapping: {e}")
        else:
            print("\n✅ All executions have matching WebSocket connections!")
        
        # Task health check
        task_health = data.get("task_health", {})
        print("\n🔧 WebSocket Task Health:")
        print(f"   Status: {task_health.get('status', 'unknown')}")
        print(f"   Queue Size: {task_health.get('queue_size', 0)}")
        print(f"   Processing: {task_health.get('processing_flag', False)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_websocket_connections())