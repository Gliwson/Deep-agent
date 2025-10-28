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
from openai import AsyncOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import mimetypes
import tempfile
import threading
import time

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LangGraph Agent Backend", version="2.0.0")

# Initialize OpenAI
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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

# LangGraph Tools
@tool
def read_file_tool(file_path: str) -> str:
    """Read content from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"

@tool
def write_file_tool(file_path: str, content: str) -> str:
    """Write content to a file"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file {file_path}: {str(e)}"

@tool
def search_text_tool(pattern: str, directory: str = "/workspace") -> str:
    """Search for text pattern in files"""
    try:
        results = []
        for file_path in Path(directory).rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern in content:
                            results.append(f"Found in {file_path}")
                except (UnicodeDecodeError, PermissionError):
                    continue
        return f"Search results: {len(results)} files found. {', '.join(results[:5])}"
    except Exception as e:
        return f"Error searching: {str(e)}"

@tool
def execute_command_tool(command: str, working_directory: str = "/workspace") -> str:
    """Execute a terminal command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=30
        )
        return f"Command: {command}\nReturn code: {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}"
    except Exception as e:
        return f"Error executing command: {str(e)}"

@tool
def list_directory_tool(directory: str = "/workspace") -> str:
    """List contents of a directory"""
    try:
        items = []
        for item in Path(directory).iterdir():
            items.append(f"{'DIR' if item.is_dir() else 'FILE'}: {item.name}")
        return f"Directory contents:\n" + "\n".join(items[:20])
    except Exception as e:
        return f"Error listing directory: {str(e)}"

# LangGraph Agent Implementation
class LangGraphAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = [
            read_file_tool,
            write_file_tool,
            search_text_tool,
            execute_command_tool,
            list_directory_tool
        ]
        self.tool_node = ToolNode(self.tools)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self._planning_node)
        workflow.add_node("executor", self._execution_node)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("reviewer", self._review_node)
        
        # Add edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "tools")
        workflow.add_edge("tools", "reviewer")
        workflow.add_conditional_edges(
            "reviewer",
            self._should_continue,
            {
                "continue": "executor",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _planning_node(self, state: AgentState) -> AgentState:
        """Plan the task execution"""
        logger.info("Planning task execution")
        
        system_prompt = f"""You are an expert task planner. Create a detailed execution plan for the following task:

Task: {state['task']}
Context: {state.get('context', {})}

Create a step-by-step plan with:
1. Clear objectives for each step
2. Required tools and actions
3. Expected outcomes
4. Dependencies between steps

Format as JSON with steps array containing: step_number, objective, action, tools_needed, expected_outcome"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Plan this task: {state['task']}")
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            plan_data = json.loads(response.content)
            state['plan'] = plan_data
            state['current_step'] = 0
            state['status'] = "executing"
            state['messages'].append({
                "role": "assistant",
                "content": f"Planning completed. Created {len(plan_data.get('steps', []))} steps."
            })
        except json.JSONDecodeError:
            state['plan'] = {"steps": [{"objective": state['task'], "action": "execute", "tools_needed": []}]}
            state['current_step'] = 0
            state['status'] = "executing"
            state['messages'].append({
                "role": "assistant", 
                "content": "Planning completed with basic structure."
            })
        
        return state
    
    def _execution_node(self, state: AgentState) -> AgentState:
        """Execute the current step of the plan"""
        logger.info(f"Executing step {state['current_step']}")
        
        if not state.get('plan') or not state['plan'].get('steps'):
            state['status'] = "error"
            state['messages'].append({
                "role": "assistant",
                "content": "No plan available for execution"
            })
            return state
        
        steps = state['plan']['steps']
        if state['current_step'] >= len(steps):
            state['status'] = "completed"
            state['messages'].append({
                "role": "assistant",
                "content": "All steps completed successfully"
            })
            return state
        
        current_step = steps[state['current_step']]
        
        # Create execution prompt
        execution_prompt = f"""Execute the following step from the plan:

Step {state['current_step'] + 1}: {current_step.get('objective', 'No objective')}
Action: {current_step.get('action', 'No action specified')}
Tools needed: {current_step.get('tools_needed', [])}

Use the available tools to complete this step. Be specific about what you're doing and why."""

        state['messages'].append({
            "role": "user",
            "content": execution_prompt
        })
        
        return state
    
    def _review_node(self, state: AgentState) -> AgentState:
        """Review the execution results and decide next steps"""
        logger.info("Reviewing execution results")
        
        # Get the last few messages to understand what happened
        recent_messages = state['messages'][-3:] if len(state['messages']) >= 3 else state['messages']
        
        review_prompt = f"""Review the execution results and determine if the current step was completed successfully:

Recent messages: {recent_messages}
Current step: {state['current_step']}
Total steps: {len(state['plan'].get('steps', [])) if state.get('plan') else 0}

Determine if:
1. The current step was completed successfully
2. We should move to the next step
3. We should retry the current step
4. The task is complete

Respond with JSON: {{"step_completed": true/false, "next_action": "continue/retry/end", "reason": "explanation"}}"""

        messages = [
            SystemMessage(content=review_prompt),
            HumanMessage(content="Please review the execution results")
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            review_data = json.loads(response.content)
            
            if review_data.get('step_completed', False):
                state['current_step'] += 1
                state['results'].append({
                    "step": state['current_step'] - 1,
                    "status": "completed",
                    "result": recent_messages[-1] if recent_messages else "No result"
                })
            
            if review_data.get('next_action') == 'end' or state['current_step'] >= len(state['plan'].get('steps', [])):
                state['status'] = "completed"
                state['messages'].append({
                    "role": "assistant",
                    "content": "Task execution completed successfully"
                })
            else:
                state['messages'].append({
                    "role": "assistant",
                    "content": f"Step completed. Moving to next step: {state['current_step'] + 1}"
                })
                
        except json.JSONDecodeError:
            # Default behavior if JSON parsing fails
            state['current_step'] += 1
            if state['current_step'] >= len(state['plan'].get('steps', [])):
                state['status'] = "completed"
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if execution should continue"""
        if state['status'] == "completed":
            return "end"
        elif state['status'] == "error":
            return "end"
        else:
            return "continue"
    
    async def execute_task(self, request: AgentRequest) -> AgentResponse:
        """Execute a task using the LangGraph workflow"""
        try:
            initial_state = AgentState(
                messages=[],
                task=request.task,
                plan=None,
                current_step=0,
                results=[],
                context=request.context or {},
                status="planning"
            )
            
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            return AgentResponse(
                success=final_state['status'] == "completed",
                message=f"Task execution {'completed' if final_state['status'] == 'completed' else 'failed'}",
                data={
                    "status": final_state['status'],
                    "plan": final_state.get('plan'),
                    "results": final_state.get('results', []),
                    "messages": final_state.get('messages', [])
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return AgentResponse(
                success=False,
                message="Task execution failed",
                error=str(e)
            )

# Initialize the agent
agent = LangGraphAgent()

# FastAPI Routes
@app.post("/agent/execute", response_model=AgentResponse)
async def execute_agent_task(request: AgentRequest):
    """Execute a task using the LangGraph agent"""
    return await agent.execute_task(request)

@app.post("/agent/analyze-code", response_model=AgentResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code for issues and suggestions"""
    try:
        system_prompt = f"""Analyze the following {request.language} code and provide:
1. Code quality assessment
2. Potential bugs or issues
3. Performance improvements
4. Best practices recommendations
5. Security concerns

Code to analyze:
```{request.language}
{request.code}
```"""

        response = await client.chat.completions.create(
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
        return AgentResponse(
            success=False,
            message="Code analysis failed",
            error=str(e)
        )

@app.post("/agent/generate-code", response_model=AgentResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code based on description"""
    try:
        system_prompt = f"""Generate clean, efficient, and well-documented {request.language} code based on the description.

Requirements:
- Language: {request.language}
- Description: {request.description}
- Context: {request.context or "No additional context"}

{("Existing code to extend/modify:\n```" + request.language + "\n" + request.existing_code + "\n```") if request.existing_code else ""}

Provide only the code without explanations, wrapped in code blocks."""

        response = await client.chat.completions.create(
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
            message="Code generation completed",
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
                # Execute task using LangGraph agent
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
        "message": "LangGraph Agent Backend",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
