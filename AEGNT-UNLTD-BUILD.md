# AEGNT-UNLTD: The Sovereign Strategist (Tier 0)
**Version:** 1.0.0 (Alpha-Zero)
**Codename:** "The Brain"
**Objective:** Construct a self-evolving, local-first cognitive hypervisor to serve as the CEO of the $1M MRR autonomous swarm.

## 1. Core Philosophy: The Bifurcated Mind
We do not build "chatbots". We build a decision engine that separates **Reflex** from **Reasoning**.

### The Architecture
*   **Core Runtime:** Rust (Binary name: `unltd-core`). High-performance, memory-safe orchestration.
*   **Inference Interface:** Python (via PyO3 binding). Bridges to local LLMs (Ollama/vLLM) and Cloud Reasoning (Gemini 3.1 Pro).
*   **Sandbox:** Docker. Every execution happens in an ephemeral, air-gapped container [1].
*   **Visual Layer:** Next.js + Tauri v2. Obsidian Glass aesthetic (#0A0A0A).

## 2. Feature Specification

### 2.1. Twins Mode v2 (Hard Bifurcation)
*Rationale: Speed builds trust; Depth builds value [6].*

**Mechanism:**
The UI presents a single input field, but the backend splits the stream:
1.  **System 1 (The Cortex):**
    *   **Model:** Local `Llama-3-8B-Instruct` (via Ollama) or `Groq`.
    *   **Latency:** < 200ms.
    *   **Function:** Intent classification, UI navigation, basic Q&A, "Vibe Check".
    *   **Visual:** Instant stream, Cyan text (#00F5FF).

2.  **System 2 (The Deep Mind):**
    *   **Model:** `Gemini 3.1 Pro` (Deep Thinking) or `DeepSeek R1`.
    *   **Latency:** Asynchronous (User sees fluid "Thinking..." particles).
    *   **Function:** Strategy formulation, multi-step planning, code architecture, "ReAct" loops.
    *   **Visual:** Slow stream, Violet text (#8B00FF), collapsible "Reasoning Trace" block.

### 2.2. The Truth Layer (NotebookLM Integration)
*Rationale: Generic RAG is noisy. We need a Constitution [2][3].*

**Implementation:**
*   **Ingestion:** `unltd-core` watches a `./knowledge` folder. Any `.pdf`, `.md`, or `.txt` dropped here is auto-uploaded to a dedicated (headless) NotebookLM instance or parsed into a local vector store (ChromaDB) if offline privacy is required.
*   **The Check:** Before `System 2` outputs a strategic plan, it must run a **Grounding Pass**:
    *   *Prompt:* "Verify this plan against the constraints in `./knowledge/brand_guidelines.pdf`. Cite discrepancies."
    *   *Failure:* If citation fails, the plan is rejected internally and regenerated.

### 2.3. The "God Mode" Canvas (Visual Reality Editor)
*Rationale: Text is low-bandwidth. We edit the *structure* of reality [7].*

**Functionality:**
*   Instead of a chat log, the primary view is a **Node Graph** (React Flow).
*   **Nodes:** Represents assets (e.g., "Landing Page", "Pricing Model", "Email Sequence").
*   **Click-to-Mutate:**
    *   User clicks the "Pricing" node.
    *   Prompt: "Change the Enterprise Pilot to $25k."
    *   `aegnt-unltd` rewrites the underlying code/config *and* updates the graph visual instantly.
*   **Tech:** Framer Motion for layout transitions. SVG generation for exports.

### 2.4. Self-Evolution (The OODA Loop)
*Rationale: The agent must get smarter while you sleep [8][9].*

**The Nightly Mutation:**
1.  **Log:** Throughout the day, `unltd-core` logs every "User Reject" (user edited the AI's code) and "User Accept".
2.  **Reflect:** At 03:00 local time, a cron job spins up a separate maintenance agent.
    *   *Input:* Daily logs + Error Traces.
    *   *Task:* "Identify one recurring pattern of failure. Rewrite your own `system_prompt.md` to prevent this tomorrow."
3.  **Commit:** The agent pushes a Git commit: `chore(self): evolved system prompt v{n+1}`.

## 3. Technical Build Steps (The Ground Up)

### Step 1: Rust Core Init
```bash
cargo new aegnt-unltd --bin
cd aegnt-unltd
# Add dependencies for async runtime and web server
cargo add tokio --features full
cargo add axum
cargo add serde --features derive
cargo add serde_json
```

### Step 2: The "Brain" Struct (Rust)
Define the state machine that holds the bifurcation logic.

```rust
struct Brain {
    fast_model: String, // e.g., "ollama:llama3"
    slow_model: String, // e.g., "gemini-3.1-pro"
    memory_path: PathBuf,
    // The "Soul" - dynamic system prompt loaded from disk
    system_prompt: String, 
}

impl Brain {
    async fn process_directive(&self, input: &str) -> Response {
        // 1. Classification (System 1)
        let intent = self.classify_intent(input).await;
        
        // 2. Routing
        match intent {
            Intent::QuickAction => self.fast_execute(input).await,
            Intent::Strategy => self.deep_reason(input).await, // Triggers NotebookLM lookup
        }
    }
}
```

### Step 3: The Docker Sandbox (Security)
Create docker/Dockerfile.sandbox.

```dockerfile
FROM python:3.11-slim
# The "Clean Room" for code execution
WORKDIR /workspace
# Install base tools ONLY. No networking allowed by default.
RUN apt-get update && apt-get install -y git
COPY requirements.txt .
RUN pip install -r requirements.txt
# Entry point awaits JSON commands via stdin
CMD ["python", "executor.py"]
```

### 4. Brand & Aesthetic Guidelines (Immutable)
*   **Font:** Playfair Display (Headlines), JetBrains Mono (Code/Reasoning), Inter (UI).
*   **Palette:** Background #0A0A0A. Accents: Teal #00F5FF (Action), Violet #8B00FF (Strategy).
*   **Motion:** Fluid, organic. No "robot" jerky movements. UI elements "grow" and "dissolve".

### 5. Success Metrics (The $1M MRR Physics)
*   **Cognitive Latency:** System 1 < 200ms.
*   **Accuracy:** System 2 Plan Acceptance Rate > 85%.
*   **Autonomy:** Nightly Mutation commits successfully for 7 consecutive days.
