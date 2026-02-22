"""
NexusAgent Enhanced Agent
Full-featured Agent Zero implementation with memory, tools, and self-evolution
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .agent_zero import AgentZeroInstance, AgentConfig, Task, AgentState
from ..memory.memory_system import UnifiedMemory, GraphitiMemory, VectorMemory
from ..sandbox.tool_registry import ToolRegistry, ToolExecution
from ..sandbox.browser import BrowserController


@dataclass
class EvolutionRecord:
    """Record of agent self-evolution"""
    timestamp: datetime
    trigger: str  # What triggered the evolution
    changes: Dict[str, Any]
    success: bool


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    tools_created: int = 0
    tools_used: int = 0
    memory_entries: int = 0
    avg_execution_time_ms: int = 0
    success_rate: float = 1.0


class EnhancedAgentZero(AgentZeroInstance):
    """
    Enhanced Agent Zero with:
    - Full memory system (Graphiti + FAISS)
    - Dynamic tool creation
    - Browser automation
    - Self-evolution
    - Performance metrics
    """
    
    def __init__(
        self,
        config: AgentConfig,
        instance_id: str = None,
        neo4j_config: Optional[Dict] = None,
        pg_config: Optional[Dict] = None
    ):
        super().__init__(config, instance_id)
        
        # Initialize memory system
        self.memory: Optional[UnifiedMemory] = None
        self.neo4j_config = neo4j_config or {}
        self.pg_config = pg_config or {}
        
        # Initialize tools
        self.tools = ToolRegistry()
        
        # Initialize browser
        self.browser: Optional[BrowserController] = None
        
        # Evolution and metrics
        self.evolution_history: List[EvolutionRecord] = []
        self.metrics = AgentMetrics()
        
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all agent components"""
        if self._initialized:
            return True
        
        try:
            # Initialize memory
            if self.neo4j_config:
                self.memory = UnifiedMemory(
                    agent_id=self.id,
                    neo4j_config=self.neo4j_config,
                    pg_config=self.pg_config
                )
                await self.memory.initialize()
            
            # Initialize browser
            self.browser = BrowserController()
            await self.browser.initialize()
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize agent: {e}")
            return False
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute task with full agent capabilities"""
        start_time = datetime.now()
        
        # Store task context in memory
        if self.memory:
            await self.memory.memorize(
                content=f"Task started: {task.description}",
                embedding=[0] * 1536,  # Placeholder
                metadata={"task_id": task.id, "status": "started"}
            )
        
        try:
            # Phase 1: Think - analyze task and plan
            plan = await self._think(task)
            
            # Phase 2: Act - execute with tools
            result = await self._act(plan, task)
            
            # Phase 3: Reflect - analyze and evolve
            reflection = await self._reflect(result, task)
            
            # Store result in memory
            if self.memory:
                await self.memory.memorize(
                    content=f"Task completed: {task.description} -> {result}",
                    embedding=[0] * 1536,
                    metadata={"task_id": task.id, "status": "completed"}
                )
            
            # Update metrics
            self.metrics.tasks_completed += 1
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._update_metrics(execution_time)
            
            # Check for self-evolution
            if reflection.get("should_evolve"):
                await self._evolve(reflection)
            
            return {
                "status": "success",
                "agent_id": self.id,
                "task_id": task.id,
                "plan": plan,
                "result": result,
                "reflection": reflection,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            self.metrics.tasks_failed += 1
            return {
                "status": "error",
                "agent_id": self.id,
                "task_id": task.id,
                "error": str(e)
            }
    
    async def _think(self, task: Task) -> Dict[str, Any]:
        """Analyze task and create execution plan"""
        self.state = AgentState.THINKING
        
        # Check relevant memory
        relevant_context = []
        if self.memory:
            memory_results = await self.memory.recall(task.description)
            relevant_context = memory_results.get("combined", [])[:3]
        
        # Create plan using available tools
        available_tools = self.tools.get_tools(created_by=self.id)
        
        plan = {
            "task": task.description,
            "context": relevant_context,
            "steps": [
                {"action": "analyze", "description": "Analyze task requirements"},
                {"action": "gather", "description": "Gather necessary information"},
                {"action": "execute", "description": "Execute main task"},
                {"action": "verify", "description": "Verify results"}
            ],
            "tools_needed": [t.name for t in available_tools[:5]],
            "estimated_steps": 4
        }
        
        self.execution_log.append({
            "phase": "think",
            "timestamp": datetime.now().isoformat(),
            "plan": plan
        })
        
        return plan
    
    async def _act(self, plan: Dict, task: Task) -> Any:
        """Execute the plan using tools"""
        self.state = AgentState.EXECUTING
        results = []
        
        for i, step in enumerate(plan["steps"]):
            # Find appropriate tool for step
            tool_name = self._select_tool(step["action"])
            
            if tool_name:
                # Execute tool
                execution = await self.tools.execute_tool(
                    tool_id=tool_name,
                    agent_id=self.id,
                    arguments={"task": task.description, "step": step}
                )
                
                results.append({
                    "step": i,
                    "action": step["action"],
                    "tool": tool_name,
                    "result": execution.result,
                    "success": not execution.error
                })
                
                self.metrics.tools_used += 1
            else:
                # No tool needed, just log
                results.append({
                    "step": i,
                    "action": step["action"],
                    "result": "completed"
                })
        
        return {"steps_completed": len(results), "details": results}
    
    async def _reflect(self, result: Any, task: Task) -> Dict[str, Any]:
        """Reflect on execution and determine if evolution needed"""
        self.state = AgentState.IDLE
        
        # Analyze execution
        steps = result.get("details", [])
        failed_steps = [s for s in steps if not s.get("success", True)]
        
        reflection = {
            "total_steps": len(steps),
            "failed_steps": len(failed_steps),
            "should_evolve": len(failed_steps) > len(steps) / 2,
            "success_rate": 1 - (len(failed_steps) / len(steps)) if steps else 1,
            "insights": []
        }
        
        # Generate insights
        if failed_steps:
            reflection["insights"].append(
                f"Failed {len(failed_steps)} steps - consider creating new tools"
            )
        
        if reflection["success_rate"] > 0.9:
            reflection["insights"].append(
                "High success rate - consider generalizing this approach"
            )
        
        self.execution_log.append({
            "phase": "reflect",
            "timestamp": datetime.now().isoformat(),
            "reflection": reflection
        })
        
        return reflection
    
    async def _evolve(self, reflection: Dict) -> bool:
        """Self-evolve based on reflection"""
        should_evolve = reflection.get("should_evolve", False)
        
        if not should_evolve:
            return False
        
        # Record evolution
        evolution = EvolutionRecord(
            timestamp=datetime.now(),
            trigger="low_success_rate",
            changes={
                "new_tools_created": 0,
                "strategy_changed": True
            },
            success=True
        )
        
        # Create new tool based on failed steps
        new_tool_id = self.tools.register_tool(
            name=f"autogen_{len(self.tools.tools)}",
            description=f"Auto-generated tool after evolution",
            parameters={"input": {"type": "string"}},
            code="async def execute(**kwargs): return {'status': 'success'}",
            created_by=self.id
        )
        
        evolution.changes["new_tools_created"] = 1
        self.metrics.tools_created += 1
        
        self.evolution_history.append(evolution)
        
        return True
    
    def _select_tool(self, action: str) -> Optional[str]:
        """Select appropriate tool for action"""
        action_tool_map = {
            "analyze": "memory_recall",
            "gather": "web_search",
            "execute": "code_execute",
            "verify": "memory_store"
        }
        
        tool_name = action_tool_map.get(action)
        if not tool_name:
            return None
        
        # Find tool ID by name
        for tool_id, tool in self.tools.tools.items():
            if tool.name == tool_name:
                return tool_id
        
        return None
    
    def _update_metrics(self, execution_time_ms: int):
        """Update performance metrics"""
        total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
        if total_tasks > 0:
            self.metrics.success_rate = self.metrics.tasks_completed / total_tasks
        
        # Update average execution time
        if self.metrics.tasks_completed > 1:
            prev_avg = self.metrics.avg_execution_time_ms
            self.metrics.avg_execution_time_ms = int(
                (prev_avg * (self.metrics.tasks_completed - 1) + execution_time_ms) 
                / self.metrics.tasks_completed
            )
        else:
            self.metrics.avg_execution_time_ms = execution_time_ms
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        base_status = self.get_status()
        
        return {
            **base_status,
            "memory": {
                "enabled": self.memory is not None,
                "entries": self.metrics.memory_entries
            },
            "tools": {
                "available": len(self.tools.tools),
                "created": self.metrics.tools_created,
                "used": self.metrics.tools_used
            },
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": self.metrics.success_rate,
                "avg_execution_time_ms": self.metrics.avg_execution_time_ms
            },
            "evolution": {
                "history_count": len(self.evolution_history),
                "last_evolution": self.evolution_history[-1].timestamp.isoformat() 
                    if self.evolution_history else None
                }
            },
            "initialized": self._initialized
        }
    
    async def recall_memory(self, query: str) -> Dict[str, Any]:
        """Search agent memory"""
        if not self.memory:
            return {"error": "Memory not initialized"}
        
        return await self.memory.recall(query)
    
    async def close(self):
        """Clean up agent resources"""
        if self.memory:
            await self.memory.close()
        
        if self.browser:
            await self.browser.close_session()


class MultiAgentOrchestrator:
    """
    Orchestrates multiple enhanced agents with:
    - Task distribution
    - Cross-agent communication
    - Shared knowledge
    - Load balancing
    """
    
    def __init__(self):
        self.agents: Dict[str, EnhancedAgentZero] = {}
        self.shared_memory: Optional[GraphitiMemory] = None
        self._task_queues: Dict[str, asyncio.Queue] = {}
    
    async def create_agent(
        self,
        config: AgentConfig,
        neo4j_config: Optional[Dict] = None,
        pg_config: Optional[Dict] = None
    ) -> str:
        """Create a new enhanced agent"""
        agent = EnhancedAgentZero(
            config=config,
            neo4j_config=neo4j_config,
            pg_config=pg_config
        )
        await agent.initialize()
        
        self.agents[agent.id] = agent
        self._task_queues[agent.id] = asyncio.Queue()
        
        return agent.id
    
    async def execute_parallel(
        self,
        tasks: List[Task],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Execute tasks in parallel across agents"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_limit(agent_id: str, task: Task):
            async with semaphore:
                if agent_id in self.agents:
                    return await self.agents[agent_id].execute_task(task)
                return {"error": f"Agent {agent_id} not found"}
        
        # Distribute tasks across agents round-robin
        agent_ids = list(self.agents.keys())
        
        coros = [
            execute_with_limit(agent_ids[i % len(agent_ids)], task)
            for i, task in enumerate(tasks)
        ]
        
        results = await asyncio.gather(*coros, return_exceptions=True)
        return results
    
    async def share_knowledge(
        self,
        from_agent_id: str,
        to_agent_id: str,
        knowledge: str
    ) -> bool:
        """Share knowledge between agents"""
        if from_agent_id not in self.agents or to_agent_id not in self.agents:
            return False
        
        # Add to shared memory
        if self.shared_memory:
            await self.shared_memory.add_episode(
                content=knowledge,
                metadata={
                    "shared_from": from_agent_id,
                    "shared_to": to_agent_id,
                    "type": "cross_agent"
                }
            )
        
        # Add to receiving agent's memory
        await self.agents[to_agent_id].memory.memorize(
            content=knowledge,
            embedding=[0] * 1536,
            metadata={"shared_from": from_agent_id}
        )
        
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of entire multi-agent system"""
        agent_statuses = [a.get_full_status() for a in self.agents.values()]
        
        return {
            "total_agents": len(self.agents),
            "active_agents": sum(1 for s in agent_statuses if s["state"] != "idle"),
            "total_tasks_completed": sum(s["metrics"]["tasks_completed"] for s in agent_statuses),
            "total_tools_created": sum(s["tools"]["created"] for s in agent_statuses),
            "average_success_rate": sum(s["metrics"]["success_rate"] for s in agent_statuses) / len(agent_statuses) if agent_statuses else 0,
            "agents": agent_statuses
        }
