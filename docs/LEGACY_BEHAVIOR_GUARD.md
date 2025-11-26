# LEGACY_BEHAVIOR_GUARD

**How Feniks becomes a safety umbrella over refactoring without tests**

**Status:** Implemented
**Related:** Feniks + RAE, legacy systems (AngularJS, Python, other)

---

## 1. Problem We're Solving

In practice:

- Large legacy systems exist (AngularJS, old Python backend, etc.)
- Systems **work for years**, but:
  - have no tests (or minimal coverage)
  - code is complex and full of technical debt
  - any major change risks regression in forgotten areas

Refactoring/migration (e.g., AngularJS → Next.js, Python → Python 3.x + types) is:

- **necessary** (maintenance, performance, security)
- but **risky**, because traditional regression tests are missing

**Legacy Behavior Guard** is Feniks' layer whose goal is:

> *Build a "safety umbrella" over refactoring legacy systems without tests, using real system behavior (logs, user paths, response snapshots) as a test substitute.*

---

## 2. High-Level Idea

### 2.1. How It Works

1. **Observe existing legacy system** during typical user/API/CLI scenarios
2. From observations build:
   - `BehaviorScenario` – scenario description
   - `BehaviorSnapshot` – concrete executions
   - `BehaviorContract` – generalized behavior contract
3. After refactoring (new system version) run same scenarios:
   - collect new snapshots
   - compare them with contracts
4. Feniks generates:
   - `BehaviorCheckResult`
   - report with violations
   - synthetic `risk_score` for refactor
   - recommendations (merge / fix / rollback)

**Key insight:**
> We don't need full test coverage to intelligently catch the most dangerous regressions.

---

## 3. Feniks' Role in Architecture

Legacy Behavior Guard fits into existing Feniks architecture:

- **Core / Models** – behavior model implementation:
  - `BehaviorScenario`, `BehaviorSnapshot`, `BehaviorContract`, `BehaviorCheckResult`, `BehaviorViolation`
- **Core / Reflection** – behavior analysis:
  - new modules: `behavior_post_mortem.py`, `behavior_longitudinal.py`
- **Core / Policies** – acceptable risk policies:
  - e.g., `MaxBehaviorRiskPolicy`
- **Adapters / Workers** – scenario execution and snapshot collection:
  - integrations with Playwright/Puppeteer (UI)
  - simple HTTP/CLI runner (API, batch)
- **Apps / CLI & API** – commands:
  - `feniks behavior record`
  - `feniks behavior build-contracts`
  - `feniks behavior check`

Feniks remains the "meta-reflection brain" – Behavior Guard is an additional loop focused on *whole system behavior*, not just code.

---

## 4. Data Models (Brief)

Detailed model specification is in `BEHAVIOR_CONTRACT_MODELS.md`.
Below is a brief summary used in this document:

- **BehaviorScenario** – scenario description (UI/API/CLI)
- **BehaviorSnapshot** – single scenario execution (collected logs, HTTP, DOM)
- **BehaviorContract** – generalized contract from multiple snapshots
- **BehaviorCheckResult** – result of comparing new snapshot with contract
- **BehaviorViolation** – single contract breach

---

## 5. Data Flow – Step by Step

### 5.1. Phase 1 – Register Legacy Scenarios

**Goal:** Capture representative behaviors of working legacy system.

1. System owner (or AI agent) chooses:
   - most important business flows (e.g., "place order", "issue invoice")
   - critical API endpoints (e.g., `/api/orders`, `/api/invoices`)
   - typical batch/CLI tasks (e.g., `python recalc_stats.py`)

2. For each flow create `BehaviorScenario`:
   - `category`: `"ui"`, `"api"`, `"cli"`, `"batch"` or `"mixed"`
   - `input`: user action sequence / API request / CLI command
   - `success_criteria`: minimal "must work" conditions (statuses, DOM elements, no errors in logs)

3. Save scenarios in Postgres (and optionally index vectorially)

CLI (proposal):

```bash
feniks behavior define-scenario \
  --project-id my_legacy_app \
  --from-file docs/scenarios/order_create.yaml
```

### 5.2. Phase 2 – Collect Legacy Snapshots

**Goal:** Collect real scenario executions in legacy environment.

1. Runner (e.g., Playwright, HTTP client, CLI wrapper) executes scenarios on old system version (AngularJS, old backend etc.)

2. Collects:
   - HTTP responses
   - DOM fragments (e.g., presence of key selectors/texts)
   - application/server logs

3. Creates `BehaviorSnapshot`, marking:
   - `environment = "legacy"`
   - `success = True/False` (per BehaviorSuccessCriteria)
   - possible `BehaviorViolation` (legacy can also have bugs)

CLI:

```bash
feniks behavior record \
  --project-id my_legacy_app \
  --scenario-id order_create \
  --environment legacy \
  --output data/behavior_legacy.jsonl
```

### 5.3. Phase 3 – Build Contracts

**Goal:** Derive stable behavior contracts from multiple snapshots.

1. Feniks analyzes collected snapshots:
   - removes outliers (e.g., one-time network errors)
   - finds common characteristics:
     - range of allowed HTTP statuses
     - minimal DOM element set
     - log patterns

2. Creates `BehaviorContract` for each scenario:
   - `required_status_codes`, `must_have_selectors`, `forbidden_patterns` etc.
   - tolerance thresholds (`max_error_rate`, `max_duration_ms_p95`)

3. Saves contracts in Postgres, with reference to source snapshots

CLI:

```bash
feniks behavior build-contracts \
  --project-id my_legacy_app \
  --input data/behavior_legacy.jsonl \
  --output data/behavior_contracts.jsonl
```

### 5.4. Phase 4 – Check New Version (Candidate)

**Goal:** Run same scenarios on new system version (candidate) and assess risk.

1. Runner executes scenarios on new version:
   - `environment = "candidate"` (Next.js, new backend, refactored Python)

2. Generates new `BehaviorSnapshot` (candidate)

3. Feniks for each snapshot:
   - finds appropriate `BehaviorContract`
   - compares snapshot with contract
   - creates `BehaviorCheckResult`

CLI:

```bash
feniks behavior check \
  --project-id my_legacy_app \
  --environment candidate \
  --contracts data/behavior_contracts.jsonl \
  --snapshots data/behavior_candidate.jsonl \
  --output data/behavior_check_results.jsonl
```

### 5.5. Phase 5 – Report and Decisions

**Goal:** Based on behavior check results, decide on merge/rollback/fixes.

1. Feniks aggregates `BehaviorCheckResult`:
   - counts how many scenarios:
     - passed without violations
     - passed with minor violations
     - didn't pass (serious regressions)
   - calculates `risk_score` (global)

2. Creates extended `FeniksReport` containing:
   - `behavior_checks_summary` (how many pass/fail, max risk)
   - list of `behavior_violations`
   - recommendation:
     - ✅ "low risk – can merge"
     - ⚠️ "medium risk – manual tests of modules X recommended"
     - ❌ "high risk – don't merge, fix scenarios Y, Z"

3. Report can be:
   - displayed in CLI
   - returned by API
   - saved as CI artifact (GitHub Actions / GitLab CI)

---

## 6. Policies and Guardrails

### 6.1. Example Policy: MaxBehaviorRiskPolicy

Policy that prevents marking refactor as "safe" if:

- `max_risk_score > 0.5` or
- number of `failed scenarios > N`

Pseudocode (Core / Policies):

```python
class MaxBehaviorRiskPolicy(Policy):
    def evaluate(self, report: FeniksReport) -> PolicyEvaluationResult:
        summary = report.behavior_checks_summary
        if not summary:
            return PolicyEvaluationResult(
                passed=False,
                reason="No behavior checks were executed."
            )

        if summary.max_risk_score > 0.5:
            return PolicyEvaluationResult(
                passed=False,
                reason=f"Max behavior risk score {summary.max_risk_score} exceeds 0.5"
            )

        if summary.total_failed > 0:
            return PolicyEvaluationResult(
                passed=False,
                reason=f"{summary.total_failed} scenarios failed behavior checks."
            )

        return PolicyEvaluationResult(passed=True, reason="Behavior risk within limits.")
```

---

## 7. Use Cases

### 7.1. AngularJS → Next.js (UI-heavy)

**Legacy:** old AngularJS app, no tests, complex DOM, many routes.

**Goal:** rewrite interface to Next.js, preserving:
- key paths
- form behavior
- backend communication

**With Legacy Behavior Guard:**

1. Record UI scenarios (Playwright)
2. Generate snapshots and contracts
3. After moving fragment to Next.js:
   - run same scenarios on new front
   - look at Feniks report:
     - are key elements missing
     - does API respond the same
     - did new errors appear in logs

### 7.2. Python → Python (Backend Refactor)

**Legacy:** Python monolith, no tests, extensive business code.

**Goal:** refactor (e.g., add types, extract modules, improve architecture).

**With Legacy Behavior Guard:**

1. Define CLI/API scenarios:
   - typical calls (e.g., "calculate statistics", "generate report")
2. Collect legacy snapshots (input → output + logs)
3. Refactor code (manually or semi-automatically)
4. Run same scenarios on new code:
   - compare response structure
   - compare logs
5. Feniks reports behavior risk

---

## 8. CI/CD Integration

### 8.1. Pipeline (GitHub Actions – Example)

**Step:** build & test (what you already have)

**Step:** behavior-check (for legacy refactors):
- Execute scenarios on candidate environment
- Collect new `BehaviorSnapshot`
- Run `feniks behavior check`
- Fail job if safety policies don't pass

**Artifacts:**
- `behavior_candidate.jsonl`
- `behavior_check_results.jsonl`
- `feniks_behavior_report.md`

Example workflow:

```yaml
jobs:
  behavior-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install -e ".[dev]"

      - name: Record candidate behavior
        run: |
          feniks behavior record \
            --project-id ${{ github.repository }} \
            --scenario-id critical-flows \
            --environment candidate \
            --output behavior_candidate.jsonl

      - name: Check behavior
        run: |
          feniks behavior check \
            --project-id ${{ github.repository }} \
            --contracts behavior_contracts.jsonl \
            --snapshots behavior_candidate.jsonl \
            --output behavior_results.jsonl \
            --fail-on-violations

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: behavior-reports
          path: |
            behavior_candidate.jsonl
            behavior_results.jsonl
```

---

## 9. Implementation Phases

### Phase 1 – Minimal Viable Guard ✅ COMPLETE

- ✅ Model implementation (BehaviorScenario, Snapshot, Contract, CheckResult)
- ✅ Simple CLI:
  - `behavior record`
  - `behavior build-contracts`
  - `behavior check`
- ✅ Integration with FeniksReport (without advanced policies)
- ✅ Policies: MaxBehaviorRiskPolicy, MinimumCoverageBehaviorPolicy, ZeroRegressionPolicy

### Phase 2 – Deep Integration (TODO)

- Deep integration in reflection loops:
  - post-mortem (one-time refactor)
  - longitudinal (behavior quality trend over time)
- Policy threshold parametrization
- Support for AngularJS / Next.js (UI runner) and simple HTTP runner
- Scenario storage in Postgres/Qdrant

### Phase 3 – Enterprise Ready (TODO)

- Integration with:
  - Playwright / Puppeteer (UI)
  - logging systems (ELK, Loki, Datadog)
  - dashboards (Grafana)
- BehaviorContract versioning (v1, v2…)
- Shared scenario library (for common system patterns)

---

## 10. Current Implementation Status

### ✅ Completed (Phase 1)

1. **Models** (`feniks/core/models/behavior.py`):
   - All behavior models implemented
   - Full Pydantic validation
   - Type safety and documentation

2. **Policies** (`feniks/core/policies/behavior_risk_policy.py`):
   - MaxBehaviorRiskPolicy
   - MinimumCoverageBehaviorPolicy
   - ZeroRegressionPolicy
   - Integration with reflection system

3. **CLI Commands** (`feniks/apps/cli/behavior.py`):
   - `behavior define-scenario`
   - `behavior record`
   - `behavior build-contracts`
   - `behavior check`
   - Full argparse integration

4. **Tests**:
   - 40+ unit tests for behavior models
   - Comprehensive policy tests
   - Integration flow tests

5. **Documentation**:
   - BEHAVIOR_CONTRACT_MODELS.md
   - This document (LEGACY_BEHAVIOR_GUARD.md)
   - Updated ARCHITECTURE.md

### 🚧 TODO (Phase 2 & 3)

1. **Scenario Execution**:
   - Playwright/Puppeteer runner for UI scenarios
   - HTTP client for API scenarios
   - Subprocess wrapper for CLI scenarios

2. **Contract Generation**:
   - Snapshot analysis algorithms
   - Outlier detection
   - Pattern extraction (HTTP, DOM, logs)

3. **Storage Layer**:
   - Postgres tables for scenarios/snapshots/contracts
   - Qdrant vector indexing for scenario similarity
   - RAE integration for meta-reflections

4. **Reflection Loops**:
   - `behavior_post_mortem.py`
   - `behavior_longitudinal.py`
   - Integration with existing reflection engine

---

## 11. Quick Start Guide

### Step 1: Define Scenarios

Create a scenario YAML file (`scenarios/login.yaml`):

```yaml
id: login-scenario
project_id: my-app
category: ui
name: User Login Flow
description: Test successful user login with valid credentials
environment: legacy
tags:
  - authentication
  - critical
input:
  ui_actions:
    - action_type: navigate
      url: /login
    - action_type: type
      selector: "#username"
      text: admin
    - action_type: type
      selector: "#password"
      text: secret123
    - action_type: click
      selector: "#submit-button"
success_criteria:
  dom:
    required_selectors:
      - "#dashboard"
      - ".user-profile"
    forbidden_selectors:
      - ".error-message"
  logs:
    forbidden_patterns:
      - ERROR
      - Exception
```

Define the scenario:

```bash
feniks behavior define-scenario \
  --project-id my-app \
  --from-file scenarios/login.yaml
```

### Step 2: Record Legacy Behavior

```bash
feniks behavior record \
  --project-id my-app \
  --scenario-id login-scenario \
  --environment legacy \
  --count 10 \
  --output data/legacy_snapshots.jsonl
```

### Step 3: Build Contracts

```bash
feniks behavior build-contracts \
  --project-id my-app \
  --input data/legacy_snapshots.jsonl \
  --output data/contracts.jsonl \
  --min-snapshots 3
```

### Step 4: Check Refactored Version

```bash
# Record behavior on new version
feniks behavior record \
  --project-id my-app \
  --scenario-id login-scenario \
  --environment candidate \
  --count 10 \
  --output data/candidate_snapshots.jsonl

# Check against contracts
feniks behavior check \
  --project-id my-app \
  --contracts data/contracts.jsonl \
  --snapshots data/candidate_snapshots.jsonl \
  --output data/check_results.jsonl \
  --fail-on-violations
```

---

## 12. Summary

Legacy Behavior Guard:

- **doesn't replace tests**
- but provides a real, operational safety umbrella over legacy system refactoring
- integrates:
  - real system behavior (snapshots)
  - behavior contracts (BehaviorContract)
  - risk policies (MaxBehaviorRiskPolicy)
  - Feniks reports

**Status:** Phase 1 (Minimal Viable Guard) complete. Ready for Phase 2 integration with real scenario runners.

---

*Document version: 1.0*
*Last updated: 2025-11-26*
*Implementation status: Phase 1 Complete*
