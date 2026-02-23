# AEGNT-UNLTD: The Sovereign Strategist (T0)

**Tier 0 (LemoniAI) Replacement** - Self-evolving cognitive hypervisor

## 🎯 Local-First Design

Runs **100% locally for free** using Ollama. Cloud integrations are optional.

### Quick Start (Free)

```bash
# 1. Install Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull recommended models (free)
ollama pull phi4              # Best small reasoning (4.5GB)
ollama pull llama3.2:3b       # Fast & capable (2GB)

# 3. Run AEGNT-UNLTD
cd aegnt-unltd/python
python inference.py
```

### Recommended Models

| Model | Size | Use Case |
|-------|------|----------|
| **phi4** | 4.5GB | Best reasoning in small package |
| **llama3.2:3b** | 2GB | Fast, capable |
| **mistral:7b** | 4.1GB | Great all-rounder |
| **qwen2.5:3b** | 2GB | Fast coding |

## 🧠 Twins Mode

- **System 1 (Cortex)**: Fast responses (<200ms) - for quick Q&A
- **System 2 (Deep Mind)**: Deep reasoning - for strategy/planning

Automatically routes based on intent classification.

## ☁️ Cloud Optional

Only uses cloud when:
1. No local models available
2. User provides API key (`GEMINI_API_KEY` or `OPENAI_API_KEY`)

## API Usage

```python
from inference import TwinsMode

twins = TwinsMode()
await twins.initialize()

# Automatically routes to System 1 or 2
result = await twins.process("What is 2+2?")
print(result.content)
print(f"Latency: {result.latency_ms}ms")
```

## Architecture

```
Input → Intent Classification → [Cortex] or [Deep Mind]
                                    ↓              ↓
                              Local Ollama    Local Ollama
                                    ↓              ↓
                                Fast (<200ms)  Deep Reasoning
```

## Self-Evolution

The system logs every user accept/reject and evolves nightly:
- Analyzes failure patterns
- Updates system prompt
- Commits improvements to git
