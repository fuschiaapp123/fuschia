#!/usr/bin/env python3
"""
Simple test script to verify the intent agent works with the new LangGraph implementation
"""
import asyncio
import sys
import os
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

from app.services.intent_agent import create_intent_agent

async def test_intent_agent():
    """Test the intent agent with a simple message"""
    print("Testing LangGraph Intent Agent...")
    
    # Create the agent
    agent = create_intent_agent()
    
    # Test message
    test_message = "I need help with creating a workflow for IT support"
    
    try:
        result = await agent.detect_intent_with_context(
            message=test_message,
            user_role="admin",
            current_module="workflow",
            current_tab="design"
        )
        
        print(f"✅ Success! Intent detected: {result.get('detected_intent')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Agent Type: {result.get('agent_type')}")
        print(f"   Reasoning: {result.get('reasoning', 'No reasoning provided')[:100]}...")
        print(f"   Workflow Execution: {result.get('workflow_execution', {})}")
        if result.get('workflow_execution', {}).get('recommended'):
            print(f"   Template ID: {result['workflow_execution'].get('template_id')}")
            print(f"   Template Name: {result['workflow_execution'].get('template_name')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_intent_agent())