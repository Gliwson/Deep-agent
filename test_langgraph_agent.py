#!/usr/bin/env python3
"""
Test script for LangGraph Agent
"""
import asyncio
import json
import os
from main import LangGraphAgent, AgentRequest

async def test_agent():
    """Test the LangGraph agent with a simple task"""
    print("🤖 Testing LangGraph Agent...")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set it in .env file")
        return
    
    # Initialize agent
    agent = LangGraphAgent()
    print("✅ Agent initialized successfully")
    
    # Test task
    test_task = "List all files in the current directory and create a simple hello world Python script"
    
    print(f"📋 Task: {test_task}")
    print("🚀 Executing task...")
    
    try:
        # Execute task
        request = AgentRequest(
            task=test_task,
            context={"workspace": "/workspace"},
            constraints=["Use Python 3", "Keep it simple"]
        )
        
        result = await agent.execute_task(request)
        
        print(f"✅ Task completed: {result.success}")
        print(f"📝 Message: {result.message}")
        
        if result.data:
            print(f"📊 Status: {result.data.get('status')}")
            print(f"📋 Plan: {json.dumps(result.data.get('plan'), indent=2)}")
            print(f"📈 Results: {len(result.data.get('results', []))} steps completed")
            
            # Show messages
            messages = result.data.get('messages', [])
            print(f"\n💬 Conversation ({len(messages)} messages):")
            for i, msg in enumerate(messages):
                print(f"  {i+1}. {msg.get('role', 'unknown')}: {msg.get('content', '')[:100]}...")
        
        if result.error:
            print(f"❌ Error: {result.error}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
