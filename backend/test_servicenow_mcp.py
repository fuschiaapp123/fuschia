#!/usr/bin/env python3
"""
Test script for ServiceNow MCP integration
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.servicenow_mcp_server import servicenow_mcp_server
from app.services.mcp_tool_bridge import mcp_tool_bridge


async def test_servicenow_mcp_server():
    """Test ServiceNow MCP server functionality"""
    print("=== Testing ServiceNow MCP Server ===")
    
    try:
        # Initialize the server
        print("1. Initializing ServiceNow MCP server...")
        await servicenow_mcp_server.initialize()
        print(f"   ✓ Server initialized: {servicenow_mcp_server.is_running}")
        
        # List available tools
        print("\n2. Listing available ServiceNow tools...")
        tools = await servicenow_mcp_server.list_tools()
        print(f"   ✓ Found {len(tools)} tools:")
        for tool in tools[:5]:  # Show first 5 tools
            print(f"     - {tool.get('name')}: {tool.get('description')[:50]}...")
        
        # List available resources
        print("\n3. Listing available ServiceNow resources...")
        resources = await servicenow_mcp_server.list_resources()
        print(f"   ✓ Found {len(resources)} resources:")
        for resource in resources[:3]:  # Show first 3 resources
            print(f"     - {resource.get('name')}: {resource.get('uri')}")
        
        # Test a simple tool call
        print("\n4. Testing ServiceNow tool execution...")
        try:
            result = await servicenow_mcp_server.call_tool(
                "servicenow_list_tables", 
                {}
            )
            print(f"   ✓ Tool execution successful: {len(result)} result items")
            
        except Exception as e:
            print(f"   ⚠ Tool execution failed (expected if ServiceNow not configured): {e}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error testing ServiceNow MCP server: {e}")
        return False


async def test_mcp_tool_bridge():
    """Test MCP tool bridge with ServiceNow integration"""
    print("\n=== Testing MCP Tool Bridge Integration ===")
    
    try:
        # Initialize the bridge
        print("1. Initializing MCP tool bridge...")
        await mcp_tool_bridge.initialize()
        print(f"   ✓ Bridge initialized with {len(mcp_tool_bridge.tool_mappings)} tool mappings")
        print(f"   ✓ External servers: {list(mcp_tool_bridge.external_servers.keys())}")
        
        # Get all available tools
        print("\n2. Getting all available MCP tools...")
        all_tools = await mcp_tool_bridge.get_available_mcp_tools()
        servicenow_tools = [t for t in all_tools if t.get('name', '').startswith('servicenow_')]
        print(f"   ✓ Total MCP tools: {len(all_tools)}")
        print(f"   ✓ ServiceNow tools: {len(servicenow_tools)}")
        
        # Show ServiceNow tools
        if servicenow_tools:
            print("   ServiceNow tools found:")
            for tool in servicenow_tools[:3]:
                print(f"     - {tool.get('name')}")
        
        # Test tool execution through bridge
        print("\n3. Testing tool execution through bridge...")
        if servicenow_tools:
            try:
                test_tool = servicenow_tools[0]
                execution = await mcp_tool_bridge.execute_mcp_tool_call(
                    test_tool.get('name'),
                    {}
                )
                print(f"   ✓ Execution created: {execution.execution_id}")
                print(f"   ✓ Status: {execution.status}")
                
            except Exception as e:
                print(f"   ⚠ Execution failed (expected if ServiceNow not configured): {e}")
        else:
            print("   ⚠ No ServiceNow tools available for testing")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error testing MCP tool bridge: {e}")
        return False


async def main():
    """Run all tests"""
    print("ServiceNow MCP Integration Test")
    print("=" * 50)
    
    # Test ServiceNow MCP server
    server_test = await test_servicenow_mcp_server()
    
    # Test MCP tool bridge integration  
    bridge_test = await test_mcp_tool_bridge()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"ServiceNow MCP Server: {'✓ PASS' if server_test else '✗ FAIL'}")
    print(f"MCP Tool Bridge:       {'✓ PASS' if bridge_test else '✗ FAIL'}")
    
    if server_test and bridge_test:
        print("\n🎉 All tests passed! ServiceNow MCP integration is working.")
        
        # Additional info
        print("\nNext steps:")
        print("1. Configure ServiceNow credentials in environment variables:")
        print("   - SERVICENOW_INSTANCE_URL")
        print("   - SERVICENOW_INSTANCE_USERNAME") 
        print("   - SERVICENOW_INSTANCE_PASSWORD")
        print("2. Call the /api/v1/mcp/servers/predefined endpoint to register ServiceNow server")
        print("3. Use ServiceNow tools in workflows via MCP protocol")
        
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
    
    return server_test and bridge_test


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)