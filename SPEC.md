# NexusAgent - Open-Source Multi-Agent Zero Platform

## Executive Summary

**NexusAgent** is a fully open-source, self-evolving AI agent platform that runs multiple Agent Zero instances locally and in the cloud. Built entirely on Western open-source technologies with no dependencies on Chinese companies or sunsetted models.

### Key Differentiators from LemonAI
- **100% Open Source** - No proprietary components, full transparency
- **Multi-Instance Native** - Run 10+ concurrent Agent Zero instances
- **Hybrid Deployment** - Local + cloud (AWS/GCP/DigitalOcean) from day one
- **No Chinese Tethering** - Uses Ollama, vLLM, HuggingFace - no ByteDance/Tencent/Alibaba
- **Active Models** - Llama 4, Qwen 3, Mistral, Gemma 3 - all actively maintained

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      NexusAgent Platform                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Agent Zero  │  │ Agent Zero  │  │ Agent Zero  │   ...       │
│  │ Instance #1 │  │ Instance #2 │  │ Instance #N │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                    │
│  ┌──────┴────────────────┴────────────────┴──────┐             │
│  │           Shared Memory & Knowledge Base       │             │
│  │     (FAISS + PostgreSQL + Vector Storage)      │             │
│  └────────────────────────────────────────────────┘             │
│                            │                                    │
│  ┌─────────────────────────┼────────────────────────┐          │
│  │        Orchestration Layer                       │          │
│  │  • Task Distribution  • Load Balancing          │          │
│  │  • Cross-Agent Comm    • Resource Management     │          │
│  └──────────────────────────────────────────────────┘          │
│                            │                                    │
│  ┌─────────────────────────┼────────────────────────┐          │
│  │         Execution Environment                    │          │
│  │  • Docker Sandboxes  • Browser Automation       │          │
│  │  • Code Interpreter   • Terminal Access         │          │
│  └──────────────────────────────────────────────────┘          │
│                            │                                    │
│  ┌──────────────────────────────────────────────────┐          │
│  │              Model Layer (Ollama/vLLM)           │          │
│  │   Llama 4  |  Qwen 3  |  Mistral  |  Gemma 3   │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Features

### 1. Multi-Agent Zero Instances

Each instance is fully isolated with:
- **Own memory partition** - FAISS vector store per agent
- **Project workspace** - Isolated file system
- **Tool set** - Dynamically created tools
- **Conversation history** - Separate context

```yaml
# Instance Configuration
agents:
  - name: "researcher"
    model: "llama4:70b"
    memory: "2gb"
    tools: ["web_search", "browser", "memory"]
    
  - name: "coder"  
    model: "qwen3:32b"
    memory: "4gb"
    tools: ["terminal", "editor", "git"]
    
  - name: "analyst"
    model: "mistral-large"
    memory: "2gb"
    tools: ["data", "visualization"]
```

### 2. Self-Evolving Memory System

- **Experience Repository** - Stores successful patterns
- **Cross-Agent Learning** - Agents share discoveries
- **Adaptive Tool Creation** - Learns to create new tools
- **Reflection Loop** - Analyzes failures, improves strategies

### 3. Sandboxed Execution

- **Docker Isolation** - Each agent runs in container
- **Resource Limits** - CPU/RAM caps per agent
- **Network Policy** - Controlled internet access
- **File System Guards** - Protect sensitive directories

### 4. Hybrid Deployment

| Component | Local | Cloud |
|-----------|-------|-------|
| Agent Instances | ✓ | ✓ |
| Model Serving | ✓ (Ollama) | ✓ (vLLM) |
| Memory/Vector DB | ✓ (local) | ✓ (cloud) |
| Browser Automation | ✓ | ✓ |
| Storage | Local disk | S3/GCS |

---

## Supported Models (Non-Sunset)

| Model | Context | Use Case | Status |
|-------|---------|----------|--------|
| **Llama 4 Scout** | 1M | General reasoning | Active |
| **Llama 4 Behemoth** | 1M | Complex tasks | Active |
| **Qwen 3 32B** | 128K | Coding | Active |
| **Qwen 3 8B** | 128K | Fast tasks | Active |
| **Mistral Large 3** | 128K | Analysis | Active |
| **Gemma 3 27B** | 128K | Multimodal | Active |
| **DeepSeek V3** | 64K | Coding (optional) | Active |

---

## Project Structure

```
nexusagent/
├── core/
│   ├── agent/           # Agent Zero core implementation
│   ├── memory/         # FAISS + PostgreSQL memory
│   ├── orchestration/  # Task distribution
│   └── sandbox/        # Docker execution
├── ui/
│   ├── dashboard/      # Web UI (Vue 3)
│   └── api/            # FastAPI backend
├── deployment/
│   ├── docker/         # Local deployment
│   ├── kubernetes/     # Cloud deployment
│   └── ansible/        # Infrastructure as code
├── models/
│   └── configs/        # Model configurations
└── docs/
    └── setup/          # Installation guides
```

---

## Quick Start (Local)

```bash
# 1. Clone and setup
git clone https://github.com/your-org/nexusagent.git
cd nexusagent

# 2. Start services
docker compose up -d

# 3. Access UI
open http://localhost:3000

# 4. Run first agent
nexusagent run --agent researcher --task "Find latest AI news"
```

---

## API Reference

### Create Agent Instance
```bash
POST /api/agents
{
  "name": "my-agent",
  "model": "llama4:70b",
  "tools": ["browser", "terminal"]
}
```

### Execute Task
```bash
POST /api/agents/{id}/execute
{
  "task": "Build a REST API",
  "context": {"language": "python", "framework": "fastapi"}
}
```

### Check Status
```bash
GET /api/agents/{id}/status
```

---

## Comparison: NexusAgent vs LemonAI

| Feature | NexusAgent | LemonAI |
|---------|-----------|---------|
| Multi-instance | Native (10+) | Limited (1-2) |
| Local + Cloud | ✓ Hybrid | Partial |
| Open Source | 100% | Partial |
| Chinese dependencies | None | DeepSeek, Qwen |
| Model choice | Any (Ollama) | Restricted |
| Self-evolving | ✓ | ✓ |
| Browser automation | ✓ | ✓ |
| Code sandbox | ✓ | ✓ |

---

## Technology Stack

- **Agent Framework**: Agent Zero (modified)
- **UI**: Vue 3 + TypeScript
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL + FAISS
- **Container**: Docker + Kubernetes
- **Model Serving**: Ollama (local) + vLLM (cloud)
- **Browser**: Playwright (headless)

---

## Roadmap

### Phase 1: Foundation (Month 1-2)
- [x] Agent Zero core integration
- [x] Single agent execution
- [x] Basic UI dashboard
- [x] Docker sandbox

### Phase 2: Multi-Agent (Month 2-3)
- [ ] Orchestration layer
- [ ] Shared memory system
- [ ] Cross-agent communication
- [ ] Task distribution

### Phase 3: Cloud (Month 3-4)
- [ ] Kubernetes deployment
- [ ] Auto-scaling
- [ ] Cloud storage integration
- [ ] Load balancing

### Phase 4: Evolution (Month 4-6)
- [ ] Self-evolving memory
- [ ] Tool creation engine
- [ ] Pattern recognition
- [ ] Performance optimization

---

## License

Apache 2.0 - Fully open source, commercial friendly
