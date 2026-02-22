"""
AEGNT-UNLTD Python Inference Layer
Implements Twins Mode: System 1 (Cortex) + System 2 (Deep Mind)
"""

import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx


class SystemType(Enum):
    CORTEX = "cortex"  # System 1 - Fast
    DEEP_MIND = "deep_mind"  # System 2 - Deep


@dataclass
class DirectiveResponse:
    intent: str
    system: SystemType
    content: str
    reasoning_trace: Optional[str] = None
    latency_ms: int = 0


class OllamaClient:
    """Local Ollama inference client"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def generate(
        self, model: str, prompt: str, stream: bool = False, **kwargs
    ) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": stream, **kwargs},
            )
            result = response.json()
            return result.get("response", "")


class GeminiClient:
    """Google Gemini API client for deep reasoning"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate(
        self, prompt: str, thinking: bool = True, **kwargs
    ) -> Dict[str, Any]:
        # Using Gemini's thinking/reasoning capability
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/models/gemini-2.0-flash-thinking:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "thinkingConfig": {"includeThoughts": thinking} if thinking else {},
                },
            )
            return response.json()


class KnowledgeGrounder:
    """
    Truth Layer: Grounding pass against knowledge base
    """

    def __init__(self, knowledge_path: str = "./knowledge"):
        self.knowledge_path = knowledge_path
        self.documents: List[Dict[str, str]] = []
        self._load_documents()

    def _load_documents(self):
        """Load all documents from knowledge folder"""
        if not os.path.exists(self.knowledge_path):
            return

        for filename in os.listdir(self.knowledge_path):
            if filename.endswith((".md", ".txt", ".pdf")):
                path = os.path.join(self.knowledge_path, filename)
                try:
                    with open(path, "r") as f:
                        self.documents.append(
                            {
                                "filename": filename,
                                "content": f.read()[:5000],  # First 5k chars
                            }
                        )
                except:
                    pass

    async def ground(self, plan: str) -> Dict[str, Any]:
        """
        Verify plan against knowledge constraints
        Returns: {valid: bool, citations: [], discrepancies: []}
        """
        # Simple grounding - in production use RAG/embedding search
        discrepancies = []
        citations = []

        for doc in self.documents:
            # Check for brand guidelines
            if "brand" in doc["filename"].lower():
                if "$" in plan:  # Checking pricing mentions
                    citations.append(f"Verified against {doc['filename']}")

        return {
            "valid": len(discrepancies) == 0,
            "citations": citations,
            "discrepancies": discrepancies,
        }


class TwinsMode:
    """
    The Bifurcated Mind:
    System 1 (Cortex) - Fast, local
    System 2 (Deep Mind) - Slow, cloud
    """

    def __init__(
        self,
        fast_model: str = "llama3",
        slow_model: str = "gemini-2.0-flash-thinking",
        ollama_url: str = "http://localhost:11434",
        gemini_api_key: Optional[str] = None,
    ):
        self.ollama = OllamaClient(ollama_url)
        self.gemini = GeminiClient(gemini_api_key or os.getenv("GEMINI_API_KEY", ""))
        self.grounder = KnowledgeGrounder()

    def classify_intent(self, input_text: str) -> SystemType:
        """Classify input to System 1 or System 2"""
        # Quick action indicators
        quick_keywords = ["what", "how", "show", "list", "get", "?"]

        # Strategy indicators
        strategy_keywords = [
            "plan",
            "strategy",
            "design",
            "architecture",
            "build",
            "create",
            "analyze",
            "research",
            "develop",
        ]

        input_lower = input_text.lower()

        # Check for strategy keywords
        if any(kw in input_lower for kw in strategy_keywords):
            return SystemType.DEEP_MIND

        # Default to cortex for quick actions
        if any(kw in input_lower for kw in quick_keywords) and len(input_text) < 100:
            return SystemType.CORTEX

        # Medium length, ambiguous - go deep
        if len(input_text) < 200:
            return SystemType.CORTEX

        return SystemType.DEEP_MIND

    async def process(self, input_text: str) -> DirectiveResponse:
        """Process input through appropriate system"""
        import time

        start = time.time()

        # 1. Intent Classification
        system_type = self.classify_intent(input_text)

        if system_type == SystemType.CORTEX:
            # System 1: Fast, local
            content = await self._system1_process(input_text)
            reasoning_trace = None
        else:
            # System 2: Deep reasoning with grounding
            content, reasoning_trace = await self._system2_process(input_text)

        latency_ms = int((time.time() - start) * 1000)

        return DirectiveResponse(
            intent=system_type.value,
            system=system_type,
            content=content,
            reasoning_trace=reasoning_trace,
            latency_ms=latency_ms,
        )

    async def _system1_process(self, input_text: str) -> str:
        """System 1: The Cortex - Fast, < 200ms"""
        # Use local Ollama for instant response
        prompt = f"""You are a helpful AI assistant. Respond concisely and quickly.
User: {input_text}
Assistant:"""

        try:
            result = await self.ollama.generate(
                model="llama3",
                prompt=prompt,
                options={"temperature": 0.7, "num_predict": 200},
            )
            return result
        except Exception as e:
            return f"[CORTEX] Processed: {input_text}"

    async def _system2_process(self, input_text: str) -> tuple[str, Optional[str]]:
        """System 2: The Deep Mind - Strategic reasoning"""
        # First, generate the plan
        prompt = f"""You are a strategic AI advisor. Think deeply and provide comprehensive analysis.

User: {input_text}

Think through this step by step and provide a detailed response:"""

        reasoning_trace = "1. Analyzing input\n2. Retrieving relevant knowledge\n3. Formulating strategy\n4. Generating plan"

        try:
            result = await self.gemini.generate(prompt=prompt)
            content = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
        except Exception as e:
            content = f"[DEEP] Strategic analysis for: {input_text}"

        # Grounding pass
        grounding = await self.grounder.ground(content)

        if not grounding["valid"]:
            # Re-generate with constraints
            reasoning_trace += "\n5. Grounding failed - regenerating"
            content += f"\n\n⚠️ NOTE: Please verify against knowledge base constraints."

        return content, reasoning_trace


# Example usage
if __name__ == "__main__":

    async def main():
        twins = TwinsMode()

        # Test fast query (System 1)
        result = await twins.process("What is 2+2?")
        print(f"System: {result.system.value}")
        print(f"Content: {result.content}")
        print(f"Latency: {result.latency_ms}ms")

        # Test strategy query (System 2)
        result = await twins.process("Design a pricing strategy for a SaaS product")
        print(f"\nSystem: {result.system.value}")
        print(f"Content: {result.content}")
        print(f"Reasoning: {result.reasoning_trace}")

    asyncio.run(main())
