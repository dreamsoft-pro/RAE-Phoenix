# Reflection and Meta-Reflection in RAE-Feniks

## Introduction

**Meta-reflection** is the ability of a system to observe, analyze, and reason about itself. In RAE-Feniks, meta-reflection enables:
- Self-awareness of code quality and architecture
- Learning from past refactorings
- Building institutional knowledge
- Enabling self-improving systems

This document explains how meta-reflection works in RAE-Feniks and how to leverage it for better code analysis.

## Levels of Reflection

### Level 1: Static Analysis (Traditional)
Traditional static analysis tools:
- Parse code to extract syntax
- Check for style violations
- Report metrics (complexity, LOC, etc.)
- **Limitation**: No context, no learning, no reasoning

### Level 2: Local Meta-Reflection (RAE-Feniks)
RAE-Feniks generates **local meta-reflections** per code chunk:
- Analyzes complexity in system context
- Identifies design patterns
- Detects technical debt
- Suggests refactoring opportunities
- **Benefit**: Contextual, actionable insights

### Level 3: Global Meta-Reflection (RAE Integration)
With RAE integration, Feniks gains:
- Self-model awareness
- Historical memory
- Cross-project learning
- Reasoning about architectural decisions
- **Benefit**: Self-aware, continuously improving

## How Meta-Reflection Works

### 1. Code Ingestion

Code chunks are ingested with rich metadata:

```json
{
  "file_path": "src/services/auth.service.ts",
  "start_line": 15,
  "end_line": 89,
  "content": "class AuthService { ... }",
  "type": "class",
  "language": "typescript",
  "metadata": {
    "imports": ["jwt", "bcrypt", "database"],
    "exports": ["AuthService"],
    "complexity": 12,
    "dependencies": ["UserRepository", "TokenService"]
  }
}
```

### 2. System Model Construction

Chunks are aggregated into a **system model**:

```
System Model
├── Modules
│   ├── auth (8 chunks)
│   ├── api (15 chunks)
│   └── ui (42 chunks)
├── Dependencies
│   ├── auth → database
│   ├── api → auth
│   └── ui → api
├── Capabilities
│   ├── authentication
│   ├── REST API
│   └── UI components
└── Metrics
    ├── Avg complexity: 4.5
    ├── Total modules: 45
    └── Dependency depth: 3
```

### 3. Capability Detection

RAE-Feniks automatically detects high-level capabilities:

| Capability | Detection Criteria |
|------------|-------------------|
| Authentication | Keywords: login, token, jwt, auth, session |
| API | Keywords: endpoint, route, controller, REST |
| Database | Keywords: query, repository, schema, ORM |
| UI Components | File patterns: *.component.*, JSX, templates |
| Testing | File patterns: *.test.*, *.spec.* |

### 4. Local Meta-Reflection Generation

For each chunk, RAE-Feniks generates meta-reflections:

```json
{
  "chunk_id": "auth.service.ts:15-89",
  "reflection_type": "complexity",
  "content": "AuthService has cyclomatic complexity of 12, which is 2.67x the system average of 4.5. The login() method accounts for 60% of this complexity. Consider extracting token validation into a separate method.",
  "severity": "medium",
  "tags": ["complexity", "refactoring-opportunity", "extract-function"],
  "timestamp": "2025-11-26T10:30:00Z",
  "context": {
    "module": "auth",
    "system_avg_complexity": 4.5,
    "chunk_complexity": 12,
    "ratio": 2.67
  }
}
```

### 5. RAE Integration (Optional)

When RAE integration is enabled:

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Feniks    │───────▶│     RAE     │───────▶│ Self-Model  │
│  Analysis   │ query   │  Reasoning  │ update  │   Memory    │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │                       │
       │                       │                       │
       ▼                       ▼                       ▼
 Local Reflections     Global Insights      Historical Learning
```

RAE can:
- Query the self-model for architectural context
- Reason about refactoring trade-offs
- Learn from past refactoring outcomes
- Store lessons learned in memory

## Types of Meta-Reflections

### 1. Complexity Reflections

Identify high-complexity code that needs refactoring:

```json
{
  "reflection_type": "complexity",
  "content": "Function processPayment() has 15 branches and 89 lines. Consider breaking it down using the Strategy pattern.",
  "severity": "high",
  "tags": ["complexity", "strategy-pattern"]
}
```

### 2. Dependency Reflections

Detect dependency issues:

```json
{
  "reflection_type": "dependency",
  "content": "Module 'auth' has bidirectional dependency with 'user'. This creates tight coupling and circular dependency risk.",
  "severity": "high",
  "tags": ["coupling", "architecture", "circular-dependency"]
}
```

### 3. Design Pattern Reflections

Identify patterns and anti-patterns:

```json
{
  "reflection_type": "pattern",
  "content": "Detected Observer pattern in EventEmitter class. Well-structured implementation with proper subscription management.",
  "severity": "info",
  "tags": ["observer-pattern", "good-practice"]
}
```

### 4. Technical Debt Reflections

Flag technical debt:

```json
{
  "reflection_type": "tech-debt",
  "content": "Legacy error handling using callbacks instead of Promises. This makes error propagation difficult and code harder to test.",
  "severity": "medium",
  "tags": ["tech-debt", "callback-hell", "modernization"]
}
```

### 5. Hotspot Reflections

Identify high-change areas:

```json
{
  "reflection_type": "hotspot",
  "content": "This module has been changed 47 times in the past 3 months. High churn suggests unclear requirements or design issues.",
  "severity": "medium",
  "tags": ["hotspot", "churn", "requirements"]
}
```

## Severity Levels

| Severity | Meaning | Action |
|----------|---------|--------|
| `critical` | System-breaking issue | Fix immediately |
| `high` | Major problem | Prioritize for next sprint |
| `medium` | Important but not urgent | Plan refactoring |
| `low` | Minor improvement | Consider when time permits |
| `info` | Informational | No action needed |

## Using Meta-Reflections

### Query by Severity

```bash
cat meta_reflections.jsonl | jq 'select(.severity == "high")'
```

### Query by Tag

```bash
cat meta_reflections.jsonl | jq 'select(.tags | contains(["refactoring-opportunity"]))'
```

### Query by Module

```bash
cat meta_reflections.jsonl | jq 'select(.context.module == "auth")'
```

### Count Reflections by Type

```bash
cat meta_reflections.jsonl | jq -r '.reflection_type' | sort | uniq -c
```

Example output:
```
 42 complexity
 23 dependency
 18 tech-debt
 12 pattern
  8 hotspot
```

## RAE Integration Example

When RAE is enabled:

```python
# RAE queries Feniks for self-awareness
response = rae_client.query(
    "What are my most complex modules that would benefit from refactoring?"
)

# RAE reasons using self-model + meta-reflections
print(response.answer)
# "Based on your code analysis, the top 3 modules are:
#  1. auth.service.ts (complexity 12, 2.67x avg) - Extract token logic
#  2. data-processor.ts (complexity 11, 2.44x avg) - Apply Strategy pattern
#  3. api.controller.ts (complexity 10, 2.22x avg) - Split into smaller controllers"
```

### RAE Learning from Refactorings

```python
# After refactoring, Feniks sends outcome to RAE
refactoring_outcome = {
    "recipe": "reduce_complexity",
    "modules_affected": ["auth.service.ts"],
    "complexity_before": 12,
    "complexity_after": 6,
    "success": True,
    "lesson_learned": "Extracting token validation reduced complexity by 50% without breaking tests"
}

rae_client.record_memory(refactoring_outcome)
```

Next time RAE sees similar complexity, it can suggest the same approach.

## Best Practices

### 1. Regular Analysis
Run analysis after significant changes:
```bash
# After feature development
feniks analyze --project-id my_project --collection my_project

# Review new reflections
cat meta_reflections.jsonl | jq 'select(.timestamp > "2025-11-26T00:00:00Z")'
```

### 2. Prioritize by Severity
Focus on high/critical issues first:
```bash
cat meta_reflections.jsonl | jq 'select(.severity == "high" or .severity == "critical")'
```

### 3. Track Trends
Monitor reflection counts over time:
```bash
# Week 1
feniks analyze --meta-reflections week1_reflections.jsonl
cat week1_reflections.jsonl | wc -l
# 342 reflections

# Week 2 (after refactoring)
feniks analyze --meta-reflections week2_reflections.jsonl
cat week2_reflections.jsonl | wc -l
# 289 reflections (-53, improvement!)
```

### 4. Use Tags for Planning
Group related refactorings:
```bash
# Find all extract-function opportunities
cat meta_reflections.jsonl | jq 'select(.tags | contains(["extract-function"]))' > extract_function_todos.jsonl

# Find all circular dependencies
cat meta_reflections.jsonl | jq 'select(.tags | contains(["circular-dependency"]))' > circular_deps.jsonl
```

### 5. Integrate with CI/CD
Add analysis to your CI pipeline:
```yaml
# .github/workflows/analysis.yml
- name: Run Feniks Analysis
  run: |
    feniks analyze --project-id ${{ github.repository }} --meta-reflections reflections.jsonl

- name: Check for Critical Issues
  run: |
    CRITICAL_COUNT=$(cat reflections.jsonl | jq 'select(.severity == "critical")' | wc -l)
    if [ $CRITICAL_COUNT -gt 0 ]; then
      echo "Found $CRITICAL_COUNT critical issues!"
      exit 1
    fi
```

## Advanced: Custom Meta-Reflection

You can extend RAE-Feniks to generate custom meta-reflections:

```python
from feniks.core.analysis_pipeline import AnalysisPipeline
from feniks.types import Chunk

class CustomCapabilityDetector:
    def detect_security_issues(self, chunks: List[Chunk]) -> List[dict]:
        reflections = []

        for chunk in chunks:
            # Custom detection logic
            if "eval(" in chunk.content and chunk.language == "javascript":
                reflections.append({
                    "chunk_id": f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}",
                    "reflection_type": "security",
                    "content": f"Use of eval() detected in {chunk.file_path}. This is a security risk.",
                    "severity": "critical",
                    "tags": ["security", "eval", "code-injection"]
                })

        return reflections
```

## Summary

Meta-reflection in RAE-Feniks:
- **Provides context** beyond simple metrics
- **Identifies opportunities** for improvement
- **Learns from outcomes** when integrated with RAE
- **Enables self-awareness** for AI agents
- **Guides refactoring** with actionable insights

By combining local meta-reflections with RAE's global reasoning, you create a system that truly understands itself and can continuously improve.

## Next Steps

- Learn about [Enterprise Refactoring workflows](./ENTERPRISE_REFACTORING.md)
- Integrate with [RAE for self-aware agents](./RAE_INTEGRATION.md)
- Explore [custom recipe development](./ENTERPRISE_REFACTORING.md#custom-recipes)
