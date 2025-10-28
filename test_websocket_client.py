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
    
    async def read_file(self, file_path, encoding="utf-8"):
        """Read file content"""
        data = {
            "file_path": file_path,
            "encoding": encoding
        }
        return await self.send_message("read_file", data)
    
    async def write_file(self, file_path, content, encoding="utf-8", backup=True):
        """Write content to file"""
        data = {
            "file_path": file_path,
            "content": content,
            "encoding": encoding,
            "backup": backup
        }
        return await self.send_message("write_file", data)
    
    async def list_directory(self, directory=None):
        """List directory contents"""
        data = {
            "directory": directory
        }
        return await self.send_message("list_directory", data)
    
    async def search_text(self, pattern, file_path=None, directory=None, case_sensitive=False, regex=False):
        """Search for text in files"""
        data = {
            "pattern": pattern,
            "file_path": file_path,
            "directory": directory,
            "case_sensitive": case_sensitive,
            "regex": regex
        }
        return await self.send_message("search_text", data)
    
    async def replace_text(self, file_path, old_text, new_text, count=-1, backup=True):
        """Replace text in file"""
        data = {
            "file_path": file_path,
            "old_text": old_text,
            "new_text": new_text,
            "count": count,
            "backup": backup
        }
        return await self.send_message("replace_text", data)
    
    async def execute_command(self, command, working_directory=None, timeout=30):
        """Execute terminal command"""
        data = {
            "command": command,
            "working_directory": working_directory,
            "timeout": timeout
        }
        return await self.send_message("execute_command", data)
    
    async def plan_task(self, task, context=None, constraints=None):
        """Plan a complex task"""
        data = {
            "task": task,
            "context": context,
            "constraints": constraints or []
        }
        return await self.send_message("plan_task", data)
    
    async def create_mock(self, mock_type, mock_data):
        """Create mock data or services"""
        data = {
            "mock_type": mock_type,
            "mock_data": mock_data
        }
        return await self.send_message("create_mock", data)

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
        
        # Test 5: File Operations
        print("\n=== Testing File Operations ===")
        await client.write_file("test_file.py", sample_code)
        await client.read_file("test_file.py")
        await client.list_directory()
        
        # Test 6: Search Operations
        print("\n=== Testing Search Operations ===")
        await client.search_text("fibonacci", case_sensitive=False)
        await client.search_text("def.*fibonacci", regex=True)
        
        # Test 7: Replace Operations
        print("\n=== Testing Replace Operations ===")
        await client.replace_text("test_file.py", "fibonacci", "fib", count=1)
        
        # Test 8: Terminal Operations
        print("\n=== Testing Terminal Operations ===")
        await client.execute_command("ls -la")
        await client.execute_command("python --version")
        
        # Test 9: Planning
        print("\n=== Testing Planning ===")
        await client.plan_task(
            "Create a web application with user authentication",
            "Python FastAPI backend with React frontend",
            ["Must use PostgreSQL", "Must have JWT authentication"]
        )
        
        # Test 10: Mock Creation
        print("\n=== Testing Mock Creation ===")
        await client.create_mock("api_response", {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": {"message": "Success", "data": []}
        })
        
        # Test 11: JavaScript Code
        print("\n=== Testing JavaScript Code ===")
        js_code = """
function calculateSum(a, b) {
    return a + b;
}
"""
        await client.analyze_code(js_code, "javascript", "Simple addition function")
        
        # Cleanup
        await client.execute_command("rm -f test_file.py test_file.py.backup")
        
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
    print("Commands: analyze, generate, test, refactor, read, write, list, search, replace, execute, plan, mock")
    
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
            elif command == "read":
                file_path = input("Enter file path: ")
                await client.read_file(file_path)
            elif command == "write":
                file_path = input("Enter file path: ")
                content = input("Enter content: ")
                await client.write_file(file_path, content)
            elif command == "list":
                directory = input("Enter directory (optional): ") or None
                await client.list_directory(directory)
            elif command == "search":
                pattern = input("Enter search pattern: ")
                file_path = input("Enter file path (optional): ") or None
                directory = input("Enter directory (optional): ") or None
                case_sensitive = input("Case sensitive? (y/n): ").lower() == "y"
                regex = input("Use regex? (y/n): ").lower() == "y"
                await client.search_text(pattern, file_path, directory, case_sensitive, regex)
            elif command == "replace":
                file_path = input("Enter file path: ")
                old_text = input("Enter text to replace: ")
                new_text = input("Enter new text: ")
                count = input("Enter count (-1 for all): ")
                count = int(count) if count else -1
                await client.replace_text(file_path, old_text, new_text, count)
            elif command == "execute":
                command_str = input("Enter command to execute: ")
                working_dir = input("Enter working directory (optional): ") or None
                await client.execute_command(command_str, working_dir)
            elif command == "plan":
                task = input("Enter task to plan: ")
                context = input("Enter context (optional): ") or None
                constraints = input("Enter constraints (comma-separated, optional): ")
                constraints = [c.strip() for c in constraints.split(",")] if constraints else None
                await client.plan_task(task, context, constraints)
            elif command == "mock":
                mock_type = input("Enter mock type (api_response, database, file_system): ")
                print("Enter mock data as JSON (or press Enter for default):")
                mock_data_input = input()
                if mock_data_input:
                    import json
                    mock_data = json.loads(mock_data_input)
                else:
                    mock_data = {}
                await client.create_mock(mock_type, mock_data)
            else:
                print("Unknown command. Available: analyze, generate, test, refactor, read, write, list, search, replace, execute, plan, mock, quit")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_agent_functionality())