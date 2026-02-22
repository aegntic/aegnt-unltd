import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentConfig:
    name: str
    model: str = "llama4:70b"
    max_memory_mb: int = 2048
    max_steps: int = 100
    timeout_seconds: int = 300
    tools: List[str] = field(default_factory=lambda: ["terminal", "browser", "memory"])
    auto_evolve: bool = True


@dataclass
class AgentContext:
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    workspace_path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    tools_created: List[str] = field(default_factory=list)


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    status: AgentState = AgentState.IDLE
    result: Optional[Any] = None
    error: Optional[str] = None


class ToolRegistry:
    """Dynamic tool creation and management"""

    def __init__(self):
        self.tools: Dict[str, callable] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self.tools = {
            "web_search": self._web_search,
            "browser_open": self._browser_open,
            "terminal_exec": self._terminal_exec,
            "memory_store": self._memory_store,
            "memory_recall": self._memory_recall,
            "file_read": self._file_read,
            "file_write": self._file_write,
            "code_execute": self._code_execute,
        }

    async def _web_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search the web for information"""
        # Implementation via browser service
        return {"status": "success", "results": [], "query": query}

    async def _browser_open(self, url: str, **kwargs) -> Dict[str, Any]:
        """Open a browser to a URL"""
        return {"status": "success", "url": url, "content": ""}

    async def _terminal_exec(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a terminal command"""
        import subprocess

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    async def _memory_store(self, key: str, value: str, **kwargs) -> Dict[str, Any]:
        """Store information in agent memory"""
        return {"status": "success", "key": key}

    async def _memory_recall(self, query: str, **kwargs) -> Dict[str, Any]:
        """Recall information from memory"""
        return {"status": "success", "query": query, "results": []}

    async def _file_read(self, path: str, **kwargs) -> Dict[str, Any]:
        """Read a file"""
        try:
            with open(path, "r") as f:
                content = f.read()
            return {"status": "success", "path": path, "content": content}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _file_write(self, path: str, content: str, **kwargs) -> Dict[str, Any]:
        """Write to a file"""
        import os

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return {"status": "success", "path": path}

    async def _code_execute(
        self, code: str, language: str = "python", **kwargs
    ) -> Dict[str, Any]:
        """Execute code in sandbox"""
        return {"status": "success", "output": "", "language": language}


class AgentZeroInstance:
    """
    A single Agent Zero instance - fully isolated execution environment
    """

    def __init__(self, config: AgentConfig, instance_id: str = None):
        self.id = instance_id or str(uuid.uuid4())[:8]
        self.config = config
        self.state = AgentState.IDLE
        self.context = AgentContext()
        self.tools = ToolRegistry()
        self.current_task: Optional[Task] = None
        self.execution_log: List[Dict] = []
        logger.info(
            f"Agent {self.config.name} ({self.id}) initialized with model {config.model}"
        )

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task using the Plan-Action-Reflection loop"""
        self.current_task = task
        self.state = AgentState.THINKING
        task.status = AgentState.THINKING

        try:
            # Phase 1: Planning
            plan = await self._plan(task)

            # Phase 2: Execution
            self.state = AgentState.EXECUTING
            task.status = AgentState.EXECUTING
            result = await self._execute_plan(plan, task)

            # Phase 3: Reflection
            await self._reflect(result, task)

            self.state = AgentState.COMPLETED
            task.status = AgentState.COMPLETED
            task.result = result

            return {
                "status": "success",
                "agent_id": self.id,
                "task_id": task.id,
                "result": result,
                "steps": len(self.execution_log),
            }

        except Exception as e:
            self.state = AgentState.ERROR
            task.status = AgentState.ERROR
            task.error = str(e)
            logger.error(f"Agent {self.id} error: {e}")
            return {"status": "error", "error": str(e)}

    async def _plan(self, task: Task) -> Dict[str, Any]:
        """Create a plan for the task"""
        # In production, this calls the LLM
        # For now, return a simple plan structure
        plan = {
            "steps": [
                {
                    "action": "analyze",
                    "description": f"Analyze task: {task.description}",
                },
                {"action": "execute", "description": "Execute the main task"},
                {"action": "verify", "description": "Verify the result"},
            ],
            "estimated_steps": 3,
        }

        self.execution_log.append(
            {"phase": "planning", "timestamp": datetime.now().isoformat(), "plan": plan}
        )

        return plan

    async def _execute_plan(self, plan: Dict, task: Task) -> Any:
        """Execute the plan step by step"""
        results = []

        for i, step in enumerate(plan["steps"]):
            if i >= self.config.max_steps:
                break

            self.execution_log.append(
                {
                    "phase": "execution",
                    "step": i,
                    "action": step["action"],
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Execute step (simplified - real impl would call tools)
            step_result = {"step": i, "action": step["action"], "status": "completed"}
            results.append(step_result)

            await asyncio.sleep(0.1)  # Simulate work

        return {"completed_steps": len(results), "details": results}

    async def _reflect(self, result: Any, task: Task) -> None:
        """Reflect on the execution and evolve if enabled"""
        self.execution_log.append(
            {
                "phase": "reflection",
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }
        )

        if self.config.auto_evolve:
            # In production: analyze failures, create new tools, update strategy
            logger.info(f"Agent {self.id} - Self-evolving enabled, analyzing execution")

    async def create_tool(self, name: str, code: str) -> bool:
        """Dynamically create a new tool"""
        try:
            # Compile and store the tool
            self.context.tools_created.append(name)
            logger.info(f"Agent {self.id} created tool: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create tool {name}: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.config.name,
            "model": self.config.model,
            "state": self.state.value,
            "current_task": self.current_task.id if self.current_task else None,
            "tools_available": len(self.tools.tools),
            "tools_created": len(self.context.tools_created),
            "execution_steps": len(self.execution_log),
        }


class AgentOrchestrator:
    """
    Manages multiple Agent Zero instances with orchestration
    """

    def __init__(self):
        self.agents: Dict[str, AgentZeroInstance] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        logger.info("AgentOrchestrator initialized")

    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent instance"""
        agent = AgentZeroInstance(config)
        self.agents[agent.id] = agent
        logger.info(f"Created agent: {agent.id} ({config.name})")
        return agent.id

    async def execute_task(self, agent_id: str, task: Task) -> Dict[str, Any]:
        """Execute a task on a specific agent"""
        if agent_id not in self.agents:
            return {"status": "error", "error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        return await agent.execute_task(task)

    async def broadcast_task(
        self, task: Task, agent_filter: str = None
    ) -> Dict[str, Any]:
        """Broadcast a task to multiple agents"""
        results = []

        for agent_id, agent in self.agents.items():
            if agent_filter and agent.config.name != agent_filter:
                continue

            result = await agent.execute_task(
                Task(
                    description=f"[Broadcast] {task.description}", context=task.context
                )
            )
            results.append(result)

        return {"status": "success", "results": results}

    def get_agent_status(self, agent_id: str = None) -> List[Dict]:
        """Get status of one or all agents"""
        if agent_id:
            if agent_id in self.agents:
                return [self.agents[agent_id].get_status()]
            return []

        return [agent.get_status() for agent in self.agents.values()]

    async def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Removed agent: {agent_id}")
            return True
        return False


# Example usage
if __name__ == "__main__":

    async def main():
        orchestrator = AgentOrchestrator()

        # Create agents
        researcher_id = await orchestrator.create_agent(
            AgentConfig(
                name="researcher",
                model="llama4:70b",
                tools=["web_search", "browser", "memory"],
            )
        )

        coder_id = await orchestrator.create_agent(
            AgentConfig(
                name="coder", model="qwen3:32b", tools=["terminal", "editor", "git"]
            )
        )

        # Execute task on researcher
        task = Task(description="Find latest developments in quantum computing")

        result = await orchestrator.execute_task(researcher_id, task)
        print(f"Task result: {result}")

        # Check status
        print(f"Agent status: {orchestrator.get_agent_status()}")

    asyncio.run(main())
