# docs/JAVASCRIPT__TYPESCRIPT-AngularJS-React-Next.md

Przygotowany z myślą o:

Twoim legacy AngularJS (1.3.x) frontendzie,

przyszłej migracji do React / Next.js,

integracji z Feniksem i BehaviorGuard,

wykorzystaniu najlepszych narzędzi OSS:
jscodeshift, Babel, Recast, ngMigration Assistant, TS-Morph, ESLint, Prettier, Playwright,

oraz pełnego workflow z Claude/Gemini.

Dokument ma strukturę enterprise — gotową do użytku w projekcie OSS.

Feniks – OSS Integrations for JavaScript / TypeScript (AngularJS → React / Next.js)

Refactoring, Migration and UI Behavior Analysis for Large Frontend Codebases

Feniks provides a meta-reflection layer for modernizing legacy JavaScript systems, especially AngularJS 1.x frontends, and migrating them into React or Next.js.

Feniks does not reimplement parsing or codemods.
Instead, it orchestrates the strongest open-source toolchain in the industry and adds:

Behavior Contracts,

UI contracts from templates (HTML/CSS),

risk scoring,

architectural guidance,

snapshot-based regression checks,

and optional long-term memory via RAE.

This document describes the exact OSS tools Feniks integrates with for JavaScript, TypeScript, AngularJS, React, and Next.js.

1. Architecture Overview
[ AngularJS Templates + JS Controllers ]
            │
            ▼
[ Template Analysis Layer ]
  - HTML/CSS Parsers
  - UiTemplateView (Feniks)
  - AngularJS Migration Scanners
            │
            ▼
[ Transformation Layer ]
  - jscodeshift
  - Babel plugins
  - TS-Morph
  - JSX Skeleton Generators
            │
            ▼
[ React/Next.js Output Code ]
            │
            ▼
[ Feniks BehaviorGuard ]
  - DOM Contracts
  - UI Behavior Contracts
  - Snapshot Comparisons
            │
            ▼
[ LLM Executors + RAE Memory ]


Feniks is the orchestrator.
Open-source tools are the machinery.

2. Template & View Extraction (AngularJS)

AngularJS relies heavily on:

template-driven rendering,

ng-repeat, ng-if, ng-bind,

two-way binding through ng-model,

controller-as patterns,

custom directives.

Feniks integrates OSS tools to extract static structure from templates.

2.1. HTML / AngularJS Template Parsers
✔️ parse5

robust HTML parsing,

fully AST-based.

✔️ cheerio

jQuery-like selector engine for HTML.

✔️ AngularJS-aware heuristics:

Feniks adds logic for:

ng-repeat,

ng-model,

ng-click,

dynamic classes (ng-class),

conditional nodes (ng-switch, ng-if).

Output:
Feniks generates UiTemplateView (structural representation of each screen).

3. Static Analysis for Legacy AngularJS
3.1. Angular Migration Scanner (Google)
✔️ ngMigration Assistant

Analyzes:

controllers,

directives,

template bindings,

dependency graph,

AngularJS-specific risks.

Feniks integrates this scanner as:

feniks ui scan-angularjs --root ./app/


Output → angularjs_structural_report.json.

4. JavaScript / TypeScript Refactoring Tools

This layer performs the heavy lifting for migrating AngularJS to React/Next.

4.1. jscodeshift (Meta/Facebook)
✔️ core engine for transforming JS/TS AST

Used by React team for official codemods.

Feniks uses jscodeshift to:

transform controllers into React components,

convert AngularJS idioms to JS/TS-friendly shapes,

rewrite event handlers (ng-click → onClick),

lift business logic to services/hooks.

4.2. Babel + Plugins
✔️ perfect for template → JSX conversion

Babel plugins can:

inject JSX tags,

transform angular-style attributes,

rewrite expressions,

convert $scope.x into useState or props.

Feniks uses Babel to convert:

AngularJS template fragments → JSX skeleton,

inline expressions → JS expressions.

4.3. Recast
✔️ code generator preserving formatting

Used by:

jscodeshift,

many React ecosystem codemods.

Feniks uses Recast for:

stable AST transformations,

predictable diffs,

generating readable React code.

4.4. TS-Morph
✔️ deep TypeScript refactoring API

Used by Feniks to:

generate .d.ts for legacy code,

create Interface Maps,

extract typedefs,

detect unused properties,

build service architecture for Next.js.

4.5. ESLint + Prettier
✔️ mandatory tools for final formatting

Feniks runs:

ESLint for code health,

Prettier for consistent formatting.

Combined with codemods, this produces:

fully standardized code,

no legacy formatting artifacts.

5. AngularJS → React / Next.js Migration Tools
5.1. AngularJS → React Codemods (Community OSS)

Includes transforms for:

ng-repeat → .map(),

ng-click="foo()" → onClick={foo},

directive-based components → React components,

inline templates → JSX children.

Feniks integrates these codemods as first-pass skeleton generators.

5.2. JS Controller → React Component

Using:

AST analysis,

jscodeshift classes → function components rewrite,

scope detection to map $scope variables into useState hooks,

watchers → effects (useEffect).

Feniks verifies results with:

BehaviorContracts,

DOM Contracts,

UI TemplateView mapping.

5.3. Service Extraction

Large AngularJS controllers often mix:

view logic,

business logic,

data fetchers,

stateful objects.

Feniks:

extracts pure logic into services/*.ts,

extracts data access as React Query or SWR hooks,

moves state into useState/useReducer.

This is validated by SystemModel.ServiceGraph.

6. UI Behavior Analysis (React / Next / AngularJS)
Tools Feniks integrates with:
✔️ Playwright

for DOM snapshots,

event flows,

navigation checks,

performance bounds.

Used to validate:

behavior parity (AngularJS vs Next.js),

DOM Contract stability.

✔️ Puppeteer

Used when only Chromium behavior is needed.

✔️ Lighthouse CI

Used to measure performance migration success.

7. BehaviorGuard for UI

Feniks evaluates the transformation:

Inputs:

UiTemplateView (HTML/CSS)

AngularJS AST

React/Next.js code

Playwright snapshots

Feniks checks:

required DOM nodes exist,

text labels exist,

buttons/functions still work,

lists still render,

flows remain valid,

critical business interactions survive.

Feniks outputs:

behavior_report.json

ui_diff.html

risk_score.json

This is the core guarantee of safe refactoring.

8. LLM Integration (Claude/Gemini)

LLMs handle:

✔ UI transformations:

complex JSX restructuring,

component decomposition,

naming logic,

CSS normalization.

✔ Structural changes:

rewriting AngularJS expressions (| filter, | orderBy),

migrating $scope → React state.

Feniks provides:

context,

template metadata,

architectural guidance,

validation.

LLMs follow BehaviorContracts to avoid regressions.

9. RAE Memory (Optional Integration)

RAE stores:

migration decisions,

UI template mappings,

DOM contracts,

regressions found,

fixed issues,

architectural history.

After each iteration, Feniks sends:

BehaviorReports,

CodeSnapshots,

UIBindings,

MigrationSteps.

This allows:

multi-day, multi-agent safe refactor,

continuous long-term improvement,

reproducible reasoning over large codebases.

10. Migration Roadmap (Recommended)

Below is the suggested migration pipeline for a legacy AngularJS frontend.

Step 1 — Template Capture

feniks ui scan-templates

Step 2 — UI Template Curation

Add business roles, identify critical flows.

Step 3 — AngularJS Structural Scan

Run ngMigrationAssistant.

Step 4 — Build UiTemplateView → DOM Contracts

Feniks generates golden UI contracts.

Step 5 — First-Pass Codemods

jscodeshift + babel → JSX skeletons.

Step 6 — Componentization

Extract logic → hooks/services/components.

Step 7 — Behavior Evaluation

Playwright snapshots → BehaviorContracts.

Step 8 — Performance and UX Validation

Lighthouse CI.

Step 9 — Iteration and RAE Memory

Long-term refinement with multi-agent assist.

11. Summary

Feniks leverages the strongest open-source ecosystem for JavaScript/TypeScript:

jscodeshift – transformations

Babel – JSX conversion

Recast – stable formatting

TS-Morph – advanced TS refactor

ngMigrationAssistant – AngularJS insight

Playwright – behavioral validation

ESLint/Prettier – hygiene layer

On top of these, Feniks adds:

UiTemplateView interpretation,

BehaviorGuard,

risk modeling,

tool orchestration,

RAE knowledge,

LLM-driven reasoning,

multi-iteration supervision.

This combination gives you a complete, industrial-grade migration engine from AngularJS → React/Next.js.