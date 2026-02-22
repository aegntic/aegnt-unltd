# NexusAgent

**Open-Source Multi-Agent Zero Platform** - Run multiple autonomous AI agents locally and in the cloud.

## Why NexusAgent?

| Feature | NexusAgent | LemonAI |
|---------|-----------|---------|
| Multi-instance | ✓ 10+ concurrent | Limited |
| Local + Cloud | ✓ Hybrid | Partial |
| 100% Open Source | ✓ | Partial |
| No Chinese deps | ✓ Ollama/vLLM | DeepSeek, Qwen |
| Active models | Llama 4, Qwen 3 | Restricted |

## Quick Start

```bash
# Clone and setup
git clone https://github.com/your-org/nexusagent.git
cd nexusagent

# Run setup
chmod +x setup.sh
./setup.sh
```

Then open http://localhost:3000

## Architecture

```
┌─────────────────────────────────────────┐
│           NexusAgent Platform           │
├─────────────────────────────────────────┤
│  Agent Zero #1  │ Agent Zero #2 │ ...  │
├─────────────────────────────────────────┤
│     Shared Memory (FAISS + PostgreSQL) │
├─────────────────────────────────────────┤
│  Orchestration │ Sandboxed Execution   │
├─────────────────────────────────────────┤
│      Ollama / vLLM (Your choice)       │
└─────────────────────────────────────────┘
```

## Features

- **Multi-Agent Zero** - Run 10+ isolated agent instances
- **Self-Evolving** - Agents learn from executions
- **Sandboxed** - Docker isolation for safety
- **Hybrid Deploy** - Local or cloud (K8s)
- **Your Models** - Any Ollama/vLLM model

## Configuration

Edit `models/configs/` to configure models:

```yaml
models:
  - name: "llama4:70b"
    provider: "ollama"
    tools: ["reasoning", "coding"]
  - name: "qwen3:32b"  
    provider: "ollama"
    tools: ["coding"]
```

## Development

```bash
# API only (no Docker)
cd ui/api
pip install -r requirements.txt
uvicorn main:app --reload

# Run tests
pytest
```

## License

Apache 2.0
