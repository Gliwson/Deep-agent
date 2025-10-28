import asyncio
import json
import logging
import os
import subprocess
import re
import ast
import shutil
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import mimetypes
import tempfile
import threading
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Deep Agent Backend", version="2.0.0")

# Initialize OpenAI
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Request/Response Models
class CodeAnalysisRequest(BaseModel):
    code: str
    language: str
    context: Optional[str] = None

class CodeGenerationRequest(BaseModel):
    description: str
    language: str
    context: Optional[str] = None
    existing_code: Optional[str] = None

class CodeTestGenerationRequest(BaseModel):
    code: str
    language: str
    test_framework: Optional[str] = None

class RefactoringRequest(BaseModel):
    code: str
    language: str
    refactoring_type: str

class FileReadRequest(BaseModel):
    file_path: str
    encoding: Optional[str] = "utf-8"

class FileWriteRequest(BaseModel):
    file_path: str
    content: str
    encoding: Optional[str] = "utf-8"
    backup: Optional[bool] = True

class SearchRequest(BaseModel):
    pattern: str
    file_path: Optional[str] = None
    directory: Optional[str] = None
    case_sensitive: Optional[bool] = False
    regex: Optional[bool] = False

class ReplaceRequest(BaseModel):
    file_path: str
    old_text: str
    new_text: str
    count: Optional[int] = -1
    backup: Optional[bool] = True

class TerminalRequest(BaseModel):
    command: str
    working_directory: Optional[str] = None
    timeout: Optional[int] = 30

class PlanningRequest(BaseModel):
    task: str
    context: Optional[str] = None
    constraints: Optional[List[str]] = None

class AgentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DeepAgent:
    def __init__(self):
        self.client = client
        self.workspace_root = Path("/workspace")
        self.temp_dir = Path(tempfile.gettempdir()) / "deep_agent"
        self.temp_dir.mkdir(exist_ok=True)
        
    # File Operations
    async def read_file(self, request: FileReadRequest) -> AgentResponse:
        """Read file content"""
        try:
            file_path = Path(request.file_path)
            if not file_path.exists():
                return AgentResponse(
                    success=False,
                    message="File not found",
                    error=f"File {file_path} does not exist"
                )
            
            with open(file_path, 'r', encoding=request.encoding) as f:
                content = f.read()
            
            return AgentResponse(
                success=True,
                message="File read successfully",
                data={
                    "content": content,
                    "file_path": str(file_path),
                    "size": len(content),
                    "lines": len(content.splitlines())
                }
            )
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to read file",
                error=str(e)
            )
    
    async def write_file(self, request: FileWriteRequest) -> AgentResponse:
        """Write content to file"""
        try:
            file_path = Path(request.file_path)
            
            # Create backup if requested
            if request.backup and file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                shutil.copy2(file_path, backup_path)
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=request.encoding) as f:
                f.write(request.content)
            
            return AgentResponse(
                success=True,
                message="File written successfully",
                data={
                    "file_path": str(file_path),
                    "size": len(request.content),
                    "lines": len(request.content.splitlines())
                }
            )
        except Exception as e:
            logger.error(f"Error writing file: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to write file",
                error=str(e)
            )
    
    async def list_directory(self, directory: str = None) -> AgentResponse:
        """List directory contents"""
        try:
            dir_path = Path(directory) if directory else self.workspace_root
            
            if not dir_path.exists():
                return AgentResponse(
                    success=False,
                    message="Directory not found",
                    error=f"Directory {dir_path} does not exist"
                )
            
            items = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_file": item.is_file(),
                    "is_directory": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                })
            
            return AgentResponse(
                success=True,
                message="Directory listed successfully",
                data={
                    "directory": str(dir_path),
                    "items": items,
                    "count": len(items)
                }
            )
        except Exception as e:
            logger.error(f"Error listing directory: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to list directory",
                error=str(e)
            )
    
    # Search Operations
    async def search_text(self, request: SearchRequest) -> AgentResponse:
        """Search for text in files"""
        try:
            pattern = request.pattern
            if not request.regex:
                pattern = re.escape(pattern)
            
            flags = 0 if request.case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            
            results = []
            search_paths = []
            
            if request.file_path:
                search_paths = [Path(request.file_path)]
            elif request.directory:
                search_paths = list(Path(request.directory).rglob("*"))
            else:
                search_paths = list(self.workspace_root.rglob("*"))
            
            for file_path in search_paths:
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            matches = list(regex.finditer(content))
                            
                            if matches:
                                file_results = []
                                for match in matches:
                                    line_num = content[:match.start()].count('\n') + 1
                                    line_start = content.rfind('\n', 0, match.start()) + 1
                                    line_end = content.find('\n', match.end())
                                    if line_end == -1:
                                        line_end = len(content)
                                    line_content = content[line_start:line_end]
                                    
                                    file_results.append({
                                        "match": match.group(),
                                        "line_number": line_num,
                                        "line_content": line_content,
                                        "start": match.start(),
                                        "end": match.end()
                                    })
                                
                                results.append({
                                    "file_path": str(file_path),
                                    "matches": file_results,
                                    "match_count": len(file_results)
                                })
                    except (UnicodeDecodeError, PermissionError):
                        continue
            
            return AgentResponse(
                success=True,
                message="Search completed",
                data={
                    "pattern": request.pattern,
                    "results": results,
                    "total_matches": sum(r["match_count"] for r in results)
                }
            )
        except Exception as e:
            logger.error(f"Error searching text: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to search text",
                error=str(e)
            )
    
    # Replace Operations
    async def replace_text(self, request: ReplaceRequest) -> AgentResponse:
        """Replace text in file"""
        try:
            file_path = Path(request.file_path)
            
            if not file_path.exists():
                return AgentResponse(
                    success=False,
                    message="File not found",
                    error=f"File {file_path} does not exist"
                )
            
            # Create backup if requested
            if request.backup:
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                shutil.copy2(file_path, backup_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if request.count == -1:
                new_content = content.replace(request.old_text, request.new_text)
            else:
                new_content = content.replace(request.old_text, request.new_text, request.count)
            
            replacements_made = content.count(request.old_text) - new_content.count(request.old_text)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return AgentResponse(
                success=True,
                message="Text replaced successfully",
                data={
                    "file_path": str(file_path),
                    "replacements_made": replacements_made,
                    "old_text": request.old_text,
                    "new_text": request.new_text
                }
            )
        except Exception as e:
            logger.error(f"Error replacing text: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to replace text",
                error=str(e)
            )
    
    # Terminal Operations
    async def execute_command(self, request: TerminalRequest) -> AgentResponse:
        """Execute terminal command"""
        try:
            working_dir = Path(request.working_directory) if request.working_directory else self.workspace_root
            
            if not working_dir.exists():
                return AgentResponse(
                    success=False,
                    message="Working directory not found",
                    error=f"Directory {working_dir} does not exist"
                )
            
            process = await asyncio.create_subprocess_shell(
                request.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=request.timeout
                )
                
                return AgentResponse(
                    success=process.returncode == 0,
                    message="Command executed",
                    data={
                        "command": request.command,
                        "return_code": process.returncode,
                        "stdout": stdout.decode('utf-8'),
                        "stderr": stderr.decode('utf-8'),
                        "working_directory": str(working_dir)
                    }
                )
            except asyncio.TimeoutError:
                process.kill()
                return AgentResponse(
                    success=False,
                    message="Command timed out",
                    error=f"Command exceeded timeout of {request.timeout} seconds"
                )
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to execute command",
                error=str(e)
            )
    
    # Planning and Thinking
    async def plan_task(self, request: PlanningRequest) -> AgentResponse:
        """Plan a complex task with step-by-step breakdown"""
        try:
            constraints_text = "\n".join(request.constraints) if request.constraints else "No specific constraints"
            
            system_prompt = f"""You are an expert project planner and software architect. Create a detailed plan for the following task:

Task: {request.task}
Context: {request.context or "No additional context provided"}
Constraints: {constraints_text}

Provide a comprehensive plan with:
1. Task breakdown into subtasks
2. Dependencies between subtasks
3. Estimated effort for each subtask
4. Required resources and tools
5. Risk assessment
6. Success criteria
7. Timeline estimation
8. Alternative approaches

Format the response as a structured JSON with clear sections."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Create a detailed plan for this task."}
                ],
                temperature=0.2
            )
            
            plan = response.choices[0].message.content
            
            return AgentResponse(
                success=True,
                message="Task planning completed",
                data={"plan": plan}
            )
        except Exception as e:
            logger.error(f"Error in task planning: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to plan task",
                error=str(e)
            )
    
    # Mock and Simulation
    async def create_mock(self, mock_type: str, data: Dict[str, Any]) -> AgentResponse:
        """Create mock data or services for testing"""
        try:
            if mock_type == "api_response":
                mock_data = {
                    "status_code": data.get("status_code", 200),
                    "headers": data.get("headers", {}),
                    "body": data.get("body", {}),
                    "delay": data.get("delay", 0),
                    "content_type": data.get("content_type", "application/json")
                }
            elif mock_type == "database":
                mock_data = {
                    "tables": data.get("tables", []),
                    "records": data.get("records", []),
                    "relationships": data.get("relationships", []),
                    "connection_string": data.get("connection_string", "mock://localhost"),
                    "query_timeout": data.get("query_timeout", 30)
                }
            elif mock_type == "file_system":
                mock_data = {
                    "files": data.get("files", []),
                    "directories": data.get("directories", []),
                    "permissions": data.get("permissions", {}),
                    "disk_space": data.get("disk_space", 1000000000),
                    "file_encoding": data.get("file_encoding", "utf-8")
                }
            elif mock_type == "websocket":
                mock_data = {
                    "connection_url": data.get("connection_url", "ws://localhost:8000"),
                    "message_types": data.get("message_types", []),
                    "handshake_headers": data.get("handshake_headers", {}),
                    "ping_interval": data.get("ping_interval", 30),
                    "max_message_size": data.get("max_message_size", 1024)
                }
            elif mock_type == "authentication":
                mock_data = {
                    "token": data.get("token", "mock_token_123"),
                    "user_id": data.get("user_id", "mock_user"),
                    "roles": data.get("roles", ["user"]),
                    "permissions": data.get("permissions", []),
                    "expires_at": data.get("expires_at", int(time.time()) + 3600),
                    "refresh_token": data.get("refresh_token", "mock_refresh_123")
                }
            elif mock_type == "caching":
                mock_data = {
                    "cache_type": data.get("cache_type", "memory"),
                    "ttl": data.get("ttl", 3600),
                    "max_size": data.get("max_size", 1000),
                    "eviction_policy": data.get("eviction_policy", "lru"),
                    "compression": data.get("compression", False)
                }
            elif mock_type == "logging":
                mock_data = {
                    "log_level": data.get("log_level", "INFO"),
                    "log_format": data.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                    "handlers": data.get("handlers", ["console", "file"]),
                    "max_file_size": data.get("max_file_size", 10485760),
                    "backup_count": data.get("backup_count", 5)
                }
            elif mock_type == "file_upload":
                mock_data = {
                    "max_file_size": data.get("max_file_size", 10485760),
                    "allowed_extensions": data.get("allowed_extensions", [".txt", ".pdf", ".jpg"]),
                    "upload_path": data.get("upload_path", "/tmp/uploads"),
                    "chunk_size": data.get("chunk_size", 8192),
                    "compression": data.get("compression", False)
                }
            elif mock_type == "email":
                mock_data = {
                    "smtp_server": data.get("smtp_server", "localhost"),
                    "smtp_port": data.get("smtp_port", 587),
                    "username": data.get("username", "mock@example.com"),
                    "password": data.get("password", "mock_password"),
                    "from_address": data.get("from_address", "noreply@example.com"),
                    "templates": data.get("templates", {})
                }
            elif mock_type == "queue":
                mock_data = {
                    "queue_name": data.get("queue_name", "mock_queue"),
                    "message_ttl": data.get("message_ttl", 3600),
                    "max_retries": data.get("max_retries", 3),
                    "visibility_timeout": data.get("visibility_timeout", 30),
                    "dead_letter_queue": data.get("dead_letter_queue", "mock_dlq")
                }
            else:
                mock_data = data
            
            # Save mock to temporary file
            mock_file = self.temp_dir / f"mock_{mock_type}_{int(time.time())}.json"
            with open(mock_file, 'w') as f:
                json.dump(mock_data, f, indent=2)
            
            # Validate mock data
            validation_result = self._validate_mock_data(mock_type, data)  # Use original data, not processed
            if not validation_result["valid"]:
                return AgentResponse(
                    success=False,
                    message="Mock validation failed",
                    error=validation_result["error"]
                )
            
            return AgentResponse(
                success=True,
                message="Mock created successfully",
                data={
                    "mock_type": mock_type,
                    "mock_data": mock_data,
                    "mock_file": str(mock_file),
                    "validation": validation_result
                }
            )
        except Exception as e:
            logger.error(f"Error creating mock: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to create mock",
                error=str(e)
            )
    
    def _validate_mock_data(self, mock_type: str, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate mock data based on type"""
        try:
            if mock_type == "api_response":
                required_fields = ["status_code", "headers", "body"]
                if not all(field in mock_data for field in required_fields):
                    return {"valid": False, "error": f"Missing required fields: {required_fields}"}
                if not isinstance(mock_data["status_code"], int) or not (100 <= mock_data["status_code"] <= 599):
                    return {"valid": False, "error": "status_code must be an integer between 100 and 599"}
                    
            elif mock_type == "database":
                required_fields = ["tables", "records"]
                if not all(field in mock_data for field in required_fields):
                    return {"valid": False, "error": f"Missing required fields: {required_fields}"}
                if not isinstance(mock_data["tables"], list):
                    return {"valid": False, "error": "tables must be a list"}
                    
            elif mock_type == "websocket":
                required_fields = ["connection_url"]
                if not all(field in mock_data for field in required_fields):
                    return {"valid": False, "error": f"Missing required fields: {required_fields}"}
                if not mock_data["connection_url"].startswith(("ws://", "wss://")):
                    return {"valid": False, "error": "connection_url must start with ws:// or wss://"}
                    
            elif mock_type == "authentication":
                required_fields = ["token", "user_id"]
                if not all(field in mock_data for field in required_fields):
                    return {"valid": False, "error": f"Missing required fields: {required_fields}"}
                if not isinstance(mock_data["roles"], list):
                    return {"valid": False, "error": "roles must be a list"}
                    
            elif mock_type == "file_upload":
                required_fields = ["max_file_size", "allowed_extensions"]
                if not all(field in mock_data for field in required_fields):
                    return {"valid": False, "error": f"Missing required fields: {required_fields}"}
                if not isinstance(mock_data["allowed_extensions"], list):
                    return {"valid": False, "error": "allowed_extensions must be a list"}
                    
            return {"valid": True, "message": "Mock data is valid"}
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
        
    # Code Analysis (Enhanced)
    async def analyze_code(self, request: CodeAnalysisRequest) -> AgentResponse:
        """Analyze code for issues, patterns, and suggestions"""
        try:
            system_prompt = f"""You are an expert code analyzer. Analyze the following {request.language} code and provide:
1. Code quality assessment
2. Potential bugs or issues
3. Performance improvements
4. Best practices recommendations
5. Security concerns
6. Code structure analysis
7. Dependencies and imports analysis
8. Complexity metrics

Code to analyze:
```{request.language}
{request.code}
```

Context: {request.context or "No additional context provided"}

Provide a detailed analysis in JSON format with sections for quality, bugs, performance, best_practices, security, structure, dependencies, and complexity."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please analyze this code thoroughly."}
                ],
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            
            return AgentResponse(
                success=True,
                message="Code analysis completed",
                data={"analysis": analysis}
            )
        except Exception as e:
            logger.error(f"Error in code analysis: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to analyze code",
                error=str(e)
            )
    
    # Code Generation (Enhanced)
    async def generate_code(self, request: CodeGenerationRequest) -> AgentResponse:
        """Generate code based on description"""
        try:
            system_prompt = f"""You are an expert {request.language} developer. Generate clean, efficient, and well-documented code based on the description.

Requirements:
- Language: {request.language}
- Description: {request.description}
- Context: {request.context or "No additional context"}

{("Existing code to extend/modify:\n```" + request.language + "\n" + request.existing_code + "\n```") if request.existing_code else ""}

Provide only the code without explanations, wrapped in code blocks. Include proper error handling, documentation, and follow best practices."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the requested code."}
                ],
                temperature=0.1
            )
            
            generated_code = response.choices[0].message.content
            
            return AgentResponse(
                success=True,
                message="Code generated successfully",
                data={"generated_code": generated_code}
            )
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to generate code",
                error=str(e)
            )
    
    # Test Generation (Enhanced)
    async def generate_tests(self, request: CodeTestGenerationRequest) -> AgentResponse:
        """Generate unit tests for the provided code"""
        try:
            test_framework = request.test_framework or self._get_default_test_framework(request.language)
            
            system_prompt = f"""You are an expert in writing unit tests. Generate comprehensive unit tests for the following {request.language} code.

Code to test:
```{request.language}
{request.code}
```

Test framework: {test_framework}

Requirements:
- Cover all functions/methods
- Test edge cases and error conditions
- Use descriptive test names
- Include setup and teardown if needed
- Mock external dependencies
- Test both positive and negative scenarios
- Include performance tests if applicable

Provide only the test code without explanations."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate comprehensive unit tests."}
                ],
                temperature=0.1
            )
            
            test_code = response.choices[0].message.content
            
            return AgentResponse(
                success=True,
                message="Tests generated successfully",
                data={"test_code": test_code, "test_framework": test_framework}
            )
        except Exception as e:
            logger.error(f"Error in test generation: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to generate tests",
                error=str(e)
            )
    
    # Refactoring (Enhanced)
    async def refactor_code(self, request: RefactoringRequest) -> AgentResponse:
        """Refactor code based on the specified type"""
        try:
            system_prompt = f"""You are an expert code refactoring specialist. Refactor the following {request.language} code for: {request.refactoring_type}

Original code:
```{request.language}
{request.code}
```

Refactoring type: {request.refactoring_type}

Requirements:
- Maintain functionality
- Improve code quality and readability
- Follow best practices and design patterns
- Add proper documentation and comments
- Optimize performance if applicable
- Improve error handling
- Make code more maintainable and testable

Provide the refactored code with a brief explanation of changes made."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Refactor this code according to the specified type."}
                ],
                temperature=0.1
            )
            
            refactored_code = response.choices[0].message.content
            
            return AgentResponse(
                success=True,
                message="Code refactored successfully",
                data={"refactored_code": refactored_code, "refactoring_type": request.refactoring_type}
            )
        except Exception as e:
            logger.error(f"Error in code refactoring: {str(e)}")
            return AgentResponse(
                success=False,
                message="Failed to refactor code",
                error=str(e)
            )
    
    def _get_default_test_framework(self, language: str) -> str:
        """Get default test framework for language"""
        frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "csharp": "nunit",
            "go": "testing",
            "rust": "cargo test",
            "php": "phpunit",
            "ruby": "rspec"
        }
        return frameworks.get(language.lower(), "pytest")

# Initialize agent
agent = DeepAgent()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await handle_websocket_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message: str):
    """Handle incoming WebSocket messages"""
    try:
        data = json.loads(message)
        action = data.get("action")
        
        if action == "analyze_code":
            request = CodeAnalysisRequest(**data.get("data", {}))
            response = await agent.analyze_code(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "generate_code":
            request = CodeGenerationRequest(**data.get("data", {}))
            response = await agent.generate_code(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "generate_tests":
            request = CodeTestGenerationRequest(**data.get("data", {}))
            response = await agent.generate_tests(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "refactor_code":
            request = RefactoringRequest(**data.get("data", {}))
            response = await agent.refactor_code(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "read_file":
            request = FileReadRequest(**data.get("data", {}))
            response = await agent.read_file(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "write_file":
            request = FileWriteRequest(**data.get("data", {}))
            response = await agent.write_file(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "list_directory":
            directory = data.get("data", {}).get("directory")
            response = await agent.list_directory(directory)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "search_text":
            request = SearchRequest(**data.get("data", {}))
            response = await agent.search_text(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "replace_text":
            request = ReplaceRequest(**data.get("data", {}))
            response = await agent.replace_text(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "execute_command":
            request = TerminalRequest(**data.get("data", {}))
            response = await agent.execute_command(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "plan_task":
            request = PlanningRequest(**data.get("data", {}))
            response = await agent.plan_task(request)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        elif action == "create_mock":
            mock_type = data.get("data", {}).get("mock_type", "generic")
            mock_data = data.get("data", {}).get("mock_data", {})
            response = await agent.create_mock(mock_type, mock_data)
            await manager.send_personal_message(json.dumps(response.model_dump()), websocket)
            
        else:
            error_response = AgentResponse(
                success=False,
                message="Unknown action",
                error=f"Action '{action}' not supported"
            )
            await manager.send_personal_message(json.dumps(error_response.model_dump()), websocket)
            
    except json.JSONDecodeError:
        error_response = AgentResponse(
            success=False,
            message="Invalid JSON",
            error="Failed to parse message as JSON"
        )
        await manager.send_personal_message(json.dumps(error_response.model_dump()), websocket)
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {str(e)}")
        error_response = AgentResponse(
            success=False,
            message="Internal error",
            error=str(e)
        )
        await manager.send_personal_message(json.dumps(error_response.model_dump()), websocket)

# REST API Endpoints
@app.get("/")
async def root():
    return {"message": "Deep Agent Backend is running", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "ready"}

@app.post("/api/analyze", response_model=AgentResponse)
async def analyze_code_api(request: CodeAnalysisRequest):
    return await agent.analyze_code(request)

@app.post("/api/generate", response_model=AgentResponse)
async def generate_code_api(request: CodeGenerationRequest):
    return await agent.generate_code(request)

@app.post("/api/tests", response_model=AgentResponse)
async def generate_tests_api(request: CodeTestGenerationRequest):
    return await agent.generate_tests(request)

@app.post("/api/refactor", response_model=AgentResponse)
async def refactor_code_api(request: RefactoringRequest):
    return await agent.refactor_code(request)

@app.post("/api/read-file", response_model=AgentResponse)
async def read_file_api(request: FileReadRequest):
    return await agent.read_file(request)

@app.post("/api/write-file", response_model=AgentResponse)
async def write_file_api(request: FileWriteRequest):
    return await agent.write_file(request)

@app.post("/api/list-directory", response_model=AgentResponse)
async def list_directory_api(directory: str = None):
    return await agent.list_directory(directory)

@app.post("/api/search", response_model=AgentResponse)
async def search_text_api(request: SearchRequest):
    return await agent.search_text(request)

@app.post("/api/replace", response_model=AgentResponse)
async def replace_text_api(request: ReplaceRequest):
    return await agent.replace_text(request)

@app.post("/api/execute", response_model=AgentResponse)
async def execute_command_api(request: TerminalRequest):
    return await agent.execute_command(request)

@app.post("/api/plan", response_model=AgentResponse)
async def plan_task_api(request: PlanningRequest):
    return await agent.plan_task(request)

@app.post("/api/mock", response_model=AgentResponse)
async def create_mock_api(mock_type: str, mock_data: Dict[str, Any]):
    return await agent.create_mock(mock_type, mock_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)