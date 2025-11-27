# 🦅 Feniks: Meta-Reflective Code Analysis Engine

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![Architecture](https://img.shields.io/badge/architecture-hexagonal-orange)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-green)]()

**Feniks** is an Enterprise-grade static code analysis system, enhanced with a unique **Meta-Reflection** layer. Unlike traditional linters, Feniks not only finds syntax errors but analyzes the *meaning* and *quality* of the development reasoning process, detects long-term code trends, and manages AI operational budgets.

It was designed as an analytical layer over the **RAE (Reflective Agent Engine)**.

---

## 🚀 Key Features

### 1. Knowledge Architecture (Knowledge Base)
*   **Ingest Pipeline**: Intelligent code parsing (JS/TS, Python, HTML) into vector form (Qdrant).
*   **Semantic Understanding**: Uses embedding models to understand code intent, not just structure.

### 2. Meta-Reflection Engine (The Brain)
*   **Post-Mortem Loop**: Analysis of individual agent sessions for reasoning errors, decision loops, and costs.
*   **Longitudinal Loop**: Detection of trends over time (e.g., "Code quality in Auth module has been declining for 3 weeks").
*   **Self-Model Loop**: System monitors its own performance and risk of "Alert Fatigue".

### 3. Governance & Guardrails
*   **Cost Controller**: Strict control of token budgets at project and session levels.
*   **Quality Policies**: Enforcement of reasoning standards (e.g., "No empty thoughts before action").
*   **Behavior Risk Policies**: MaxBehaviorRiskPolicy, ZeroRegressionPolicy for legacy systems.

### 4. Legacy Behavior Guard 🆕
*   **Behavior Contracts**: Replaces regression tests for systems without tests.
*   **Snapshot Comparison**: Compares behavior before/after refactoring.
*   **Risk Scoring**: Automatic regression risk assessment (0.0-1.0).
*   **Multi-layer Validation**: HTTP status, DOM elements, log patterns.
*   **CI/CD Integration**: Block merge on high risk.
*   Details in [docs/LEGACY_BEHAVIOR_GUARD.md](docs/LEGACY_BEHAVIOR_GUARD.md)

### 5. AngularJS Migration Recipes 🆕
*   **Automated Migration**: 5 specialized recipes for AngularJS → Next.js migration
*   **Controller to Component**: Automatic conversion of controllers to React components
*   **Template to JSX**: HTML templates → TSX with full directive support
*   **Routing Migration**: $routeProvider/ui-router → Next.js App Router
*   **Scope to Hooks**: $scope/$rootScope → useState/Context API
*   **Behavior Guard Integration**: Validate migrations with automated testing
*   Details in [docs/ANGULARJS_MIGRATION.md](docs/ANGULARJS_MIGRATION.md)

### 6. Availability
*   **CLI**: Powerful command-line tool for CI/CD integration.
*   **REST API**: Modern API (FastAPI) for integration with dashboards and external tools.
*   **Behavior CLI**: Dedicated commands for Legacy Behavior Guard (`feniks behavior`).

---

## ⚡ Quick Start

### Requirements
*   Python 3.10+
*   Qdrant (running locally or in cloud)
*   Environment variables (copy `.env.example` to `.env`)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/glesniowski/feniks.git
cd feniks

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install in development mode
pip install -e .
```

### CLI Usage

**1. Ingest (Feed knowledge base):**
```bash
feniks ingest --jsonl-path ./data/source_code.jsonl --collection my_project_v1 --reset
```

**2. Analysis (Run pipeline):**
```bash
feniks analyze --project-id my_project --collection my_project_v1 --output report.md
```

**3. Start API:**
```bash
feniks serve-api --port 8000
```

**4. Legacy Behavior Guard (testing without tests):**
```bash
# Record legacy system behavior
feniks behavior record --project-id my_app --scenario-id login --environment legacy --output legacy_snapshots.jsonl

# Build contracts
feniks behavior build-contracts --project-id my_app --input legacy_snapshots.jsonl --output contracts.jsonl

# Check refactored system
feniks behavior check --project-id my_app --contracts contracts.jsonl --snapshots candidate_snapshots.jsonl --output results.jsonl --fail-on-violations
```

**5. AngularJS Migration:**
```python
from feniks.core.refactor.recipes.angularjs import (
    ControllerToComponentRecipe,
    TemplateToJsxRecipe,
    RoutingToAppRouterRecipe
)

# Migrate controllers to Next.js components
controller_recipe = ControllerToComponentRecipe()
plan = controller_recipe.analyze(system_model)
result = controller_recipe.execute(plan, chunks, dry_run=False)
```

---

## 🏛️ Architecture Overview

Feniks follows Clean Architecture / Hexagonal principles, separating business logic from infrastructure.

```
feniks/
├── apps/           # Entry points (CLI, API, Workers)
├── core/           # Business logic (Reflection, Evaluation, Policies)
├── adapters/       # Integrations (Qdrant, RAE, LLM)
├── infra/          # Technical infrastructure (Logging, Tracing, Metrics)
└── config/         # Configuration (Pydantic Settings)
```

Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📊 Metrics and Observability

Feniks natively supports structured logging (JSON) and business metrics.

*   **Trace ID**: Each operation has a unique trace identifier.
*   **Metrics**:
    *   `feniks_quality_score`: Current project quality score.
    *   `feniks_cost_total`: Total operational cost.
    *   `feniks_recommendations_count`: Number of generated remediation suggestions.

---

## 📚 Documentation

### Architecture and Mechanisms
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture, data flow, components
- **[ANALYSIS_MECHANISMS.md](docs/ANALYSIS_MECHANISMS.md)** - 🆕 Detailed description of analysis mechanisms (Post-Mortem, Rules Engine, Policies)
- **[OVERVIEW.md](docs/OVERVIEW.md)** - High-level system overview

### Legacy Behavior Guard
- **[LEGACY_BEHAVIOR_GUARD.md](docs/LEGACY_BEHAVIOR_GUARD.md)** - 🆕 Complete guide to Legacy Behavior Guard
- **[BEHAVIOR_CONTRACT_MODELS.md](docs/BEHAVIOR_CONTRACT_MODELS.md)** - 🆕 Behavior models specification
- **[examples/](docs/examples/)** - 🆕 Example YAML scenarios (UI, API, CLI)

### AngularJS Migration
- **[ANGULARJS_MIGRATION.md](docs/ANGULARJS_MIGRATION.md)** - 🆕 Complete guide to AngularJS → Next.js migration
- **[Feniks–Recipe_Pack_AngularJS_1-3.md](docs/Feniks–Recipe_Pack_AngularJS_1-3.md)** - AngularJS Recipe Pack specification

### Refactoring and Recipes
- **[PYTHON_REFACTORING_PIPELINE.md](docs/PYTHON_REFACTORING_PIPELINE.md)** - Python refactoring pipeline documentation
- **[JAVASCRIPT__TYPESCRIPT-AngularJS-React-Next.md](docs/JAVASCRIPT__TYPESCRIPT-AngularJS-React-Next.md)** - JavaScript/TypeScript migration guide

### For Developers
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines

---

## 🎯 Project Status

- **Version:** 0.4.0 (AngularJS Migration Ready)
- **Status:** ⭐⭐⭐⭐⭐ Production Ready
- **Test Coverage:** 80%+
- **Commits:** 80+
- **Lines of Code:** ~27,000+
- **Last Update:** 2025-11-27

### Latest Additions (2025-11-27)
- ✅ **AngularJS Migration Recipes** - Complete Migration Pack (5 recipes, ~6,000 lines)
  - Controller to Component recipe (automatic conversion)
  - Directive to Component/Hook recipe (smart strategy selection)
  - Template to JSX recipe (full directive support)
  - Routing to App Router recipe ($routeProvider/ui-router → Next.js)
  - Scope to Hooks recipe ($scope/$rootScope → React hooks)
  - Behavior Guard integration (automated testing)
  - Comprehensive test suite (15+ tests)
  - Full documentation and examples

### Previous Additions (2025-11-26)
- ✅ **Legacy Behavior Guard - Phase 3** - Enterprise Ready Complete (8 commits, 3,500 lines)
  - UI runner with Playwright (browser automation)
  - Storage abstraction layer (pluggable backends)
  - Postgres storage backend (relational + versioning)
  - Qdrant storage backend (semantic search)
  - Shared scenario library (cross-project sharing)
  - Grafana dashboards (9 panels, metrics visualization)
  - Comprehensive test suite (15+ tests)
- ✅ **Legacy Behavior Guard - Phase 2** - Deep Integration Complete (9 commits, 2,500 lines)
- ✅ **Legacy Behavior Guard - Phase 1** - Complete (6 commits, 2,700 lines)
- ✅ **Enterprise Upgrade** - 14 tasks, 80%+ coverage (14 commits, 1,868 lines)
- ✅ **CI/CD Pipeline** - GitHub Actions multi-version testing
- ✅ **OpenTelemetry + Prometheus** - Full observability
- ✅ **Auth + RBAC** - JWT authentication, role-based access

---

## 📋 Implementation Status

Clear overview of what's **implemented and working** vs what's **planned** for future releases:

### Core Features

| Feature | Status | Implementation | Notes |
|---------|--------|----------------|-------|
| **Knowledge Base (Qdrant)** | ✅ **Implemented** | 100% | Fully operational vector storage |
| **Ingest Pipeline** | ✅ **Implemented** | 100% | JSONL loading, embeddings, TF-IDF |
| **Analysis Pipeline** | ✅ **Implemented** | 100% | System model, capabilities, dependencies |
| **Meta-Reflection Engine** | ✅ **Implemented** | 90% | Post-mortem analysis, trend detection |
| **Cost Controller** | ✅ **Implemented** | 100% | Token budgets, spend tracking |
| **Quality Policies** | ✅ **Implemented** | 100% | Policy enforcement, violations |
| **CLI Interface** | ✅ **Implemented** | 100% | Full CLI with all commands |
| **REST API (FastAPI)** | ✅ **Implemented** | 100% | Production-ready API |
| **Metrics & Observability** | ✅ **Implemented** | 100% | OpenTelemetry, Prometheus, Grafana |
| **Auth & RBAC** | ✅ **Implemented** | 100% | JWT, role-based access control |

### Legacy Behavior Guard

| Feature | Status | Implementation | Notes |
|---------|--------|----------------|-------|
| **Core Framework** | ✅ **Implemented** | 100% | Scenario, Contract, Snapshot models |
| **API Runner** | ✅ **Implemented** | 100% | HTTP/REST API testing |
| **CLI Runner** | ✅ **Implemented** | 100% | Command-line testing |
| **UI Runner (Playwright)** | ✅ **Implemented** | 100% | Browser automation |
| **Storage Abstraction** | ✅ **Implemented** | 100% | Pluggable backend system |
| **Postgres Backend** | ✅ **Implemented** | 100% | Relational storage + versioning |
| **Qdrant Backend** | ✅ **Implemented** | 100% | Semantic search for scenarios |
| **Shared Library** | ✅ **Implemented** | 100% | Cross-project scenario sharing |
| **Grafana Dashboards** | ✅ **Implemented** | 100% | 9 panels, metrics visualization |
| **CLI Commands** | ✅ **Implemented** | 100% | `feniks behavior` commands |

### AngularJS Migration

| Feature | Status | Implementation | Notes |
|---------|--------|----------------|-------|
| **Controller to Component** | ✅ **Implemented** | 90% | See Known Limitations |
| **Directive to Component** | ✅ **Implemented** | 90% | Smart strategy selection |
| **Template to JSX** | ✅ **Implemented** | 75% | Basic directives automated |
| **Routing to App Router** | ✅ **Implemented** | 85% | $routeProvider & ui-router |
| **Scope to Hooks** | ⚠️ **Partial** | 40% | **Analysis only** - generates infrastructure |
| **Behavior Guard Integration** | ✅ **Implemented** | 100% | Test scenario generation |
| **CLI Migration Command** | ✅ **Implemented** | 100% | `feniks angular migrate` |
| **End-to-End Demo** | ✅ **Implemented** | 100% | Complete working example |

### Refactoring Recipes

| Feature | Status | Implementation | Notes |
|---------|--------|----------------|-------|
| **Reduce Complexity** | ✅ **Implemented** | 100% | Cyclomatic complexity reduction |
| **Extract Function** | ✅ **Implemented** | 100% | Long method refactoring |
| **Modernize Syntax** | ✅ **Implemented** | 100% | Python 3.10+ features |
| **AngularJS Recipes** | ✅ **Implemented** | 70-75% | See AngularJS Migration above |
| **React Recipes** | 📅 **Planned** | 0% | Q1 2026 |
| **Vue.js Recipes** | 📅 **Planned** | 0% | Q2 2026 |

### External Integrations

| Feature | Status | Implementation | Notes |
|---------|--------|----------------|-------|
| **RAE Integration** | ⚠️ **Partial** | 30% | Config ready, E2E example needed |
| **GitHub Actions** | ✅ **Implemented** | 100% | CI/CD pipeline |
| **Lighthouse CI** | 📅 **Planned** | 0% | Architecture designed |
| **ng-migration-assistant** | 📅 **Planned** | 0% | Architecture designed |
| **Rector (PHP)** | 📅 **Planned** | 0% | Architecture designed |
| **PHPStan** | 📅 **Planned** | 0% | Architecture designed |

### Legend

- ✅ **Implemented** - Feature is complete and production-ready
- ⚠️ **Partial** - Feature is partially implemented, see notes
- 📅 **Planned** - Feature is designed but not yet implemented

---

## 🌟 Use Cases

### 1. AngularJS to Next.js Migration
Modernize legacy AngularJS applications with automated code transformation:
- Automatic controller → component conversion (85-90% automated)
- Template → JSX transformation with ng-directive support (70-80% automated)
- Routing migration to Next.js App Router (85-95% automated)
- State management analysis and infrastructure generation (scope → hooks)
- Behavior validation with automated regression testing
- **Overall**: 70-75% automation, 25-30% manual work required
- See [Known Limitations](docs/ANGULARJS_MIGRATION.md#known-limitations) for details

### 2. Legacy System Refactoring
Refactor systems without breaking functionality:
- Record behavior contracts before refactoring
- Apply automated or manual refactorings
- Validate behavior preservation
- Risk assessment and reporting

### 3. Code Quality Analysis
Continuous code quality monitoring:
- Meta-reflection on development processes
- Trend detection over time
- Cost tracking and optimization
- Automated recommendations

---

## 🤝 Contributing

We welcome contributions! Please review [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) before submitting a PR.

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Examples**: [docs/examples/](docs/examples/)
- **Issues**: [GitHub Issues](https://github.com/glesniowski/feniks/issues)

---

**Feniks Team** - Grzegorz Leśniowski
*Bringing consciousness to code analysis.*

🦅 **Feniks doesn't just analyze code - it understands its meaning and evolution.**
