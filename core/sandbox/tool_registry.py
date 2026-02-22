"""
NexusAgent Tool Registry
Dynamic tool creation and management for agents
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    code: str  # Python code for the tool
    created_by: str  # agent_id
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 1.0


@dataclass
class ToolExecution:
    tool_id: str
    agent_id: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class ToolRegistry:
    """
    Dynamic tool registry with auto-creation capabilities
    Tools can be created by agents at runtime
    """

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.executions: List[ToolExecution] = []
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register built-in tools"""
        builtin_tools = [
            {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "default": 5},
                },
                "code": """
async def execute(query: str, num_results: int = 5):
    # Web search implementation
    return {"results": [], "query": query}
""",
            },
            {
                "name": "browser_navigate",
                "description": "Navigate to a URL in the browser",
                "parameters": {
                    "url": {"type": "string", "description": "URL to navigate to"}
                },
                "code": """
async def execute(url: str):
    return {"status": "navigated", "url": url}
""",
            },
            {
                "name": "terminal_exec",
                "description": "Execute a terminal command",
                "parameters": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout": {"type": "integer", "default": 60},
                },
                "code": """
async def execute(command: str, timeout: int = 60):
    import subprocess
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }
""",
            },
            {
                "name": "file_read",
                "description": "Read a file from the filesystem",
                "parameters": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "code": """
async def execute(path: str):
    with open(path, 'r') as f:
        content = f.read()
    return {"content": content, "path": path}
""",
            },
            {
                "name": "file_write",
                "description": "Write content to a file",
                "parameters": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "code": """
async def execute(path: str, content: str):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    return {"status": "written", "path": path}
""",
            },
            {
                "name": "memory_store",
                "description": "Store information in agent memory",
                "parameters": {
                    "key": {"type": "string", "description": "Memory key"},
                    "value": {"type": "string", "description": "Value to store"},
                },
                "code": """
async def execute(key: str, value: str):
    return {"status": "stored", "key": key}
""",
            },
            {
                "name": "memory_recall",
                "description": "Recall information from agent memory",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "code": """
async def execute(query: str):
    return {"results": [], "query": query}
""",
            },
            {
                "name": "code_execute",
                "description": "Execute Python code in sandbox",
                "parameters": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "language": {"type": "string", "default": "python"},
                },
                "code": """
async def execute(code: str, language: str = "python"):
    # Sandbox execution
    return {"output": "", "language": language}
""",
            },
            {
                "name": "create_agent",
                "description": "Create a new agent instance",
                "parameters": {
                    "name": {"type": "string", "description": "Agent name"},
                    "model": {"type": "string", "description": "Model to use"},
                },
                "code": """
async def execute(name: str, model: str = "llama4:70b"):
    return {"status": "created", "name": name, "model": model}
""",
            },
            {
                "name": "http_request",
                "description": "Make an HTTP request",
                "parameters": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "default": "GET"},
                    "headers": {"type": "object", "default": {}},
                    "body": {"type": "object", "default": None},
                },
                "code": """
async def execute(url: str, method: str = "GET", headers: dict = None, body: dict = None):
    import httpx
    response = httpx.request(method, url, headers=headers or {}, json=body)
    return {
        "status": response.status_code,
        "body": response.text,
        "headers": dict(response.headers)
    }
""",
            },
        ]

        for tool in builtin_tools:
            self.register_tool(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["parameters"],
                code=tool["code"],
                created_by="system",
            )

        logger.info(f"Registered {len(builtin_tools)} built-in tools")

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        code: str,
        created_by: str,
    ) -> str:
        """Register a new tool"""
        tool_id = str(uuid.uuid4())

        tool = ToolDefinition(
            id=tool_id,
            name=name,
            description=description,
            parameters=parameters,
            code=code,
            created_by=created_by,
        )

        self.tools[tool_id] = tool
        logger.info(f"Tool registered: {name} ({tool_id})")

        return tool_id

    async def execute_tool(
        self, tool_id: str, agent_id: str, arguments: Dict[str, Any]
    ) -> ToolExecution:
        """Execute a tool"""
        start_time = datetime.now()

        if tool_id not in self.tools:
            return ToolExecution(
                tool_id=tool_id,
                agent_id=agent_id,
                arguments=arguments,
                error=f"Tool {tool_id} not found",
            )

        tool = self.tools[tool_id]

        try:
            # Execute the tool code
            # In production, this would run in a sandbox
            result = {"status": "executed", "tool": tool.name}

            execution = ToolExecution(
                tool_id=tool_id,
                agent_id=agent_id,
                arguments=arguments,
                result=result,
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )

            tool.usage_count += 1
            self.executions.append(execution)

            return execution

        except Exception as e:
            execution = ToolExecution(
                tool_id=tool_id,
                agent_id=agent_id,
                arguments=arguments,
                error=str(e),
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )

            tool.usage_count += 1
            self.executions.append(execution)

            return execution

    def get_tools(
        self, created_by: Optional[str] = None, search: Optional[str] = None
    ) -> List[ToolDefinition]:
        """Get tools with optional filtering"""
        tools = list(self.tools.values())

        if created_by:
            tools = [t for t in tools if t.created_by == created_by]

        if search:
            search_lower = search.lower()
            tools = [
                t
                for t in tools
                if search_lower in t.name.lower()
                or search_lower in t.description.lower()
            ]

        return tools

    def get_tool_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        total_executions = len(self.executions)
        successful = sum(1 for e in self.executions if not e.error)

        tool_stats = {}
        for tool in self.tools.values():
            tool_executions = [e for e in self.executions if e.tool_id == tool.id]
            tool_success = sum(1 for e in tool_executions if not e.error)

            tool_stats[tool.name] = {
                "usage_count": tool.usage_count,
                "success_rate": tool_success / tool.usage_count
                if tool.usage_count > 0
                else 0,
                "created_by": tool.created_by,
            }

        return {
            "total_tools": len(self.tools),
            "total_executions": total_executions,
            "success_rate": successful / total_executions
            if total_executions > 0
            else 0,
            "tools": tool_stats,
        }


class ToolCreator:
    """
    AI-powered tool creation from natural language
    Analyzes task patterns and generates new tools
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def create_tool_from_task(
        self, agent_id: str, task_description: str, parameters: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a tool based on task analysis
        In production, this would use an LLM to generate tool code
        """
        tool_name = f"tool_{len(self.registry.tools) + 1}"

        # Generate tool code (simplified - real impl would use LLM)
        code = f"""
async def execute(**kwargs):
    # Auto-generated tool for: {task_description}
    return {{"status": "executed", "task": "{task_description}"}}
"""

        tool_id = self.registry.register_tool(
            name=tool_name,
            description=task_description,
            parameters=parameters,
            code=code,
            created_by=agent_id,
        )

        return tool_id
