"""
AEGNT-UNLTD Python Inference Layer
Local-First: Runs entirely offline with small models
Cloud Optional: Fallback to Gemini/Claude when needed
"""

import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx


class SystemType(Enum):
    CORTEX = "cortex"  # System 1 - Fast, local
    DEEP_MIND = "deep_mind"  # System 2 - Deep, local or cloud


@dataclass
class DirectiveResponse:
    intent: str
    system: SystemType
    content: str
    reasoning_trace: Optional[str] = None
    latency_ms: int = 0
    model_used: str = "local"
    source: str = "local"


class LocalModels:
    """
    Curated list of small, free models that run locally via Ollama
    Sorted by size/capability tradeoff
    """

    # Fast models for System 1 (< 200ms)
    CORTEX_MODELS = [
        ("phi4", "Microsoft Phi-4", 4.5),  # 4.5GB - Best reasoning in small package
        ("llama3.2:3b", "Llama 3.2 3B", 2.0),  # 2GB - Fast, capable
        ("mistral:7b", "Mistral 7B", 4.1),  # 4.1GB - Great all-rounder
        ("qwen2.5:3b", "Qwen 2.5 3B", 2.0),  # 2GB - Fast Chinese
        ("phi3:3.8b", "Phi-3 3.8B", 2.3),  # 2.3GB - Microsoft small
        ("gemma2:2b", "Gemma 2 2B", 1.4),  # 1.4GB - Google's smallest
    ]

    # Capable models for System 2
    DEEP_MODELS = [
        ("llama3.1:8b", "Llama 3.1 8B", 4.9),  # 4.9GB - Best overall
        ("qwen2.5:7b", "Qwen 2.5 7B", 4.4),  # 4.4GB - Great coding
        ("mistral:7b", "Mistral 7B", 4.1),  # 4.1GB - Balanced
        ("llama3.2:8b", "Llama 3.2 8B", 4.9),  # 4.9GB - Newer Llama
        ("phi4", "Phi-4", 4.5),  # 4.5GB - Solid reasoning
    ]

    @classmethod
    def get_best_cortex(cls) -> tuple:
        return cls.CORTEX_MODELS[0]

    @classmethod
    def get_best_deep(cls) -> tuple:
        return cls.DEEP_MODELS[0]


class OllamaClient:
    """Local Ollama inference - fully offline, free"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._available_models: Optional[List[str]] = None

    async def is_available(self) -> bool:
        """Check if Ollama is running locally"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False

    async def list_models(self) -> List[str]:
        """Get available local models"""
        if self._available_models:
            return self._available_models

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    self._available_models = [m["name"] for m in data.get("models", [])]
                    return self._available_models
        except:
            pass
        return []

    async def get_best_available(self, preferred: List[tuple]) -> Optional[str]:
        """Find the best available model from preferred list"""
        available = await self.list_models()
        for model_name, _, _ in preferred:
            # Check exact match or partial
            base_name = model_name.split(":")[0]
            for avail in available:
                if base_name in avail or avail.startswith(base_name):
                    return avail
        return None

    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        temperature: float = 0.7,
        num_predict: int = 512,
        **kwargs,
    ) -> str:
        """Generate response from local model"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": temperature,
                        "num_predict": num_predict,
                        **kwargs,
                    },
                },
            )
            result = response.json()
            return result.get("response", "")


class LocalInference:
    """
    Full local inference - NO cloud, NO API keys, 100% free
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama = OllamaClient(ollama_url)
        self.cortex_model: Optional[str] = None
        self.deep_model: Optional[str] = None

    async def initialize(self) -> Dict[str, Any]:
        """Initialize with best available local models"""
        if not await self.ollama.is_available():
            return {
                "status": "error",
                "message": "Ollama not running. Install: curl -fsSL https://ollama.com/install.sh | sh",
                "local": False,
            }

        # Find best available models
        self.cortex_model = await self.ollama.get_best_available(
            LocalModels.CORTEX_MODELS
        )
        self.deep_model = await self.ollama.get_best_available(LocalModels.DEEP_MODELS)

        # Fallback chain
        if not self.cortex_model:
            self.cortex_model = "llama3.2:3b"
        if not self.deep_model:
            self.deep_model = self.cortex_model

        return {
            "status": "ready",
            "local": True,
            "cortex_model": self.cortex_model,
            "deep_model": self.deep_model,
            "models": await self.ollama.list_models(),
        }

    async def generate(
        self, prompt: str, system: SystemType, stream: bool = False
    ) -> str:
        """Generate using appropriate local model"""
        model = self.deep_model if system == SystemType.DEEP_MIND else self.cortex_model

        full_prompt = prompt
        if system == SystemType.DEEP_MIND:
            full_prompt = f"""Think step by step and provide detailed reasoning.

{prompt}

Provide your analysis and then your conclusion."""

        return await self.ollama.generate(
            model=model,
            prompt=full_prompt,
            stream=stream,
            temperature=0.7 if system == SystemType.CORTEX else 0.5,
            num_predict=256 if system == SystemType.CORTEX else 1024,
        )


class CloudFallback:
    """
    Optional cloud integration - only used when:
    1. Local fails
    2. User provides API key
    3. Complex reasoning needed
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        )

    async def generate(self, prompt: str, provider: str = "gemini") -> Optional[str]:
        """Generate using cloud API if key available"""
        if not self.api_key:
            return None

        if provider == "gemini":
            return await self._gemini(prompt)
        return None

    async def _gemini(self, prompt: str) -> str:
        """Google Gemini API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                params={"key": self.api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            result = response.json()
            return (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )


class TwinsMode:
    """
    Twins Mode: System 1 (Cortex) + System 2 (Deep Mind)
    LOCAL FIRST - always tries local models before cloud
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        cloud_api_key: Optional[str] = None,
    ):
        self.local = LocalInference(ollama_url)
        self.cloud = CloudFallback(cloud_api_key)
        self.status: Dict[str, Any] = {}

    async def initialize(self) -> Dict[str, Any]:
        """Initialize - tries local first"""
        self.status = await self.local.initialize()

        if self.status.get("local"):
            return {
                "status": "ready",
                "mode": "local",
                "cortex": self.status.get("cortex_model"),
                "deep": self.status.get("deep_model"),
            }

        # Try cloud as fallback
        if self.cloud.api_key:
            return {"status": "ready", "mode": "cloud", "provider": "gemini"}

        return {"status": "error", "message": "No local models and no cloud API key"}

    def classify_intent(self, input_text: str) -> SystemType:
        """Classify to System 1 or System 2"""
        quick_keywords = ["what", "how", "show", "list", "?", "time"]
        strategy_keywords = [
            "plan",
            "strategy",
            "design",
            "analyze",
            "build",
            "create",
            "develop",
            "architecture",
            "research",
        ]

        text = input_text.lower()

        if any(kw in text for kw in strategy_keywords):
            return SystemType.DEEP_MIND

        if any(kw in text for kw in quick_keywords) and len(input_text) < 80:
            return SystemType.CORTEX

        if len(input_text) < 150:
            return SystemType.CORTEX

        return SystemType.DEEP_MIND

    async def process(self, input_text: str) -> DirectiveResponse:
        """Process through appropriate system - LOCAL FIRST"""
        import time

        start = time.time()

        system_type = self.classify_intent(input_text)

        # Try local first
        if self.status.get("local"):
            content = await self.local.generate(input_text, system_type)
            source = "local"
        elif self.cloud.api_key:
            # Fallback to cloud
            content = await self.cloud.generate(input_text)
            source = "cloud"
        else:
            content = "[ERROR] No inference engine available. Install Ollama or provide API key."
            source = "none"

        latency_ms = int((time.time() - start) * 1000)

        model_used = (
            self.status.get("cortex_model")
            if system_type == SystemType.CORTEX
            else self.status.get("deep_model")
        )
        if not self.status.get("local"):
            model_used = "gemini-cloud"

        return DirectiveResponse(
            intent=system_type.value,
            system=system_type,
            content=content,
            reasoning_trace=None
            if system_type == SystemType.CORTEX
            else "Step-by-step analysis completed",
            latency_ms=latency_ms,
            model_used=model_used,
            source=source,
        )


# Install helper
LOCAL_SETUP = """
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended models (free, local)
ollama pull phi4              # Best small reasoning (4.5GB)
ollama pull llama3.2:3b       # Fast & capable (2GB)
ollama pull mistral:7b        # Great all-rounder (4.1GB)

# Verify
ollama list
"""


if __name__ == "__main__":

    async def test():
        twins = TwinsMode()
        status = await twins.initialize()
        print(f"Status: {status}")

        if status.get("status") == "ready":
            # Test Cortex (fast)
            result = await twins.process("What is 2+2?")
            print(f"\n[CORTEX] Latency: {result.latency_ms}ms")
            print(f"Content: {result.content[:100]}")

            # Test Deep Mind
            result = await twins.process("Design a pricing strategy for a SaaS")
            print(f"\n[DEEP] Latency: {result.latency_ms}ms")
            print(f"Content: {result.content[:200]}")
        else:
            print(f"\nError: {status.get('message')}")
            print(f"\nTo fix:\n{LOCAL_SETUP}")

    asyncio.run(test())
