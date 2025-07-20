#!/usr/bin/env python3
"""
Check if the LangChain packages can be imported without errors
"""
import sys

def check_imports():
    """Check if all required packages can be imported"""
    try:
        print("Checking LangChain imports...")
        
        # Check core LangChain imports
        from langchain_core.tools import tool
        print("✅ langchain_core.tools imported successfully")
        
        from langchain_core.messages import HumanMessage
        print("✅ langchain_core.messages imported successfully")
        
        from langchain_openai import ChatOpenAI
        print("✅ langchain_openai imported successfully")
        
        # Check LangGraph import
        from langgraph.prebuilt import create_react_agent
        print("✅ langgraph.prebuilt imported successfully")
        
        # Check if we can create a basic agent
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, api_key="dummy")
        print("✅ ChatOpenAI created successfully")
        
        # Create a dummy tool
        @tool
        def dummy_tool(query: str) -> str:
            """A dummy tool for testing"""
            return f"Got query: {query}"
        
        print("✅ Tool decorator works")
        
        # Try to create an agent
        agent = create_react_agent(llm, [dummy_tool])
        print("✅ create_react_agent works")
        
        print("\n🎉 All imports successful! The packages are compatible.")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)