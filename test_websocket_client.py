"""
WebSocket client for testing the Deep Agent backend
"""
import asyncio
import websockets
import json
import sys

class DeepAgentClient:
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri
        self.websocket = None
    
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"Connected to {self.uri}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            print("Disconnected from server")
    
    async def send_message(self, action, data):
        """Send a message to the server"""
        message = {
            "action": action,
            "data": data
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"Sent: {action}")
            
            # Wait for response
            response = await self.websocket.recv()
            response_data = json.loads(response)
            print(f"Received: {response_data}")
            return response_data
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    async def analyze_code(self, code, language="python", context=None):
        """Analyze code"""
        data = {
            "code": code,
            "language": language,
            "context": context
        }
        return await self.send_message("analyze_code", data)
    
    async def generate_code(self, description, language="python", context=None, existing_code=None):
        """Generate code"""
        data = {
            "description": description,
            "language": language,
            "context": context,
            "existing_code": existing_code
        }
        return await self.send_message("generate_code", data)
    
    async def generate_tests(self, code, language="python", test_framework=None):
        """Generate tests"""
        data = {
            "code": code,
            "language": language,
            "test_framework": test_framework
        }
        return await self.send_message("generate_tests", data)
    
    async def refactor_code(self, code, language="python", refactoring_type="optimize"):
        """Refactor code"""
        data = {
            "code": code,
            "language": language,
            "refactoring_type": refactoring_type
        }
        return await self.send_message("refactor_code", data)

async def test_agent_functionality():
    """Test all agent functionality"""
    client = DeepAgentClient()
    
    if not await client.connect():
        return
    
    try:
        # Test 1: Code Analysis
        print("\n=== Testing Code Analysis ===")
        sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        await client.analyze_code(sample_code, "python", "Fibonacci function")
        
        # Test 2: Code Generation
        print("\n=== Testing Code Generation ===")
        await client.generate_code(
            "Create a function that calculates the factorial of a number",
            "python",
            "Mathematical function"
        )
        
        # Test 3: Test Generation
        print("\n=== Testing Test Generation ===")
        await client.generate_tests(sample_code, "python", "pytest")
        
        # Test 4: Code Refactoring
        print("\n=== Testing Code Refactoring ===")
        await client.refactor_code(sample_code, "python", "optimize")
        
        # Test 5: JavaScript Code
        print("\n=== Testing JavaScript Code ===")
        js_code = """
function calculateSum(a, b) {
    return a + b;
}
"""
        await client.analyze_code(js_code, "javascript", "Simple addition function")
        
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        await client.disconnect()

async def interactive_mode():
    """Interactive mode for testing"""
    client = DeepAgentClient()
    
    if not await client.connect():
        return
    
    print("\nInteractive mode. Type 'quit' to exit.")
    print("Commands: analyze, generate, test, refactor")
    
    try:
        while True:
            command = input("\nEnter command: ").strip().lower()
            
            if command == "quit":
                break
            elif command == "analyze":
                code = input("Enter code to analyze: ")
                language = input("Enter language (default: python): ") or "python"
                context = input("Enter context (optional): ") or None
                await client.analyze_code(code, language, context)
            elif command == "generate":
                description = input("Enter code description: ")
                language = input("Enter language (default: python): ") or "python"
                await client.generate_code(description, language)
            elif command == "test":
                code = input("Enter code to test: ")
                language = input("Enter language (default: python): ") or "python"
                await client.generate_tests(code, language)
            elif command == "refactor":
                code = input("Enter code to refactor: ")
                language = input("Enter language (default: python): ") or "python"
                refactor_type = input("Enter refactoring type (default: optimize): ") or "optimize"
                await client.refactor_code(code, language, refactor_type)
            else:
                print("Unknown command. Available: analyze, generate, test, refactor, quit")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_agent_functionality())