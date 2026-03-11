# docs/PHP__tools_enterprise-grade.md

Dokument obejmuje cały zestaw narzędzi klasy enterprise dla PHP, ze szczególnym naciskiem na:

Twój aktualny backend (PHP 8.1.2, MySQL/MariaDB),

moduły produkcji/kalkulacji/ofertowania/e-commerce,

refaktoryzację legacy code,

analizę bezpieczeństwa i stabilności,

integrację z Feniksem i BehaviorGuard,

automatyczne modernizacje przez Rector,

pełną ścieżkę modernizacji dużego systemu bez testów.

Jest to gotowy plik do repo – strukturalnie i jakościowo zgodny z OSS.

📄 docs/PHP__tools_enterprise-grade.md
Enterprise-Grade PHP Tooling for Refactoring, Modernization & Quality Control

Feniks Integration Guide for Large Legacy PHP Backends

This document describes the enterprise-grade PHP toolchain used by Feniks to modernize, refactor and stabilize large PHP codebases – including legacy systems without tests, procedural modules, mixed frameworks, and business-critical backend services.

Feniks does not reimplement refactoring tools.
Instead, it provides a meta-layer of behavior analysis, risk scoring, AST validation, and iterative modernization planning, while relying on mature OSS tools such as:

Rector – automated refactoring engine

PHPStan / Psalm – static analysis

PHP-CS-Fixer – code consistency

PHP_CodeSniffer – style + rules

Deptrac – architectural boundaries

Phan / PHPCompatibility – version compatibility

Pest / PHPUnit – tests (optional)

Feniks can coordinate these tools and evaluate results using:

BehaviorContracts

SystemModel graphs

Risk scoring

Snapshot diffs

Architecture invariants

This enables safe modernization even for systems without tests, such as:

production management backend,

complex product calculators,

e-commerce logic,

order configuration engines,

CRM modules,

pricing engines.

1. Architecture Overview
[ Legacy PHP Code ]
        │
        ▼
[ OSS Tools Layer ]
  - Rector
  - PHPStan / Psalm
  - PHP-CS-Fixer
  - PHP_CodeSniffer
  - Deptrac
        │
        ▼
[ Feniks Analysis Layer ]
  - AST integrity
  - SystemModel.PhpModuleGraph
  - BehaviorContracts
  - UI/HTTP flow contracts
        │
        ▼
[ Refactoring Plan + Risk Score ]
        │
        ▼
[ LLM Executors (optional) ]
        │
        ▼
[ RAE Memory (optional) ]


Feniks directs tools.
Tools perform refactors.
Feniks verifies results, evaluates behavior, and produces human-readable reports.

2. Rector – the Core of Enterprise PHP Modernization

Rector is the most powerful automated refactor engine for PHP.

Feniks uses Rector for:

2.1. Language Upgrades

PHP 5.x → 7.x → 8.x

Add strict types

Modernize functions, syntax, constructs

Convert array() → []

Replace deprecated features

2.2. Framework Upgrades

Symfony migrations

Doctrine improvements

Laravel modernization

(If applicable in the future.)

2.3. Domain Logic Modernization

Introduce return types

Introduce parameter types

Extract classes and DTOs

Replace procedural structures

Remove dead code

Inline variables / simplify control flow

2.4. Automated Safety Rules

Feniks integrates Rector with behavior rules:

avoid breaking contracts,

detect signature drift,

detect changed method visibility,

detect removed side effects,

validate SQL changes.

Rector becomes the foundation of PHP modernization.
3. PHPStan and Psalm – Deep Static Analysis

Feniks integrates both engines, because they complement each other.

✔ PHPStan – practical, fast, widely adopted
✔ Psalm – more strict, deeper type inference

Feniks uses them for:

function signature mismatch detection,

wrong return type detection,

risky nullability,

incorrect SQL parameter usage,

code paths that may break behavior,

unreachable code detection,

data flow tracing in calculators / configurators.

Outputs:

phpstan.json

psalm.json

combined static_analysis_summary.json

These results feed into the BehaviorRiskModel inside Feniks.

4. PHP-CS-Fixer & CodeSniffer – Code Hygiene and Consistency

Clean code massively improves safety during refactor.

Feniks orchestrates:

4.1. PHP-CS-Fixer

Applies rules for:

whitespace,

naming conventions,

import ordering,

array syntax,

docblocks,

strict comparisons.

4.2. PHP_CodeSniffer (PHPCS)

Enforces rulesets such as:

PSR-1, PSR-12,

custom rules (Forbidden functions, no globals, etc.),

architectural constraints.

Feniks uses both tools before AST-based refactors to ensure code stability.

5. Deptrac – Architecture Analysis & Boundary Protection

In large systems, key modules include:

calculators,

pricing engines,

production workflow logic,

e-commerce logic,

data models.

Deptrac allows Feniks to:

detect dependency cycles,

enforce architectural layers,

prevent domain logic from leaking into controllers,

maintain clear module boundaries.

Feniks produces:

architecture_report.json

layer_violations.json

These feed into SystemModel graphs.

6. PHPCompatibility / Phan – Version Compatibility

Useful for:

server migrations,

Dockerized production (like yours),

Kubernetes deployments.

Feniks integrates these tools to ensure:

no deprecated API usage,

compatibility with PHP 8.x,

safe use of new features like enums/readonly.

7. Testing Layers (Optional but Supported)

Feniks supports:

✔ PHPUnit

Traditional testing.

✔ Pest

Modern syntax + snapshot testing.

✔ HTTP snapshot tests

For behavior comparison of:

APIs,

calculators,

pricing endpoints,

order logic.

Feniks can auto-generate snapshot tests from real requests.

8. Database Integration (MySQL/MariaDB)

Feniks’s PHP integration supports:

SQL query extraction,

parameter analysis,

prepared statements enforcement,

detection of dangerous patterns:

string concatenation in queries,

unescaped variables,

risky joins,

inconsistent transaction handling.

Feniks combines:

PHPStan/Psalm SQL plugins,

regex detection,

semantic heuristics,

SystemModel.DatabaseGraph.

This is critical for:

production planning modules,

pricing modules,

frontend e-commerce endpoints.

9. Behavior Contracts for PHP

Feniks generates several kinds of contracts:

9.1. Output Contracts

For functions like:

pricing calculators,

PDF generators,

configuration engines,

business logic methods.

9.2. HTTP Contracts

For controllers/APIs:

status codes,

schema of JSON responses,

mandatory fields,

SQL side effects.

9.3. Safety Contracts

For:

SQL injection protection,

input validation,

permission checks,

filesystem operations.

9.4. Risk Contracts

Evaluate:

complexity,

volatility,

impact on money-related logic,

cross-module coupling.

These contracts guide every refactor iteration.

10. LLM-Assisted Refactoring (Claude / Gemini)

Feniks uses LLMs for:

decomposing large files,

suggesting architecture improvements,

transforming procedural code into classes,

renaming functions,

generating DTOs, interfaces, type hints,

discovering hidden business rules.

LLMs never apply changes directly.

Feniks:

validates suggestions with BehaviorContracts,

integrates codemods automatically,

provides architectural constraints,

stores iteration history in RAE.

11. Recommended PHP Modernization Pipeline
1. Code Hygiene Pass
   - PHP-CS-Fixer
   - PHPCS
   - Dead code elimination
----------------------------------------
2. Static Analysis
   - PHPStan (level 6+)
   - Psalm
   - SQL analyzers
----------------------------------------
3. Architecture Scan
   - Deptrac
   - SystemModel graphs
----------------------------------------
4. Rector Automated Refactors
   - language upgrades
   - type inference
   - class extraction
   - method cleanup
----------------------------------------
5. BehaviorGuard
   - snapshot-based comparisons
   - HTTP/JSON contract checks
   - SQL execution plan monitoring
----------------------------------------
6. LLM Assisted Improvements
   - logic decomposition
   - architecture suggestions
   - DTO/VO introduction
----------------------------------------
7. Iteration & RAE Memory
   - store reports
   - plan next refactor phase
   - evolve contracts


This pipeline is safe for legacy production-critical systems, including those running 24/7 in Docker/Kubernetes.

12. Summary

Enterprise-grade PHP support in Feniks integrates:

Layer	Tools
Automated refactor	Rector
Static analysis	PHPStan, Psalm
Code style	PHP-CS-Fixer, PHPCS
Architecture	Deptrac
Compatibility	PHPCompatibility, Phan
Testing	PHPUnit, Pest, snapshots
Security	SQL analyzers, prepared statement enforcement
UI/API behavior	HTTP contracts, BehaviorGuard

Feniks adds on top:

architectural supervision,

behavioral invariants,

safe refactoring cycles,

risk scoring,

optional long-term memory (RAE),

LLM orchestration.

This combination enables safe modernization and long-term sustainability of large PHP systems — even without tests.