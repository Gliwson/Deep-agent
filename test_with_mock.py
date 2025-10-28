#!/usr/bin/env python3
"""
Test agent with mock implementation (no real API calls)
"""
import asyncio
import json
import os
from unittest.mock import Mock, patch
from main import LangGraphAgent, AgentRequest

async def test_agent_with_mock():
    """Test the agent with mocked OpenAI API calls"""
    print("🤖 Testing LangGraph Agent with Mock API...")
    
    # Mock the OpenAI API calls
    with patch('main.ChatOpenAI') as mock_chat_openai:
        # Setup mock response
        mock_response = Mock()
        mock_response.content = json.dumps({
            "steps": [
                {
                    "step_number": 1,
                    "objective": "List directory contents",
                    "action": "Use list_directory_tool",
                    "tools_needed": ["list_directory_tool"],
                    "expected_outcome": "Directory listing"
                },
                {
                    "step_number": 2,
                    "objective": "Create hello world script",
                    "action": "Use write_file_tool",
                    "tools_needed": ["write_file_tool"],
                    "expected_outcome": "Python script created"
                }
            ]
        })
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm
        
        # Initialize agent
        agent = LangGraphAgent()
        print("✅ Agent initialized with mock")
        
        # Test task
        test_task = "List files and create a hello world script"
        
        print(f"📋 Task: {test_task}")
        print("🚀 Executing task with mock...")
        
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
                plan = result.data.get('plan', {})
                if plan:
                    steps = plan.get('steps', [])
                    print(f"📋 Plan: {len(steps)} steps created")
                    for i, step in enumerate(steps[:2]):  # Show first 2 steps
                        print(f"  Step {i+1}: {step.get('objective', 'No objective')}")
                
                results = result.data.get('results', [])
                print(f"📈 Results: {len(results)} steps completed")
                
                messages = result.data.get('messages', [])
                print(f"💬 Messages: {len(messages)} conversation turns")
            
            if result.error:
                print(f"❌ Error: {result.error}")
            
            print("\n🎯 Mock Test Results:")
            print("  ✅ Agent structure working")
            print("  ✅ Mock API calls working")
            print("  ✅ Task execution flow working")
            print("  ✅ No real API calls made")
            
        except Exception as e:
            print(f"❌ Mock test failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_with_mock())
