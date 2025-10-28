#!/usr/bin/env python3
"""
WebSocket client test for LangGraph Agent
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection to the agent"""
    print("🌐 Testing WebSocket connection...")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send ping
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping")
            
            # Wait for pong
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get("type") == "pong":
                print("✅ WebSocket communication working!")
            else:
                print("❌ Unexpected response")
                
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the server is running on port 8000")
    except Exception as e:
        print(f"❌ WebSocket test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
