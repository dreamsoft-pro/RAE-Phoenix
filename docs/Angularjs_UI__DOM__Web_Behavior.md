# docs/UI__DOM__Web_Behavior.md
UI, DOM & Web Behavior Contracts in Feniks

A Unified Model for Capturing, Comparing and Validating Frontend Behavior

Feniks provides a structured and verifiable framework for capturing, analyzing and validating UI and DOM behavior across different frontend implementations.

This is essential for:

Legacy AngularJS → React/Next.js migrations,

Large refactors without tests,

Stabilizing UI/UX across releases,

Preventing regressions,

Ensuring contract-based frontend behavior,

Reconstructing functional UI knowledge from templates,

Long-term reasoning via RAE.

Feniks introduces:

UiTemplateView – structural representation of UI from HTML/CSS,

DOMContract – invariant DOM elements that must exist,

UIBehaviorScenario – user flows and interactive behavior,

UISnapshot – DOM + text + selectors captured from runtime,

UIBehaviorReport – delta analysis between old and new implementations.

These abstractions allow for safe incremental frontend modernization, even without end-to-end tests.

1. UI Behavior Architecture in Feniks
[ HTML / CSS / JS Templates ]
          │
          ▼
[ UiTemplateView Extraction ]
          │
          ▼
[ DOM Contract Generation ]
          │
          ▼
[ UIBehaviorScenario (Flows) ]
          │
          ▼
[ Runtime Execution (Playwright/Puppeteer) ]
          │
          ▼
[ UI Snapshots ]
          │
          ▼
[ Feniks Comparison Engine ]
  - DOM diff
  - behavior invariants
  - structural risk score
          │
          ▼
[ UIBehaviorReport + RAE Memory ]


Feniks is responsible for:

extracting structure,

defining invariants,

verifying behavior,

producing risk-aware reports,

iterating improvements.

2. UiTemplateView – The Source of Truth

Feniks does not rely solely on browser runtime for legacy systems like AngularJS.

Instead, it first analyzes static templates:

.html templates (AngularJS),

.css / .less styles,

inline AngularJS directives.

Feniks builds a structural model:

{
  "template_path": "views/orders/list.html",
  "title_candidates": ["Orders", "Order List"],
  "repeat_blocks": [
    { "selector": "table#orders > tr[ng-repeat]" }
  ],
  "form_fields": [
    { "type": "text", "model": "order.name", "selector": "input[name='name']" }
  ],
  "action_buttons": [
    { "label": "Create Order", "selector": "button.btn-create" }
  ],
  "business_role": "Order List View"
}

UiTemplateView is the foundation for:

DOMContract generation,

behavior flow inference,

consistency checking after refactors.

3. DOMContract – Structural Invariants

A DOMContract is a minimal set of DOM properties that must remain stable.

Feniks generates DOMContract from:

UiTemplateView,

AngularJS structure,

business role metadata.

DOMContract enforces:
✔ Element existence

key selectors must be present

regardless of React/Next.js reimplementation

✔ Text invariants

stable labels

meaningful business terms

✔ Layout anchors

tables

forms

containers

toolbars

repeat blocks

CTA buttons

✔ Attribute invariants

ids,

ARIA attributes,

data attributes,

binding roles.

Example:

{
  "must_have_selectors": [
    "#orders-table",
    ".toolbar",
    "button#new-order"
  ],
  "must_have_text": [
    "Order List",
    "Create Order"
  ],
  "repeat_blocks": ["#orders-table > tbody > tr"]
}


If a new UI violates this contract → high-risk regression.

4. UIBehaviorScenario – User Flows & Interactions

Scenarios model actual user actions:

clicking,

navigation,

form filling,

selection,

async waits,

modal flows.

Feniks defines:

✔ High-level business flows

From curated templates:

Scenario: Create new order
1. Navigate to "/orders"
2. Click button#new-order
3. Fill form fields
4. Submit
5. Expect success banner

✔ Low-level DOM interactions

Generated automatically when needed.

Example:
{
  "name": "open_order_list",
  "actions": [
    { "type": "navigate", "url": "/orders" },
    { "type": "wait_for_selector", "selector": "#orders-table" }
  ],
  "success_criteria": {
    "required_selectors": ["#orders-table"],
    "required_text": ["Order List"]
  }
}

5. UISnapshot – Runtime Evidence

Snapshots contain:

serialized DOM,

visible text,

attributes,

CSS classes,

screenshots (optional),

timing metrics.

Captured by:

Playwright (preferred)

Puppeteer

Snapshot structure:

{
  "url": "/orders",
  "timestamp": "2025-11-26T21:33:00",
  "dom_tree_hash": "sha256:af82...",
  "text": ["Order List", "Create Order", ...],
  "selectors_present": ["#orders-table", ".toolbar"],
  "performance": {
    "dom_load": 220,
    "first_paint": 350
  }
}


Snapshots are compared before/after migration.

6. UIBehaviorReport – The Comparison Engine

Feniks compares:

✔ DOM structure

Before vs after:

missing selectors,

changed nesting,

removed elements,

altered form structures.

✔ Text invariants

Labels removed/renamed unintentionally.

✔ Interactive flows

BehaviorScenario success/failure.

✔ Regressions in async flows

Navigation timing
Modal availability
Loading indicators

✔ Performance changes

(Optional Lighthouse metrics)

Output example:
{
  "status": "warning",
  "missing_elements": ["button#new-order"],
  "text_changes": [
    { "old": "Order List", "new": "Orders Overview" }
  ],
  "scenario_failures": ["open_order_list"],
  "risk_score": 0.72
}


Risk scoring is crucial for safe migration.

7. Tooling Integrated With Feniks
7.1. Playwright (recommended)

navigate flows,

capture snapshots,

DOM diff,

screenshot diff,

error logs,

network logs.

Feniks uses Playwright to validate UIBehaviorScenario.

7.2. Puppeteer

Simpler Chromium-only runner.

7.3. Lighthouse CI

Optional for comparing UI performance:

LCP,

CLS,

FID,

Accessibility,

Best Practices.

7.4. DOM diff engines

Feniks uses:

structural diff,

semantic diff,

selector-level diff.

This enables controlled refactors without visual regressions.

8. Behavior Contracts for Web Requests

Feniks can extend UI behavior with:

HTTP request invariants,

API schemas,

success patterns,

data-binding checks.

Example:

{
  "endpoint": "/api/orders",
  "method": "GET",
  "schema_invariants": ["id", "status", "customer"],
  "status_code": 200
}


This ties frontend behavior to backend contracts.

9. LLM-Assisted UI Workflows

Claude/Gemini help with:

reasoning about template structure,

describing business semantics,

rewriting templates to JSX,

optimizing flows,

repairing inconsistencies,

writing React component logic.

Feniks provides:

UiTemplateView,

DOMContract,

Scenario definitions,

Snapshot deltas.

LLMs remain constrained by contracts → safe.

10. RAE Memory Integration

Feniks can persist:

UI evolution history,

behavior regressions,

fixed UI bugs,

template mappings,

migration decisions,

performance snapshots.

This enables:

multi-day collaborative refactor,

multi-agent execution,

historical reasoning,

architecture traceability.

11. Recommended Workflow
1. feniks ui scan-templates
2. feniks ui curate-templates
3. generate DOMContract
4. define BehaviorScenarios
5. run UISnapshots (Playwright)
6. migrate component (React/Next/AngularJS refactor)
7. run Feniks behavior-eval
8. examine UIBehaviorReport
9. store results in RAE
10. next iteration


This workflow ensures safe, controlled, and observable frontend modernization.

12. Summary

Feniks unifies all layers of UI behavior:

Layer	Purpose
UiTemplateView	structural static representation
DOMContract	invariants that must survive refactors
UIBehaviorScenario	flow definition
UISnapshot	runtime validation
UIBehaviorReport	diff + regressions + risk
Playwright/Puppeteer	execution engine
RAE Memory	long-term understanding

This gives you:

predictable migrations,

measurable stability,

refactors without blind spots,

behavior-driven modernization of legacy UI,

safe AngularJS → React/Next transitions.