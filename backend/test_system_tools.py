#!/usr/bin/env python3
"""
Test script for System Tools Service

This script tests the basic functionality of the system tools service
without requiring full AWS/OpenAI setup.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.system_tools_service import (
    system_tools_service, 
    SystemToolMetadata,
    SystemToolCategory
)


async def test_system_tools_service():
    """Test the system tools service functionality"""
    print("🔧 Testing System Tools Service")
    print("=" * 50)
    
    try:
        # Test initialization
        print("\n1. Initializing System Tools Service...")
        await system_tools_service.initialize()
        print(f"✅ System tools service initialized with {len(system_tools_service.tools)} tools")
        
        # List available tools
        print("\n2. Available System Tools:")
        for tool_name, tool in system_tools_service.tools.items():
            status = "✅ Initialized" if tool.initialized else "❌ Failed"
            print(f"   • {tool_name} ({tool.metadata.category.value}) - {status}")
            print(f"     Description: {tool.metadata.description}")
        
        # Test Context Enhancement Tool (should always work)
        print("\n3. Testing Context Enhancement Tool...")
        context_tool = system_tools_service.get_tool("enhance_context")
        if context_tool and context_tool.initialized:
            result = await context_tool.execute(
                "Deploy application to production environment",
                {"priority": "high", "team": "devops"}
            )
            print("✅ Context Enhancement Result:")
            print(f"   {result[:200]}..." if len(result) > 200 else f"   {result}")
        else:
            print("❌ Context Enhancement Tool not available")
        
        # Test DSPy tool compatibility
        print("\n4. Testing DSPy Tool Compatibility...")
        dspy_tools = system_tools_service.get_dspy_tools()
        print(f"✅ Generated {len(dspy_tools)} DSPy-compatible tools")
        
        for tool_func in dspy_tools:
            print(f"   • {tool_func.__name__}: {tool_func.__doc__}")
        
        # Test RAG tool (might fail without AWS/OpenAI setup)
        print("\n5. Testing RAG Knowledge Tool...")
        rag_tool = system_tools_service.get_tool("rag_knowledge_search")
        if rag_tool:
            if rag_tool.initialized:
                print("✅ RAG Knowledge Tool is initialized")
                # Only test if properly initialized
                try:
                    result = await rag_tool.execute("test query", max_results=1)
                    print(f"✅ RAG Search Result: {result[:100]}...")
                except Exception as e:
                    print(f"⚠️  RAG Search Test Failed: {str(e)}")
            else:
                print("⚠️  RAG Knowledge Tool not initialized (AWS/OpenAI config missing)")
        else:
            print("❌ RAG Knowledge Tool not found")
        
        # Test MCP tool (might fail without MCP services)
        print("\n6. Testing MCP Integration Tool...")
        mcp_tool = system_tools_service.get_tool("mcp_service_call")
        if mcp_tool:
            if mcp_tool.initialized:
                print("✅ MCP Integration Tool is initialized")
                try:
                    result = await mcp_tool.execute("knowledge", "health", {})
                    print(f"✅ MCP Service Call Result: {result[:100]}...")
                except Exception as e:
                    print(f"⚠️  MCP Service Call Test Failed: {str(e)}")
            else:
                print("⚠️  MCP Integration Tool not initialized (MCP services not available)")
        else:
            print("❌ MCP Integration Tool not found")
        
        print("\n" + "=" * 50)
        print("✅ System Tools Service test completed!")
        
        # Summary
        total_tools = len(system_tools_service.tools)
        initialized_tools = sum(1 for tool in system_tools_service.tools.values() if tool.initialized)
        
        print("📊 Summary:")
        print(f"   Total Tools: {total_tools}")
        print(f"   Initialized: {initialized_tools}")
        print(f"   Success Rate: {initialized_tools/total_tools*100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_custom_tool():
    """Test creating and registering a custom system tool"""
    print("\n🔨 Testing Custom Tool Registration")
    print("=" * 50)
    
    try:
        from app.services.system_tools_service import BaseSystemTool
        
        class TestTool(BaseSystemTool):
            def __init__(self):
                super().__init__(SystemToolMetadata(
                    name="test_custom_tool",
                    category=SystemToolCategory.EXTERNAL_SERVICES,
                    description="A test tool for demonstration purposes",
                    version="1.0.0",
                    requires_auth=False
                ))
            
            async def initialize(self) -> bool:
                self.test_data = {"status": "ready", "counter": 0}
                self.initialized = True
                return True
            
            async def execute(self, operation: str = "status", increment: int = 1) -> str:
                if operation == "status":
                    return f"Test tool is {self.test_data['status']}, counter: {self.test_data['counter']}"
                elif operation == "increment":
                    self.test_data['counter'] += increment
                    return f"Counter incremented by {increment}, new value: {self.test_data['counter']}"
                else:
                    return f"Unknown operation: {operation}"
        
        # Register the custom tool
        custom_tool = TestTool()
        await system_tools_service.register_tool(custom_tool)
        
        print(f"✅ Custom tool registered: {custom_tool.metadata.name}")
        
        # Test the custom tool
        result1 = await custom_tool.execute("status")
        print(f"✅ Custom tool status: {result1}")
        
        result2 = await custom_tool.execute("increment", 5)
        print(f"✅ Custom tool increment: {result2}")
        
        result3 = await custom_tool.execute("status")
        print(f"✅ Custom tool final status: {result3}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom tool test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 System Tools Service Test Suite")
    print("=" * 60)
    
    # Test basic service functionality
    success1 = await test_system_tools_service()
    
    # Test custom tool registration
    success2 = await test_custom_tool()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests passed successfully!")
        return 0
    else:
        print("💥 Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)