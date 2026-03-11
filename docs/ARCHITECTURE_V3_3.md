# RAE-Feniks Architecture v3.3 (The Iron Protocol)

## 🏛️ Core Philosophy
"Automated Behavioral Symmetry."
The goal is not just to rewrite code, but to guarantee that the new system behaves exactly like the legacy one, verified through multi-layered AI consensus and real-world evidence.

---

## 🧠 The 3x3x3 Council of Elders
Decision-making is divided into three specialized layers. Each decision requires a consensus of three models or escalation.

| Layer | Model A (Speed) | Model B (Logic) | Model C (Context) | Location |
| :--- | :--- | :--- | :--- | :--- |
| **L1: Working** | **Qwen 2.5 14B** | **DeepSeek 14B** | **Gemini 2.5 Flash** | Local (RTX 4080) / API |
| **L2: Expert** | **Gemini 2.5 Pro** | **Claude 3.5 Sonnet** | **Qwen 2.5 14B** | API Gateway / Local |
| **L3: Supreme** | **Gemini 3.1 Pro** | **Claude 4.5/Opus** | **GPT-5.2 (o1)** | Pure API Gateway |

---

## ⚡ The Operational Flow (End-to-End)

### Step 0: Discovery & Evidence (The Source of Truth)
Before any refactoring, **Playwright Scanners** crawl the legacy AngularJS application.
- **Action**: Interaction recording, DOM snapshots, and API payload sniffing.
- **Output**: `Evidence Pack` stored in RAE-Core with the `verified_behavior` tag.

### Step 1: Semantic Contract (The Agreement)
The L2 Expert Council analyzes the legacy source and the Evidence Pack.
- **Action**: Map AngularJS `$scope` to React `props/state`. Define interfaces.
- **Output**: `contract.json` (The "Assembly Instruction").

### Step 2: Architectural Blueprint (The Design)
The Supreme Architect (Gemini 3.1 Pro) designs the module structure.
- **Action**: Decompose large files into logical sub-modules (hooks, utils, UI).
- **Output**: `blueprint.json` (Dependency graph and file list).

### Step 3: Atomic Production (The Builder)
The L1 Working Layer implements the code based strictly on the Blueprint and Contract.
- **Restriction**: No logic guessing. If the contract is unclear, the agent fails the task and requests a contract update.

### Step 4: Triple-Stage Audit (The Quality Gate)
1. **Technical Gate (L1)**: Static analysis, type checking, and compilation.
2. **Semantic Gate (L2)**: Business logic verification. Compare calculated values (e.g., prices) with legacy logic.
3. **Behavioral Gate (L3)**: Final arbitration. Compare Next.js runtime behavior with the Step 0 `Evidence Pack`.

---

## 📡 Nervous System: Telemetry & Monitoring
The entire factory is instrumented with **OpenTelemetry (OTel)**.

- **Tracing**: Every decision, model response, and conflict is a `span` in **Jaeger (Port 16686)**.
- **Metrics**: Track "Time to Consensus" and "Escalation Rate". High escalation triggers a manual architectural review.
- **Supervisor v2**: An autonomous watchdog that monitors Jaeger. It automatically restarts stalled builds and adjusts `CHUNK_SIZE` dynamically.

---

## 🖥️ Hardware Infrastructure: Node 1 (Lumina)
- **Primary Node**: NVIDIA RTX 4080 (16GB VRAM).
- **Optimized for 14B**: Local models (Qwen, DeepSeek) are tuned for 16GB VRAM to ensure high speed and zero cost for L1 tasks.
- **RAE-Gateway**: Centralized API access to SaaS models with automatic token budget control.

## 🛡️ Strategic Mandates
1. **Contract-First**: Code is a byproduct of the contract, not the goal.
2. **Zero Guessing**: If legacy behavior is unknown, it must be discovered in Step 0, never guessed.
3. **AI-Native Output**: Resulting code must be optimized for readability by both humans and future AI agents.
