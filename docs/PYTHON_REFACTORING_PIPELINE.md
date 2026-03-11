# docs/PYTHON_REFACTORING_PIPELINE.md
Python Refactoring Pipeline – Feniks Integration Guide

Safe, Iterative, Behavior-Driven Refactoring for Large Python Codebases

1. Introduction

This document describes the official refactoring pipeline used by Feniks to safely modernize and improve large Python projects (35k–50k LOC and beyond).

The pipeline integrates:

Feniks Reflection Engine

BehaviorGuard (BehaviorScenario & BehaviorContract)

Open-source refactoring tools (AST-based)

Static analysis (Ruff, MyPy/Pyright)

Automated codemods (Bowler, LibCST, Rope)

Snapshot-based regression detection

LLM executors (Claude/Gemini) for creative or structural tasks

This pipeline enables controlled refactoring of legacy Python systems without breaking behavior, even when:

tests are incomplete,

functions exceed 1500–2000 lines,

modules are monolithic,

business logic is deeply intertwined.

Feniks acts as the orchestrator, auditor, and risk controller, while OSS tools do the heavy lifting.

2. Architecture Overview
[ Source Code ]
       │
       ▼
[ Static Analysis Layer ]
  (Ruff, MyPy, Pyright)
       │
       ▼
[ AST Transformation Layer ]
  (LibCST, Bowler, Rope)
       │
       ▼
[ Feniks Behavior Layer ]
  - BehaviorSnapshot
  - BehaviorContracts
  - Risk Scoring
       │
       ▼
[ LLM Executor Layer ]
  (Claude CLI, Gemini CLI)
       │
       ▼
[ Reports & RAE Memory ]


Feniks is responsible for:

task planning,

validation,

behavior comparison,

risk scoring,

iterative refinement.

External tools perform:

formatting,

linting,

structural rewrites,

extraction of helpers,

splitting of large modules.

3. Pipeline Goals

The Python refactoring pipeline ensures that:

✔ 1. Behavior does not change

Even without tests, Feniks uses:

golden inputs/outputs,

snapshot comparisons,

BehaviorContracts,

structural invariants,

metrics (function arity, complexity, coupling).

✔ 2. Code becomes modular and maintainable

Large modules (1–2k lines) are safely:

split into smaller files,

decomposed into classes/services/helpers,

annotated with type hints,

cleaned of dead code.

✔ 3. Risk is controlled

Feniks assigns a RiskScore after each iteration:

Structural Risk

Runtime Behavior Risk

Complexity Reduction Score

Side-Effect Probability

✔ 4. Changes are iterative and reversible

Each refactor is run through:

Feniks eval

snapshot → contract comparison

optional RAE memory recording

human approval

4. Pipeline Stages

Below is the exact workflow for Python refactoring inside Feniks.

Stage 1 — Static Analysis Baseline
Tools:

Ruff

MyPy / Pyright

Radon (optional) – complexity & maintainability index

Deptry – dependency cycle detection

Feniks Tasks:

collect code metrics,

identify hotspots,

detect unsound imports,

generate initial SystemModel.PythonModuleMap,

build RefactorPriorityList.

Outputs:

static_analysis.json

initial_behavior_snapshot.json

module_hotspots.json

Stage 2 — Deep Structural Analysis (AST)
Tools:

LibCST (primary AST tool)

RedBaron (semantic read layer)

Bowler (codemods)

Rope (rename/move/extract OOP refactors)

Feniks Tasks:

detect excessively long modules / functions,

detect duplicated patterns,

propose decomposition strategies,

identify code that can be automated (bowler/libcst),

generate AST-based diff reports.

Outputs:

structure_analysis.json

ast_candidates_for_refactor.json

Stage 3 — Behavior Contracts (Optional but Recommended)

When tests are limited, Feniks compensates via BehaviorContracts.

Types:

A) State Contracts

return shape invariants,

type invariants,

side-effect detection (I/O, SQL, filesystem).

B) Interaction Contracts

sequence of calls,

required arguments,

function signature stability.

C) Output Contracts

golden input → expected output snapshots,

hash/diff-based assertions.

D) Safety Contracts

forbidden side effects,

forbidden global mutation,

concurrency-risk indicators.

These contracts allow Feniks to check that refactoring did not alter meaning.

Stage 4 — Automated Refactoring (OSS Tools)

This stage is executed under Feniks supervision.

Automated tasks:

dead code removal,

reorder imports,

auto-fix simple smells (via Ruff),

auto-upgrade syntax (via PyUpgrade),

extract helper functions,

flatten deeply nested logic,

rewrite old idioms.

AST-based refactors:

LibCST transformations,

Bowler codemods,

Rope rename/extract operations.

AI-assisted structural refactors:

transform monolith into modules,

migrate logic to classes/services,

rewrite procedural code.

Feniks:

generates plan,

executes tools,

collects results,

performs diffs,

computes risk score.

Stage 5 — Behavior Evaluation

Feniks compares:

snapshots (before/after),

structural diffs,

contract violations,

complexity changes,

type changes.

Outputs:

behavior_evaluation.json

risk_score.json

refactor_summary.md

If risk too high → iteration stopped.

Stage 6 — LLM Integration

Claude or Gemini handle creative or semantic transformations:

suggest decomposition strategies,

generate docstrings and types,

rewrite complex functions into readable versions,

propose new architectures.

Feniks:

provides prompts,

captures LLM output,

validates results through contracts.

Stage 7 — Memory & Iteration Loop (Optional RAE Integration)

If RAE Memory Engine is available:

Feniks stores:

all BehaviorReports,

snapshots,

module history,

architectural decisions,

risk evolution.

This allows long-term, cross-iteration reasoning.

5. Example: Refactoring a 2000-line Module (“SplitterCore”)

Feniks produces:

Step 1 — Static Analysis

function complexity map,

dependency graph,

cycles detected.

Step 2 — AST Analysis

identifies 4 natural groups of logic:

loading PDFs,

geometry calculations,

chunking,

output generation.

Step 3 — Behavior Contracts
- same number of outputs
- same file naming
- same geometry invariants
- same stats

Step 4 — Automated Refactor

LibCST extracts 12 helper functions,

Bowler moves them to helpers/geometry.py,

Rope renames confusing identifiers.

Step 5 — Behavior Evaluation

snapshot comparison passes,

no type regressions,

RiskScore: 0.21 (low).

Step 6 — LLM-assisted cleanup

Claude rewrites docstrings,

Gemini reorganizes module imports.

Step 7 — Snapshot saved in RAE

next iteration uses enriched context.

6. Tooling Benchmarks
Tool	Purpose	Stability	Recommended Usage
Ruff	Lint/format/fix	Excellent	default sanity check
MyPy	Type checker	Excellent	type invariants
Pyright	Fast type checker	Excellent	large repos
LibCST	AST transform	Excellent	precise refactors
Bowler	Codemods	Very good	mass transformations
Rope	OOP refactors	Good	rename/extract/move
Radon	Complexity	Good	hotspot detection
Deptry	Cycles	Good	dependency cleanup

Feniks can automatically run any combination of the above.

7. Configuration File Example

feniks_python_pipeline.yml:

project_id: billboard_splitter
language: python
root: ./billboard_splitter

static_analysis:
  tools:
    - ruff
    - mypy

refactor_tools:
  - libcst
  - bowler
  - rope

behavior_contracts:
  enabled: true
  auto_snapshot: true

llm_executors:
  claude: "claude"
  gemini: "gemini"

iterations: 4
save_to_rae: true

8. Summary

The Feniks Python Refactoring Pipeline provides:

safe, behavior-driven refactoring

AST-based precision

integration with industry-grade OSS tools

iterative evaluation & risk scoring

compatibility with large legacy codebases

optional memory-enhanced iterations (RAE)

This pipeline is now the recommended way to modernize, decompose, and stabilize large Python systems under Feniks supervision.