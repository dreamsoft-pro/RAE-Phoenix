# RAE-Feniks: The Trinity Protocol (Architecture v3.0)

## 🏛️ Core Philosophy
"Think before you act, check before you commit."
The system is designed not just to rewrite code, but to **transform a legacy system** into an AI-native platform through rigorous contracts, deep planning, and multi-layered consensus.

---

## 🧠 The 3x3x3 Council (Rada Starszych)
Evaluation and decision-making are strictly hierarchical. No code passes without consensus.

### Layer 1: The Working Layer (Local Speed)
*   **Role**: Rapid prototyping, syntax checking, draft generation.
*   **Models**:
    1.  **Gemini 2.5 Flash** (Coordinator/Context)
    2.  **Qwen 2.5 14B** (Logic/Coding - Running on Node 1 RTX 4080)
    3.  **DeepSeek Coder 14B** (Math/Structure - Running on Node 1 RTX 4080)
*   **Output**: Draft Code + Basic Unit Tests.

### Layer 2: The Expert Layer (Refinement)
*   **Role**: Architecture review, security audit, optimization.
*   **Models**:
    1.  **Gemini 2.5 Pro** (Lead Architect)
    2.  **Claude 3.5 Sonnet** (Styling/Refactoring Specialist)
    3.  **DeepSeek 33B** (Logic Verifier)
*   **Output**: Polished Code + Integration Tests.

### Layer 3: The Supreme Council (Final Verdict)
*   **Role**: Conflict resolution, edge case analysis, strategic alignment.
*   **Models**:
    1.  **Gemini 3.1 Pro** (Supreme Logic/Reasoning)
    2.  **Claude 3.7 / Opus** (Security & Safety Guard)
    3.  **GPT-4o** (Edge Case Hunter)
*   **Trigger**: Activated ONLY when L2 models disagree or complex logic requires arbitration.

---

## ⚙️ The Workflow: Plan -> Act -> Verify

### Step 1: Preparation (Phase 2.5 Integration)
Before a single line of code is written, the system MUST:
1.  **Symbol Table Recovery**: Extract all variables, functions, and directives from the legacy scope.
2.  **UI Dependency Graph**: Map how components interact (AST-based).
3.  **Contract Definition**: Generate `contract.json` defining inputs, outputs, and behavior.

### Step 2: Planning (The Architect)
*   **Agent**: Planner (Gemini 2.5 Pro).
*   **Input**: Legacy Source + UI Graph + Contract.
*   **Action**: Creates a detailed implementation blueprint (JSON structure of files/modules).
*   **Output**: `blueprint.json`.

### Step 3: Execution (The Builder)
*   **Agent**: Implementer (Qwen 14B/32B + Gemini Flash).
*   **Input**: Blueprint + Contract.
*   **Action**: Generates code strictly adhering to the plan. **NO creativity outside the blueprint.**
*   **Output**: Source Code (`.tsx`, `.ts`).

### Step 4: Verification (The Judge)
*   **Agent**: Verifier (Separate Model Instance).
*   **Action**: 
    1.  Static Analysis (Lint/Types).
    2.  Contract Check (Does it meet `contract.json`?).
    3.  Legacy Guard (Playwright/Snapshot comparison).
*   **Verdict**: Pass / Fail / Escalate to Supreme Council.

---

## 🖥️ Hardware Infrastructure (Node 1 - Lumina)
*   **GPU**: NVIDIA RTX 4080 (16GB VRAM).
*   **Local Models**: Hosted via Ollama/vLLM (Qwen 14B, DeepSeek 14B).
*   **API Gateway**: RAE API v2 acts as a bridge for paid models (Gemini, Claude, OpenAI).
*   **Telemetry**: OpenTelemetry Collector + Jaeger (Port 16686) tracking every decision.

## 🛡️ Strategic Mandates
1.  **Contract-First**: No code without a contract.
2.  **Zero Regression**: Legacy behavior must be preserved unless explicitly deprecated.
3.  **AI-Native**: The resulting codebase must be easily understandable by future AI agents (clear types, explicit deps).
