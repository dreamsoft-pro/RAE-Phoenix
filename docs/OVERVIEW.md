# RAE-Feniks Overview

## What is RAE-Feniks?

**RAE-Feniks** is an enterprise-grade code analysis, meta-reflection, and refactoring engine designed to help understand, evaluate, and improve large-scale software systems.

RAE-Feniks goes beyond traditional static analysis by:
- **Building deep system models** that capture architecture, dependencies, and capabilities
- **Generating meta-reflections** that provide insights into code quality, design patterns, and technical debt
- **Automating safe refactorings** through recipe-based workflows with risk assessment
- **Integrating with RAE (Reflective Agent Engine)** to enable self-aware, self-improving agents

## Key Features

### 🔍 Deep Code Analysis
- Multi-language support (JavaScript, TypeScript, Python, etc.)
- AST-based parsing and semantic understanding
- Dependency graph extraction
- Capability detection (auth, API, UI components, etc.)

### 🧠 Meta-Reflection Layer
- Local meta-reflections per code chunk
- RAE-powered self-model integration
- Historical memory of refactorings and learnings
- Rationale capture for every decision

### 🔧 Enterprise Refactoring
- Recipe-based refactoring workflows
- Risk assessment (LOW, MEDIUM, HIGH, CRITICAL)
- Dry-run mode (safe by default)
- Unified diff patch generation
- Comprehensive validation steps

### 🏢 Enterprise Grade
- **Observability**: Full metrics collection and reporting
- **Security**: JWT authentication with RBAC (viewer, refactorer, admin)
- **Governance**: Budget management and cost control
- **Multi-tenant**: Per-project isolation and access control

### 🔌 Extensible Architecture
- Plugin system for language indexers
- Custom refactoring recipes
- Webhook integration for CI/CD
- REST API for external tools

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAE-Feniks CLI                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│    Ingest    │    │   Analyze    │      │   Refactor   │
│   Pipeline   │    │   Pipeline   │      │    Engine    │
└──────────────┘    └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
        ┌──────────────────────────────────────────┐
        │       System Model & Meta-Reflection     │
        │    (Dependencies, Capabilities, etc.)    │
        └──────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│   Qdrant     │    │     RAE      │      │  Observ.     │
│  (Vector DB) │    │  (Self-Model)│      │  Security    │
└──────────────┘    └──────────────┘      └──────────────┘
```

## Core Concepts

### Code Chunks
The fundamental unit of analysis. Each chunk represents a coherent piece of code with:
- Source file path and line numbers
- Content (code text)
- Language and type (function, class, component, etc.)
- Metadata (imports, exports, dependencies)

### System Model
A holistic representation of your codebase including:
- **Modules**: Logical groupings of code
- **Dependencies**: Import/export relationships
- **Capabilities**: High-level features (authentication, API, UI)
- **Central Modules**: Key architectural components
- **Hotspot Modules**: High-change areas

### Meta-Reflections
Self-generated insights about code quality and architecture:
- **Local**: Per-chunk reflections on complexity, patterns, issues
- **Global**: System-wide insights from RAE integration
- **Historical**: Memory of past refactorings and their outcomes

### Refactoring Recipes
Reusable, parameterized refactoring workflows:
- **analyze()**: Identify refactoring opportunities
- **execute()**: Generate code changes (patches)
- **validate()**: Verify correctness and safety
- Built-in recipes: reduce_complexity, extract_function, etc.

## Use Cases

### 1. Codebase Onboarding
New team members can quickly understand:
- System architecture and dependencies
- Key modules and their responsibilities
- Technical debt hotspots
- Design patterns in use

### 2. Technical Debt Management
Identify and prioritize:
- High-complexity modules
- Dependency tangles
- Missing capabilities
- Refactoring opportunities

### 3. Safe Refactoring
Automated refactoring with:
- Risk assessment
- Dry-run previews
- Comprehensive validation
- Rollback support

### 4. Continuous Improvement
- Track refactoring outcomes
- Learn from past decisions
- Build institutional knowledge
- Enable self-improving systems

### 5. RAE Integration
Enable AI agents that:
- Understand their own code
- Propose informed improvements
- Learn from refactoring outcomes
- Build self-models

## Getting Started

See [GETTING_STARTED.md](./GETTING_STARTED.md) for a step-by-step guide to:
1. Installing RAE-Feniks
2. Indexing your first project
3. Running analysis
4. Viewing meta-reflections
5. Executing refactorings

## Documentation

- [Getting Started](./GETTING_STARTED.md) - Installation and quickstart
- [Reflection & Meta-Reflection](./REFLECTION_AND_META_REFLECTION.md) - How meta-reflection works
- [Enterprise Refactoring](./ENTERPRISE_REFACTORING.md) - Refactoring workflows
- [RAE Integration](./RAE_INTEGRATION.md) - Integrating with RAE

## Philosophy

RAE-Feniks is built on three core principles:

1. **Safety First**: All refactorings are dry-run by default with comprehensive risk assessment
2. **Meta-Awareness**: Systems should understand themselves to improve themselves
3. **Enterprise Ready**: Production-grade observability, security, and governance

## License

Apache-2.0
