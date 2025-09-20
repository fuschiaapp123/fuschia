#!/usr/bin/env python3
"""
Test script to verify tool name to function mapping in WorkflowExecutionAgent
This will show you exactly which functions are being called for each tool name.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the required classes and modules
class MockTool:
    def __init__(self, name):
        self.name = name

class MockAgentNode:
    def __init__(self):
        self.id = "test_agent"
        self.tools = [
            MockTool("database_query"),
            MockTool("api_request"), 
            MockTool("file_operation"),
            MockTool("human_interaction"),
            MockTool("agent_handoff"),
            MockTool("task_validation"),
            MockTool("knowledge_search"),
            MockTool("notification"),
            MockTool("custom_unknown_tool")  # This will use the generic wrapper
        ]

class MockWorkflowExecutionAgent:
    """Mock version of WorkflowExecutionAgent to test tool mapping"""
    
    def __init__(self):
        self.agent_node = MockAgentNode()
        self.available_tools = self._initialize_tools()
    
    # Mock tool implementation methods (same names as real agent)
    async def _tool_database_query(self, **kwargs):
        return "Database query executed"
    
    async def _tool_api_request(self, **kwargs):
        return "API request executed"
    
    async def _tool_file_operation(self, **kwargs):
        return "File operation executed"
    
    async def _tool_human_interaction(self, **kwargs):
        return "Human interaction executed"
    
    async def _tool_agent_handoff(self, **kwargs):
        return "Agent handoff executed"
    
    async def _tool_task_validation(self, **kwargs):
        return "Task validation executed"
    
    async def _tool_knowledge_search(self, **kwargs):
        return "Knowledge search executed"
    
    async def _tool_notification(self, **kwargs):
        return "Notification sent"
    
    async def _generic_tool_execution(self, tool_name, **kwargs):
        return f"Generic execution for {tool_name}"
    
    def _initialize_tools(self):
        """Exact same logic as real WorkflowExecutionAgent"""
        tools = {}
        
        for tool in self.agent_node.tools:
            # Map tool names to implementations
            if tool.name == "database_query":
                tools[tool.name] = self._tool_database_query
            elif tool.name == "api_request":
                tools[tool.name] = self._tool_api_request
            elif tool.name == "file_operation":
                tools[tool.name] = self._tool_file_operation
            elif tool.name == "human_interaction":
                tools[tool.name] = self._tool_human_interaction
            elif tool.name == "agent_handoff":
                tools[tool.name] = self._tool_agent_handoff
            elif tool.name == "task_validation":
                tools[tool.name] = self._tool_task_validation
            elif tool.name == "knowledge_search":
                tools[tool.name] = self._tool_knowledge_search
            elif tool.name == "notification":
                tools[tool.name] = self._tool_notification
            else:
                # Generic tool wrapper
                tools[tool.name] = lambda **kwargs: self._generic_tool_execution(tool.name, **kwargs)
        
        return tools

def main():
    """Test the tool mapping to verify correct functions are called"""
    print("🔍 Testing Tool Name → Function Mapping")
    print("=" * 60)
    
    agent = MockWorkflowExecutionAgent()
    
    print(f"Agent has {len(agent.available_tools)} tools mapped:")
    print()
    
    for tool_name, func in agent.available_tools.items():
        # Extract function details (same as the debugging code we added)
        func_name = getattr(func, '__name__', str(func))
        func_module = getattr(func, '__module__', 'unknown')
        func_qualname = getattr(func, '__qualname__', func_name)
        
        print(f"Tool Name: '{tool_name}'")
        print(f"  ├── Function Name: {func_name}")
        print(f"  ├── Qualified Name: {func_qualname}")
        print(f"  ├── Module: {func_module}")
        print(f"  └── Callable Object: {func}")
        print()
    
    print("\n" + "=" * 60)
    print("✅ This shows exactly what function gets called for each tool!")
    print("   When you see logs like:")
    print("   'Executing tool database_query -> function _tool_database_query'")
    print("   You'll know it's calling the correct method.")

if __name__ == "__main__":
    main()