# Code vs. Documentation Audit Report: Feniks Project

**Date**: 2025-11-28
**Status**: Analysis Complete
**Target**: `/feniks` directory vs. `docs/ARCHITECTURE.md`, `docs/AUDIT_CODE_VS_DOCS.md`

---

## Executive Summary

The **Feniks** codebase implements the majority of the high-level architecture described in `docs/ARCHITECTURE.md`, specifically the Clean Architecture layers (Core, Adapters, Apps). However, there are significant discrepancies in naming conventions, module organization, and feature completeness. Several architectural components exist as "empty shells" in the codebase, while other robust features in the code are undocumented.

**Overall Alignment**: **~70%**
- **Core Architecture**: Aligned (Clean Architecture layers present).
- **Behavior Guard**: Implemented but structural details differ from docs.
- **Refactoring Engine**: Implemented but functionality oversold in docs (see [Known Limitations](#3-known-limitations--incomplete-features)).

---

## 1. Code Exists > Missing in Documentation (Undocumented Features)

The following components are fully or partially implemented in the codebase but are **not** adequately described in `docs/ARCHITECTURE.md`.

| Component | Location | Description |
|-----------|----------|-------------|
| **Security Module** | `feniks/security/` | Contains `auth.py` and `rbac.py` (Role-Based Access Control). The architecture docs mention "Policies" but not a dedicated security/auth module. |
| **Ingest Adapters** | `feniks/adapters/ingest/` | Contains `jsonl_loader.py` and `filters.py`. Critical for loading data, but the Architecture diagram only shows "Storage (Qdrant)" and "RAE Client". |
| **Refactor Core** | `feniks/core/refactor/` | A massive module containing the entire AngularJS migration logic (`recipes/angularjs`). The Architecture doc focuses on "Reflection" and "Evaluation" but barely mentions this refactoring engine. |
| **Plugins** | `feniks/plugins/` | Contains `javascript.py`. Suggests a plugin architecture for language support, which is not documented. |
| **Workers** | `feniks/apps/workers/` | Implemented as an app entry point, but only vaguely referred to as "Async Workers" in diagrams without detail on their role. |

---

## 2. Documentation Exists > Missing in Code (Ghost Features)

The following components are described in the architecture or structure but appear to be empty shells or missing.

| Component | Location | Status |
|-----------|----------|--------|
| **Governance** | `feniks/governance/` | **Empty Shell**. Directory exists but contains only `__init__.py`. |
| **Observability** | `feniks/observability/` | **Empty Shell**. Directory exists but contains only `__init__.py`. (Note: Logging/Tracing is currently handled in `feniks/infra`). |
| **Resolve Functions** | *Docs: AngularJS Migration* | **Missing**. Migration of AngularJS `resolve` functions to Server Components is documented but not implemented. |

---

## 3. Naming & Structural Discrepancies

There is a mismatch between the specific class names/modules described in high-level docs and the actual code.

| Concept in Docs | Actual Code Implementation | Notes |
|-----------------|----------------------------|-------|
| `ReflectionEngine` | `MetaReflectionEngine` | Located in `feniks/core/reflection/engine.py`. |
| `EvaluationPipeline` | `AnalysisPipeline` | Located in `feniks/core/evaluation/pipeline.py`. |
| `BehaviorChecker` | `ComparisonEngine` (likely) | `feniks/core/behavior/comparison_engine.py` seems to handle the checking logic. |
| `Contract Builder` | `ContractGenerator` | `feniks/core/behavior/contract_generator.py`. |

---

## 4. Known Limitations & Incomplete Features

Based on `docs/AUDIT_CODE_VS_DOCS.md` verification:

### AngularJS Migration Recipes
The documentation claims high levels of automation (85-95%), but the reality is lower (~70-75%).

*   **ScopeToHooksRecipe**:
    *   **Claim**: "Converts $scope to useState/useEffect".
    *   **Reality**: Analyzes scope usage and generates a `GlobalContext` boilerplate but **does not** rewrite the logic within components.
*   **Service Generation**:
    *   **Claim**: Generates service stubs.
    *   **Reality**: Generates `// TODO` comments for imports, requiring manual creation of files.
*   **$http Conversion**:
    *   **Claim**: Converts `$http` to `fetch`.
    *   **Reality**: Generates `// TODO` comments only.

---

## Recommendations

1.  **Update Architecture Docs**: Rename `ReflectionEngine` to `MetaReflectionEngine` and `EvaluationPipeline` to `AnalysisPipeline` in the diagrams to match reality.
2.  **Document Security & Ingest**: Add sections for `feniks/security` and `feniks/adapters/ingest` to `ARCHITECTURE.md`.
3.  **Cleanup Empty Shells**: Decide whether `governance` and `observability` are planned features or deprecated ideas. If planned, add `TODO` files; if not, remove the directories.
4.  **Honest Refactoring Docs**: Update the AngularJS migration docs to clearly state that `ScopeToHooks` is an *analysis* tool, not a *conversion* tool, to manage user expectations.
