import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Deep Agent Backend", version="1.0.0")

# Initialize OpenAI
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str
    context: Optional[str] = None

class CodeGenerationRequest(BaseModel):
    description: str
    language: str
    context: Optional[str] = None
    existing_code: Optional[str] = None

class TestGenerationRequest(BaseModel):
    code: str
    language: str
    test_framework: Optional[str] = None

class RefactoringRequest(BaseModel):
    code: str
    language: str
    refactoring_type: str  # e.g., "optimize", "clean", "restructure"

class AgentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DeepAgent:
    def __init__(self):
        self.client = client
        
    async def analyze_code(self, request: CodeAnalysisRequest) -> AgentResponse:
        """Analyze code for issues, patterns, and suggestions"""
        try:
            system_prompt = f"""You are an expert code analyzer. Analyze the following {request.language} code and provide:
1. Code quality assessment
2. Potential bugs or issues
3. Performance improvements
4. Best practices recommendations
5. Security concerns

Code to analyze:
```{request.language}
{request.code}
```

Context: {request.context or "No additional context provided"}

Provide a detailed analysis in JSON format with sections for quality, bugs, performance, best_practices, and security."""
            
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
    
    async def generate_code(self, request: CodeGenerationRequest) -> AgentResponse:
        """Generate code based on description"""
        try:
            system_prompt = f"""You are an expert {request.language} developer. Generate clean, efficient, and well-documented code based on the description.

Requirements:
- Language: {request.language}
- Description: {request.description}
- Context: {request.context or "No additional context"}

{("Existing code to extend/modify:\n```" + request.language + "\n" + request.existing_code + "\n```") if request.existing_code else ""}

Provide only the code without explanations, wrapped in code blocks."""
            
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
    
    async def generate_tests(self, request: TestGenerationRequest) -> AgentResponse:
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
- Test edge cases
- Test error conditions
- Use descriptive test names
- Include setup and teardown if needed

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
- Improve code quality
- Follow best practices
- Add proper documentation
- Optimize performance if applicable

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
            "go": "testing"
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
            await manager.send_personal_message(json.dumps(response.dict()), websocket)
            
        elif action == "generate_code":
            request = CodeGenerationRequest(**data.get("data", {}))
            response = await agent.generate_code(request)
            await manager.send_personal_message(json.dumps(response.dict()), websocket)
            
        elif action == "generate_tests":
            request = TestGenerationRequest(**data.get("data", {}))
            response = await agent.generate_tests(request)
            await manager.send_personal_message(json.dumps(response.dict()), websocket)
            
        elif action == "refactor_code":
            request = RefactoringRequest(**data.get("data", {}))
            response = await agent.refactor_code(request)
            await manager.send_personal_message(json.dumps(response.dict()), websocket)
            
        else:
            error_response = AgentResponse(
                success=False,
                message="Unknown action",
                error=f"Action '{action}' not supported"
            )
            await manager.send_personal_message(json.dumps(error_response.dict()), websocket)
            
    except json.JSONDecodeError:
        error_response = AgentResponse(
            success=False,
            message="Invalid JSON",
            error="Failed to parse message as JSON"
        )
        await manager.send_personal_message(json.dumps(error_response.dict()), websocket)
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {str(e)}")
        error_response = AgentResponse(
            success=False,
            message="Internal error",
            error=str(e)
        )
        await manager.send_personal_message(json.dumps(error_response.dict()), websocket)

@app.get("/")
async def root():
    return {"message": "Deep Agent Backend is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)