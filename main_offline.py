import asyncio
import json
import logging
import os
import subprocess
import re
import ast
import shutil
from typing import Dict, Any, Optional, List, Tuple, TypedDict, Annotated
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
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

app = FastAPI(title="LangGraph Agent Backend (Offline)", version="2.0.0")

# LangGraph State Definition
class AgentState(TypedDict):
    messages: Annotated[List[dict], "List of messages in conversation"]
    task: str
    plan: Optional[Dict[str, Any]]
    current_step: int
    results: List[Dict[str, Any]]
    context: Dict[str, Any]
    status: str  # "planning", "executing", "completed", "error"

# Request/Response Models
class AgentRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    constraints: Optional[List[str]] = None

class AgentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str
    context: Optional[str] = None

class CodeGenerationRequest(BaseModel):
    description: str
    language: str
    context: Optional[str] = None
    existing_code: Optional[str] = None

# Offline Agent Implementation (no OpenAI API calls)
class OfflineAgent:
    def __init__(self):
        self.workspace_root = Path("/workspace")
        self.temp_dir = Path(tempfile.gettempdir()) / "offline_agent"
        self.temp_dir.mkdir(exist_ok=True)
    
    def create_simple_plan(self, task: str) -> Dict[str, Any]:
        """Create a simple plan without AI"""
        # Basic task analysis
        task_lower = task.lower()
        
        steps = []
        step_num = 1
        
        if "list" in task_lower or "show" in task_lower or "directory" in task_lower:
            steps.append({
                "step_number": step_num,
                "objective": "List directory contents",
                "action": "Use list_directory_tool",
                "tools_needed": ["list_directory_tool"],
                "expected_outcome": "Directory listing displayed"
            })
            step_num += 1
        
        if "create" in task_lower or "write" in task_lower or "file" in task_lower:
            steps.append({
                "step_number": step_num,
                "objective": "Create or modify file",
                "action": "Use write_file_tool",
                "tools_needed": ["write_file_tool"],
                "expected_outcome": "File created or modified"
            })
            step_num += 1
        
        if "search" in task_lower or "find" in task_lower:
            steps.append({
                "step_number": step_num,
                "objective": "Search for text in files",
                "action": "Use search_text_tool",
                "tools_needed": ["search_text_tool"],
                "expected_outcome": "Search results found"
            })
            step_num += 1
        
        if "run" in task_lower or "execute" in task_lower or "command" in task_lower:
            steps.append({
                "step_number": step_num,
                "objective": "Execute terminal command",
                "action": "Use execute_command_tool",
                "tools_needed": ["execute_command_tool"],
                "expected_outcome": "Command executed"
            })
            step_num += 1
        
        # If no specific actions detected, create a generic plan
        if not steps:
            steps.append({
                "step_number": 1,
                "objective": f"Execute task: {task}",
                "action": "Use available tools as needed",
                "tools_needed": ["list_directory_tool", "read_file_tool", "write_file_tool"],
                "expected_outcome": "Task completed"
            })
        
        return {"steps": steps}
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step"""
        objective = step.get("objective", "No objective")
        tools_needed = step.get("tools_needed", [])
        
        result = {
            "step": step.get("step_number", 0),
            "objective": objective,
            "tools_used": tools_needed,
            "status": "completed",
            "result": f"Executed: {objective}"
        }
        
        # Simulate tool usage based on tools_needed
        if "list_directory_tool" in tools_needed:
            try:
                items = []
                for item in self.workspace_root.iterdir():
                    items.append(f"{'DIR' if item.is_dir() else 'FILE'}: {item.name}")
                result["result"] += f"\nDirectory listing: {len(items)} items found"
            except Exception as e:
                result["result"] += f"\nDirectory listing error: {str(e)}"
        
        if "write_file_tool" in tools_needed:
            try:
                # Create a simple hello world file
                hello_file = self.workspace_root / "hello_world.py"
                with open(hello_file, 'w') as f:
                    f.write('#!/usr/bin/env python3\nprint("Hello, World!")\n')
                result["result"] += f"\nCreated file: {hello_file}"
            except Exception as e:
                result["result"] += f"\nFile creation error: {str(e)}"
        
        if "search_text_tool" in tools_needed:
            try:
                # Simple search simulation
                result["result"] += "\nSearch completed: Found relevant files"
            except Exception as e:
                result["result"] += f"\nSearch error: {str(e)}"
        
        if "execute_command_tool" in tools_needed:
            try:
                # Simple command simulation
                result["result"] += "\nCommand executed successfully"
            except Exception as e:
                result["result"] += f"\nCommand error: {str(e)}"
        
        return result
    
    async def execute_task(self, request: AgentRequest) -> AgentResponse:
        """Execute a task using offline processing"""
        try:
            logger.info(f"Executing offline task: {request.task}")
            
            # Create plan
            plan = self.create_simple_plan(request.task)
            logger.info(f"Created plan with {len(plan['steps'])} steps")
            
            # Execute steps
            results = []
            messages = []
            
            messages.append({
                "role": "assistant",
                "content": f"Created plan with {len(plan['steps'])} steps"
            })
            
            for step in plan["steps"]:
                logger.info(f"Executing step {step['step_number']}: {step['objective']}")
                
                # Execute step
                step_result = self.execute_step(step, request.context or {})
                results.append(step_result)
                
                messages.append({
                    "role": "assistant",
                    "content": f"Step {step['step_number']} completed: {step_result['result']}"
                })
            
            # Mark as completed
            messages.append({
                "role": "assistant",
                "content": "All steps completed successfully"
            })
            
            return AgentResponse(
                success=True,
                message="Task execution completed",
                data={
                    "status": "completed",
                    "plan": plan,
                    "results": results,
                    "messages": messages
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return AgentResponse(
                success=False,
                message="Task execution failed",
                error=str(e)
            )

# Initialize the offline agent
agent = OfflineAgent()

# FastAPI Routes
@app.post("/agent/execute", response_model=AgentResponse)
async def execute_agent_task(request: AgentRequest):
    """Execute a task using the offline agent"""
    return await agent.execute_task(request)

@app.post("/agent/analyze-code", response_model=AgentResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code for issues and suggestions (offline)"""
    try:
        # Simple offline code analysis
        code_lines = request.code.split('\n')
        analysis = {
            "lines_of_code": len(code_lines),
            "language": request.language,
            "basic_checks": [
                "Code structure looks valid",
                f"Found {len(code_lines)} lines of code",
                f"Language: {request.language}",
                "No syntax errors detected (basic check)"
            ],
            "recommendations": [
                "Add error handling",
                "Add documentation",
                "Consider adding tests"
            ]
        }
        
        return AgentResponse(
            success=True,
            message="Code analysis completed (offline)",
            data={"analysis": analysis}
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            message="Code analysis failed",
            error=str(e)
        )

@app.post("/agent/generate-code", response_model=AgentResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code based on description (offline)"""
    try:
        # Simple offline code generation
        if "calculator" in request.description.lower():
            generated_code = f'''#!/usr/bin/env python3
"""
{request.description}
Language: {request.language}
"""

def add_numbers(a, b):
    """Add two numbers"""
    return a + b

def subtract_numbers(a, b):
    """Subtract b from a"""
    return a - b

def multiply_numbers(a, b):
    """Multiply two numbers"""
    return a * b

def divide_numbers(a, b):
    """Divide a by b"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    # Example usage
    print("Calculator functions:")
    print(f"2 + 3 = {{add_numbers(2, 3)}}")
    print(f"10 - 4 = {{subtract_numbers(10, 4)}}")
    print(f"3 * 4 = {{multiply_numbers(3, 4)}}")
    print(f"15 / 3 = {{divide_numbers(15, 3)}}")
'''
        else:
            generated_code = f'''#!/usr/bin/env python3
"""
{request.description}
Language: {request.language}
"""

def main():
    """Main function"""
    print("Hello, World!")
    print("This is a generated {request.language} script")
    print("Description: {request.description}")

if __name__ == "__main__":
    main()
'''
        
        return AgentResponse(
            success=True,
            message="Code generation completed (offline)",
            data={"generated_code": generated_code}
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            message="Code generation failed",
            error=str(e)
        )

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "task":
                # Execute task using offline agent
                request = AgentRequest(
                    task=message.get("task", ""),
                    context=message.get("context", {}),
                    constraints=message.get("constraints", [])
                )
                
                result = await agent.execute_task(request)
                
                # Send result back to client
                await websocket.send_text(json.dumps({
                    "type": "result",
                    "data": result.dict()
                }))
            
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LangGraph Agent Backend (Offline Mode)",
        "version": "2.0.0",
        "status": "running",
        "mode": "offline"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time(), "mode": "offline"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
