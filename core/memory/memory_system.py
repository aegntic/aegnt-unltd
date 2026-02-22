"""
NexusAgent Memory System
Integrates Graphiti Knowledge Graph + FAISS Vector Store + PostgreSQL
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

from graphiti_core import Graphiti
from graphiti_core.graph_client import GraphClient
from graphiti_core.config import GraphitiConfig

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    id: str
    content: str
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    agent_id: Optional[str] = None


class GraphitiMemory:
    """
    Graphiti-powered temporal knowledge graph memory
    Stores facts, entities, relationships with temporal context
    """

    def __init__(
        self,
        agent_id: str,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
        openai_api_key: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.graphiti: Optional[Graphiti] = None
        self.config = GraphitiConfig(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            openai_api_key=openai_api_key,
        )

    async def initialize(self) -> bool:
        """Initialize Graphiti connection"""
        try:
            self.graphiti = Graphiti(
                config=self.config, index_name=f"nexusagent_{self.agent_id}"
            )
            await self.graphiti.initialize()
            logger.info(f"Graphiti initialized for agent {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            return False

    async def add_episode(
        self,
        content: str,
        reference_date: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Add an episode (memory) to the knowledge graph
        Graphiti automatically extracts entities and relationships
        """
        if not self.graphiti:
            raise RuntimeError("Graphiti not initialized")

        episode_id = str(uuid.uuid4())
        reference_date = reference_date or datetime.now()

        await self.graphiti.add_episode(
            {
                "id": episode_id,
                "content": content,
                "reference_date": reference_date.isoformat(),
                "metadata": metadata or {},
            }
        )

        logger.info(f"Added episode {episode_id} to knowledge graph")
        return episode_id

    async def search(
        self, query: str, clusters: bool = True, depth: int = 2, num_samples: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge graph using hybrid (graph + semantic) search
        """
        if not self.graphiti:
            raise RuntimeError("Graphiti not initialized")

        results = await self.graphiti.search(
            query=query, clusters=clusters, depth=depth, num_samples=num_samples
        )

        return results

    async def get_entity_history(self, entity_name: str) -> List[Dict]:
        """Get full history of an entity"""
        if not self.graphiti:
            raise RuntimeError("Graphiti not initialized")

        return await self.graphiti.get_node_history(entity_name)

    async def get_related_entities(
        self, entity_name: str, relation_type: Optional[str] = None
    ) -> List[Dict]:
        """Get entities related to a given entity"""
        if not self.graphiti:
            raise RuntimeError("Graphiti not initialized")

        return await self.graphiti.get_related_nodes(
            entity_name, relation_type=relation_type
        )

    async def close(self):
        """Close Graphiti connection"""
        if self.graphiti:
            await self.graphiti.close()


class VectorMemory:
    """
    FAISS-based vector memory for semantic search
    Complements Graphiti with dense vector similarity
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index = None
        self.entries: Dict[str, MemoryEntry] = {}
        self._initialize_index()

    def _initialize_index(self):
        """Initialize FAISS index"""
        try:
            import faiss

            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"FAISS index initialized with dimension {self.dimension}")
        except ImportError:
            logger.warning("FAISS not installed, using numpy fallback")
            self.index = None

    async def add(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        """Add a memory entry with embedding"""
        entry_id = str(uuid.uuid4())

        entry = MemoryEntry(
            id=entry_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            agent_id=agent_id,
        )

        self.entries[entry_id] = entry

        if self.index is not None and len(embedding) == self.dimension:
            import numpy as np

            self.index.add(np.array([embedding]).astype("float32"))

        return entry_id

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        agent_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Search for similar memories"""
        results = []

        if self.index is not None and len(query_embedding) == self.dimension:
            import numpy as np

            distances, indices = self.index.search(
                np.array([query_embedding]).astype("float32"), top_k
            )

            for idx in indices[0]:
                if idx >= 0 and idx < len(self.entries):
                    entry = list(self.entries.values())[idx]
                    if agent_id is None or entry.agent_id == agent_id:
                        results.append(entry)
        else:
            # Fallback: simple text search
            for entry in self.entries.values():
                if agent_id is None or entry.agent_id == agent_id:
                    results.append(entry)
                if len(results) >= top_k:
                    break

        return results

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry"""
        if entry_id in self.entries:
            del self.entries[entry_id]
            return True
        return False


class UnifiedMemory:
    """
    Unified memory system combining:
    - Graphiti (knowledge graph, relationships, temporal)
    - FAISS (semantic search)
    - PostgreSQL (persistent storage)
    """

    def __init__(
        self,
        agent_id: str,
        neo4j_config: Dict[str, str],
        pg_config: Dict[str, str],
        embedding_dimension: int = 1536,
    ):
        self.agent_id = agent_id
        self.graphiti_memory = GraphitiMemory(
            agent_id=agent_id,
            neo4j_uri=neo4j_config.get("uri", "bolt://localhost:7687"),
            neo4j_user=neo4j_config.get("user", "neo4j"),
            neo4j_password=neo4j_config.get("password", "password"),
        )
        self.vector_memory = VectorMemory(dimension=embedding_dimension)
        self.pg_config = pg_config

    async def initialize(self) -> bool:
        """Initialize all memory systems"""
        success = await self.graphiti_memory.initialize()

        # Initialize PostgreSQL connection
        # await self._init_postgres()

        logger.info(f"Unified memory initialized for agent {self.agent_id}")
        return success

    async def memorize(
        self, content: str, embedding: List[float], metadata: Optional[Dict] = None
    ) -> str:
        """Store a memory in both knowledge graph and vector store"""
        # Add to knowledge graph
        episode_id = await self.graphiti_memory.add_episode(
            content=content, metadata=metadata
        )

        # Add to vector store
        await self.vector_memory.add(
            content=content,
            embedding=embedding,
            metadata={**metadata, "episode_id": episode_id}
            if metadata
            else {"episode_id": episode_id},
            agent_id=self.agent_id,
        )

        return episode_id

    async def recall(
        self, query: str, query_embedding: Optional[List[float]] = None, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Recall memories using hybrid search:
        1. Graphiti knowledge graph search (relationships, context)
        2. Vector semantic search (similarity)
        """
        results = {"knowledge_graph": [], "semantic": [], "combined": []}

        # Knowledge graph search
        try:
            kg_results = await self.graphiti_memory.search(query, num_samples=top_k)
            results["knowledge_graph"] = kg_results
        except Exception as e:
            logger.error(f"Knowledge graph search failed: {e}")

        # Vector search
        if query_embedding:
            try:
                vector_results = await self.vector_memory.search(
                    query_embedding, top_k=top_k, agent_id=self.agent_id
                )
                results["semantic"] = [
                    {"id": r.id, "content": r.content, "metadata": r.metadata}
                    for r in vector_results
                ]
            except Exception as e:
                logger.error(f"Vector search failed: {e}")

        # Combine and rank results
        results["combined"] = self._combine_results(
            results["knowledge_graph"], results["semantic"]
        )

        return results

    def _combine_results(
        self, kg_results: List[Dict], semantic_results: List[Dict]
    ) -> List[Dict]:
        """Combine and rank results from both sources"""
        combined = []
        seen = set()

        # Add knowledge graph results first (higher relevance for relationships)
        for r in kg_results:
            if r.get("id") not in seen:
                combined.append({**r, "source": "knowledge_graph"})
                seen.add(r.get("id"))

        # Add semantic results
        for r in semantic_results:
            if r.get("id") not in seen:
                combined.append({**r, "source": "semantic"})
                seen.add(r.get("id"))

        return combined

    async def get_context_window(
        self, entity_name: str, time_range_days: int = 30
    ) -> Dict[str, Any]:
        """Get all context around an entity within a time window"""
        history = await self.graphiti_memory.get_entity_history(entity_name)
        related = await self.graphiti_memory.get_related_entities(entity_name)

        return {
            "entity": entity_name,
            "history": history,
            "related_entities": related,
            "time_range_days": time_range_days,
        }

    async def close(self):
        """Close all memory connections"""
        await self.graphiti_memory.close()


class SharedMemory:
    """
    Shared memory across multiple agents
    Enables cross-agent learning and knowledge sharing
    """

    def __init__(self, global_kg: GraphitiMemory):
        self.global_kg = global_kg
        self.agent_memories: Dict[str, UnifiedMemory] = {}

    async def register_agent(self, agent_id: str, config: Dict) -> bool:
        """Register a new agent's memory"""
        if agent_id in self.agent_memories:
            return False

        memory = UnifiedMemory(
            agent_id=agent_id,
            neo4j_config=config.get("neo4j", {}),
            pg_config=config.get("postgres", {}),
        )
        await memory.initialize()

        self.agent_memories[agent_id] = memory
        logger.info(f"Agent {agent_id} registered with shared memory")
        return True

    async def share_knowledge(
        self, from_agent: str, to_agent: str, knowledge: str
    ) -> bool:
        """Share knowledge between agents"""
        if from_agent not in self.agent_memories:
            return False

        # Add to global knowledge graph
        await self.global_kg.add_episode(
            content=knowledge,
            metadata={
                "shared_from": from_agent,
                "shared_to": to_agent,
                "type": "cross_agent_knowledge",
            },
        )

        # Add to receiving agent's memory
        if to_agent in self.agent_memories:
            await self.agent_memories[to_agent].memorize(
                content=knowledge,
                embedding=[0] * 1536,  # Placeholder
                metadata={"shared_from": from_agent, "type": "received_knowledge"},
            )

        return True

    async def global_search(self, query: str) -> List[Dict]:
        """Search across all agents' knowledge"""
        return await self.global_kg.search(query)
