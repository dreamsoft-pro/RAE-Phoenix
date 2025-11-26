# AGENT PLAYBOOK: Feniks Refactoring Guidelines

**Target Audience:** AI Agents (RAE, Github Copilot, etc.) and Human Engineers.

This document defines the "Rules of Engagement" for modifying the Feniks codebase. Following these rules ensures stability, quality, and architectural integrity.

---

## 1. Core Mandates (The "Prime Directives")

1.  **Do No Harm**: Never break existing tests. If a change requires breaking a test, the test must be updated *with justification*.
2.  **Hexagonal Purity**:
    *   **Core** (`feniks/core`) NEVER imports from **Adapters** or **Apps**.
    *   Business logic must be testable without IO (Mock IO).
3.  **Type Safety**: All new code must be strictly typed (`mypy` compliant).
4.  **Test First**: Create a test case (or use a Golden Fixture) *before* implementing complex logic.

---

## 2. Workflow for AI Agents

### Phase 1: Understanding
*   Read `docs/ARCHITECTURE.md` to understand module boundaries.
*   Read `docs/REFLECTION_LOOPS.md` if modifying the analysis logic.
*   Check `tests/fixtures/golden` to see expected inputs/outputs.

### Phase 2: Implementation
*   **Modifying Core**:
    *   Add new Domain Models in `core/models` if needed.
    *   Implement pure logic in `core/reflection` or `core/evaluation`.
    *   Ensure 100% unit test coverage for new logic.
*   **Modifying Adapters**:
    *   Implement the interface defined in Core.
    *   Use `feniks/infra` for logging and metrics.
    *   Handle external errors (Network, Timeout) gracefully and wrap them in `FeniksError`.

### Phase 3: Verification
*   Run Unit Tests: `./venv/bin/pytest feniks/tests/unit`
*   Run Golden Tests: `./venv/bin/pytest feniks/tests/golden` (Snapshot tests)
*   Run Linter: `ruff check .`

---

## 3. Golden Test Fixtures

We maintain a set of "Golden" input/output pairs to guarantee regression testing for the complex logic of Meta-Reflection.

*   **Location**: `tests/fixtures/golden/`
*   **Usage**:
    *   When tuning prompt logic or reflection rules, run the Golden Tests to ensure you haven't degraded the system's ability to detect known patterns (e.g., Loops, Empty Thoughts).
    *   If you *improve* the logic, update the Golden Outputs (`expected_*.json`) to reflect the new, better behavior.

---

## 4. Common Pitfalls (What NOT to do)

*   ❌ **Don't** put business logic in `apps/cli`. The CLI should only parse args and call Core.
*   ❌ **Don't** hardcode API keys. Use `feniks/config/settings.py`.
*   ❌ **Don't** print to stdout. Use `feniks.infra.logging`.
*   ❌ **Don't** ignore the Policy Manager. All sessions must be checked against policies.

---

**Status**: Active
**Maintainer**: Feniks Core Team
