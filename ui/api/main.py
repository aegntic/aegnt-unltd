from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import asyncio

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core"))

from agent.agent_zero import AgentOrchestrator, AgentConfig, Task, AgentState

app = FastAPI(title="NexusAgent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator
orchestrator = AgentOrchestrator()


# Request/Response Models
class CreateAgentRequest(BaseModel):
    name: str
    model: str = "llama4:70b"
    max_memory_mb: int = 2048
    max_steps: int = 100
    tools: List[str] = ["terminal", "browser", "memory"]
    auto_evolve: bool = True


class ExecuteTaskRequest(BaseModel):
    description: str
    context: Dict[str, Any] = {}
    priority: int = 1


class AgentStatus(BaseModel):
    id: str
    name: str
    model: str
    state: str
    current_task: Optional[str] = None
    tools_available: int
    tools_created: int
    execution_steps: int


class TaskStatus(BaseModel):
    id: str
    description: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


# In-memory task storage (use Redis in production)
tasks: Dict[str, Task] = {}


@app.get("/")
async def root():
    return {
        "message": "NexusAgent API",
        "version": "0.1.0",
        "agents_running": len(orchestrator.agents),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "agents": len(orchestrator.agents)}


# Agent Management
@app.post("/api/agents", response_model=Dict[str, str])
async def create_agent(request: CreateAgentRequest):
    """Create a new Agent Zero instance"""
    config = AgentConfig(
        name=request.name,
        model=request.model,
        max_memory_mb=request.max_memory_mb,
        max_steps=request.max_steps,
        tools=request.tools,
        auto_evolve=request.auto_evolve,
    )

    agent_id = await orchestrator.create_agent(config)
    return {"agent_id": agent_id, "status": "created"}


@app.get("/api/agents", response_model=List[AgentStatus])
async def list_agents():
    """List all agent instances"""
    statuses = orchestrator.get_agent_status()
    return [AgentStatus(**s) for s in statuses]


@app.get("/api/agents/{agent_id}", response_model=AgentStatus)
async def get_agent(agent_id: str):
    """Get status of a specific agent"""
    statuses = orchestrator.get_agent_status(agent_id)
    if not statuses:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentStatus(**statuses[0])


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Remove an agent instance"""
    success = await orchestrator.remove_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "deleted", "agent_id": agent_id}


# Task Execution
@app.post("/api/agents/{agent_id}/execute", response_model=TaskStatus)
async def execute_task(agent_id: str, request: ExecuteTaskRequest):
    """Execute a task on a specific agent"""
    task = Task(
        description=request.description,
        context=request.context,
        priority=request.priority,
    )
    tasks[task.id] = task

    result = await orchestrator.execute_task(agent_id, task)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))

    return TaskStatus(
        id=task.id,
        description=task.description,
        status=task.status.value,
        result=task.result,
        error=task.error,
    )


@app.post("/api/agents/broadcast", response_model=Dict)
async def broadcast_task(
    request: ExecuteTaskRequest, agent_filter: Optional[str] = None
):
    """Broadcast a task to multiple agents"""
    task = Task(description=request.description, context=request.context)
    tasks[task.id] = task

    result = await orchestrator.broadcast_task(task, agent_filter)
    return result


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
async def get_task(task_id: str):
    """Get status of a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    return TaskStatus(
        id=task.id,
        description=task.description,
        status=task.status.value,
        result=task.result,
        error=task.error,
    )


# Model Management
@app.get("/api/models")
async def list_models():
    """List available models (queries Ollama)"""
    # In production, this would query the Ollama API
    return {
        "available_models": [
            {"name": "llama4:70b", "context": 1000000, "status": "ready"},
            {"name": "llama4:8b", "context": 1000000, "status": "ready"},
            {"name": "qwen3:32b", "context": 128000, "status": "ready"},
            {"name": "qwen3:8b", "context": 128000, "status": "ready"},
            {"name": "mistral-large", "context": 128000, "status": "ready"},
            {"name": "gemma3:27b", "context": 128000, "status": "ready"},
        ],
        "ollama_url": "http://ollama:11434",
    }


# Orchestrator Info
@app.get("/api/orchestrator")
async def get_orchestrator_status():
    """Get overall orchestrator status"""
    return {
        "total_agents": len(orchestrator.agents),
        "queued_tasks": orchestrator.task_queue.qsize(),
        "active_agents": sum(
            1 for a in orchestrator.agents.values() if a.state != AgentState.IDLE
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
