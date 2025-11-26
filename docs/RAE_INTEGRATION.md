# RAE Integration - Building Self-Aware Agents

## Introduction

**RAE (Reflective Agent Engine)** integration enables RAE-Feniks to power self-aware, self-improving AI agents. By connecting Feniks's code analysis capabilities with RAE's reasoning and memory systems, we create agents that:

- **Understand their own code** through system models and meta-reflections
- **Reason about improvements** using self-model queries
- **Learn from refactorings** by storing outcomes in memory
- **Propose informed changes** based on architectural context

This document explains how to integrate RAE-Feniks with RAE.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          RAE Agent                          │
│  (Reasoning Engine + Memory + Self-Model)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   RAE API         │
                    │  (REST/WebSocket) │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│ Self-Model   │    │   Memory     │      │  Reasoning   │
│   Query      │    │   Storage    │      │   Context    │
└──────────────┘    └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
        ┌──────────────────────────────────────────┐
        │           RAE-Feniks Integration         │
        │  (Analysis → Self-Model → Memory)        │
        └──────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│  Analysis    │    │   System     │      │    Meta-     │
│  Pipeline    │    │   Model      │      │  Reflection  │
└──────────────┘    └──────────────┘      └──────────────┘
```

## Configuration

### 1. Enable RAE Integration

Edit `.env`:

```bash
# RAE Integration
RAE_ENABLED=true
RAE_BASE_URL=http://localhost:8000
RAE_API_KEY=your_rae_api_key_here
RAE_TIMEOUT=30
```

### 2. Verify Configuration

```bash
feniks --version
```

Output should show:
```
RAE Integration: enabled
RAE URL: http://localhost:8000
```

## Integration Points

### 1. System Model → Self-Model

After analysis, Feniks uploads the system model to RAE's self-model:

```python
# feniks/integration/rae_client.py

class RAEClient:
    def upload_system_model(self, system_model: SystemModel):
        """Upload system model to RAE self-model."""
        payload = {
            "project_id": system_model.project_id,
            "modules": [
                {
                    "name": m.name,
                    "file_paths": m.file_paths,
                    "complexity": m.avg_complexity,
                    "dependencies": m.dependencies,
                    "capabilities": m.capabilities
                }
                for m in system_model.modules.values()
            ],
            "dependencies": [
                {"from": d.from_module, "to": d.to_module, "type": d.import_type}
                for d in system_model.dependencies
            ],
            "capabilities": list(system_model.capabilities),
            "metrics": {
                "total_modules": system_model.total_modules,
                "avg_complexity": system_model.avg_complexity,
                "dependency_depth": system_model.dependency_depth
            }
        }

        response = self.session.post(
            f"{self.base_url}/api/self-model/update",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

        response.raise_for_status()
        return response.json()
```

### 2. Meta-Reflections → Memory

Meta-reflections are stored in RAE's memory for future reasoning:

```python
def upload_meta_reflections(self, reflections: List[dict]):
    """Upload meta-reflections to RAE memory."""
    for reflection in reflections:
        memory_entry = {
            "type": "meta_reflection",
            "content": reflection["content"],
            "metadata": {
                "chunk_id": reflection["chunk_id"],
                "reflection_type": reflection["reflection_type"],
                "severity": reflection["severity"],
                "tags": reflection["tags"],
                "context": reflection.get("context", {})
            },
            "timestamp": reflection["timestamp"]
        }

        self.session.post(
            f"{self.base_url}/api/memory/store",
            json=memory_entry,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
```

### 3. Refactoring Outcomes → Learning

After refactoring, outcomes are recorded for learning:

```python
def record_refactoring_outcome(self, outcome: dict):
    """Record refactoring outcome for learning."""
    learning_entry = {
        "type": "refactoring_outcome",
        "recipe": outcome["recipe"],
        "success": outcome["success"],
        "impact": {
            "modules_affected": outcome["modules_affected"],
            "complexity_before": outcome.get("complexity_before"),
            "complexity_after": outcome.get("complexity_after"),
            "tests_passed": outcome.get("tests_passed", True)
        },
        "lesson_learned": outcome["lesson_learned"],
        "timestamp": outcome["timestamp"]
    }

    self.session.post(
        f"{self.base_url}/api/memory/store",
        json=learning_entry,
        headers={"Authorization": f"Bearer {self.api_key}"}
    )
```

## Use Cases

### Use Case 1: Self-Aware Code Review

An RAE agent reviewing code can query its self-model:

```python
# RAE agent code
def review_pull_request(pr_files: List[str]):
    # Query self-model for context
    context = rae_client.query_self_model(
        "What modules are affected by changes to auth.service.ts?"
    )

    # Response from RAE
    print(context)
    # {
    #   "affected_modules": ["auth", "api", "user"],
    #   "dependencies": ["api depends on auth", "user depends on auth"],
    #   "risks": ["Changes to auth may break API authentication"],
    #   "test_suggestions": ["Test auth.service.ts", "Test api integration"]
    # }

    # Review with full context
    for file in pr_files:
        if file in context["affected_modules"]:
            review_with_context(file, context)
```

### Use Case 2: Intelligent Refactoring Suggestions

RAE can suggest refactorings based on system understanding:

```python
# RAE agent code
def suggest_refactorings(project_id: str):
    # Query meta-reflections from memory
    reflections = rae_client.query_memory(
        query="Find high-complexity modules with refactoring opportunities",
        filters={"project_id": project_id, "type": "meta_reflection"}
    )

    # Reason about priorities
    for reflection in reflections:
        if reflection["severity"] == "high":
            # Check if similar refactoring succeeded before
            past_outcomes = rae_client.query_memory(
                query=f"Find past refactorings of {reflection['context']['module']}",
                filters={"type": "refactoring_outcome"}
            )

            if past_outcomes and all(o["success"] for o in past_outcomes):
                print(f"✓ High confidence: {reflection['content']}")
                print(f"  Past success: {len(past_outcomes)} similar refactorings")
            else:
                print(f"⚠ Uncertain: {reflection['content']}")
                print(f"  Recommend manual review")
```

### Use Case 3: Continuous Learning

RAE learns from refactoring outcomes:

```python
# After refactoring
outcome = {
    "recipe": "reduce_complexity",
    "modules_affected": ["auth.service.ts"],
    "complexity_before": 12,
    "complexity_after": 6,
    "success": True,
    "tests_passed": True,
    "lesson_learned": "Extracting token validation into separate method reduced complexity by 50% without breaking tests. This pattern works well for authentication logic.",
    "timestamp": datetime.now().isoformat()
}

rae_client.record_refactoring_outcome(outcome)

# Later, when encountering similar complexity
similar_module = "payment.service.ts"  # Also has high complexity
past_lessons = rae_client.query_memory(
    query="Find successful complexity reductions",
    filters={"type": "refactoring_outcome", "recipe": "reduce_complexity"}
)

# RAE suggests: "Based on auth.service.ts refactoring, consider extracting validation logic"
```

### Use Case 4: Architectural Decision Support

RAE helps make informed architectural decisions:

```python
# Developer asks: "Should I split the auth module into separate services?"
def answer_architectural_question(question: str):
    # Query self-model
    auth_module = rae_client.query_self_model("Describe auth module")

    # Response includes:
    # - Current complexity: 12 (high)
    # - Dependencies: 8 modules depend on auth
    # - Capabilities: authentication, token management, session handling

    # Query memory for similar decisions
    past_decisions = rae_client.query_memory(
        query="Find past module splitting decisions",
        filters={"type": "refactoring_outcome", "tags": ["split-module"]}
    )

    # Reason about trade-offs
    reasoning = rae_client.reason({
        "question": question,
        "context": {
            "module": auth_module,
            "past_decisions": past_decisions
        }
    })

    print(reasoning["answer"])
    # "Yes, splitting auth module is recommended because:
    #  1. High complexity (12) suggests multiple responsibilities
    #  2. Three distinct capabilities (auth, tokens, sessions)
    #  3. Past split of 'api' module succeeded with similar metrics
    #  4. Risk is manageable with proper interface design
    #
    #  Suggested split:
    #  - AuthService (authentication only)
    #  - TokenService (token management)
    #  - SessionService (session handling)"
```

## API Reference

### RAEClient Methods

#### `upload_system_model(system_model: SystemModel) -> dict`
Upload system model to RAE's self-model.

**Returns**: Confirmation with self-model ID

#### `upload_meta_reflections(reflections: List[dict]) -> dict`
Upload meta-reflections to RAE's memory.

**Returns**: Confirmation with memory entry IDs

#### `record_refactoring_outcome(outcome: dict) -> dict`
Record refactoring outcome for learning.

**Returns**: Confirmation with learning entry ID

#### `query_self_model(query: str) -> dict`
Query RAE's self-model for architectural context.

**Example**:
```python
response = client.query_self_model("What modules depend on auth?")
# Returns: {"dependencies": ["api", "user", "admin"], ...}
```

#### `query_memory(query: str, filters: dict) -> List[dict]`
Query RAE's memory for past reflections, refactorings, etc.

**Example**:
```python
results = client.query_memory(
    query="Find high-complexity modules",
    filters={"type": "meta_reflection", "severity": "high"}
)
```

#### `reason(context: dict) -> dict`
Ask RAE to reason about a question with given context.

**Example**:
```python
answer = client.reason({
    "question": "Should I refactor this module?",
    "context": {"module": "auth", "complexity": 12}
})
# Returns: {"answer": "Yes, because...", "confidence": 0.85}
```

## Running with RAE Integration

### 1. Start RAE Server

```bash
# Start RAE (see RAE documentation)
rae-server --port 8000
```

### 2. Run Analysis with RAE

```bash
feniks analyze \
  --project-id my_project \
  --collection my_project \
  --rae-enabled true \
  --output analysis_report.txt \
  --meta-reflections meta_reflections.jsonl
```

With RAE enabled, analysis also:
- Uploads system model to RAE self-model
- Uploads meta-reflections to RAE memory
- Queries RAE for additional insights

### 3. Check RAE Self-Model

```bash
curl -H "Authorization: Bearer $RAE_API_KEY" \
  http://localhost:8000/api/self-model/get?project_id=my_project
```

Response:
```json
{
  "project_id": "my_project",
  "modules": [...],
  "dependencies": [...],
  "capabilities": [...],
  "last_updated": "2025-11-26T10:30:00Z"
}
```

## Example: Complete Workflow

```python
#!/usr/bin/env python3
"""
Example: RAE-powered code analysis and refactoring
"""

from feniks.core.analysis_pipeline import run_analysis
from feniks.refactor.refactor_engine import RefactorEngine
from feniks.integration.rae_client import RAEClient

# 1. Run analysis with RAE integration
print("Step 1: Analyzing code...")
system_model = run_analysis(
    project_id="my_project",
    collection_name="my_project",
    output_path="analysis_report.txt",
    meta_reflections_output="meta_reflections.jsonl"
)

# 2. Query RAE for refactoring suggestions
print("Step 2: Querying RAE for suggestions...")
rae = RAEClient()

suggestions = rae.reason({
    "question": "What refactorings should I prioritize?",
    "context": {
        "system_model": system_model.to_dict(),
        "meta_reflections": "meta_reflections.jsonl"
    }
})

print(f"RAE suggests: {suggestions['answer']}")
# "Prioritize reducing complexity in auth.service.ts (12 → 6) because:
#  1. It's 2.67x the system average
#  2. Past refactorings of similar complexity succeeded
#  3. 8 modules depend on it, so improvements have high impact"

# 3. Execute suggested refactoring
print("Step 3: Executing refactoring...")
engine = RefactorEngine()

result = engine.run_workflow(
    recipe_name="reduce_complexity",
    system_model=system_model,
    chunks=load_chunks(),
    target={"module_name": "auth"},
    dry_run=True,
    output_dir="refactor_output"
)

print(f"Refactoring: {'✓ Success' if result.success else '✗ Failed'}")
print(f"Patch: {result.patch_path}")

# 4. Record outcome in RAE memory
print("Step 4: Recording outcome...")
outcome = {
    "recipe": "reduce_complexity",
    "modules_affected": ["auth.service.ts"],
    "complexity_before": 12,
    "complexity_after": 6,
    "success": result.success,
    "tests_passed": True,
    "lesson_learned": result.meta_reflection["lessons_learned"],
    "timestamp": datetime.now().isoformat()
}

rae.record_refactoring_outcome(outcome)
print("✓ Outcome recorded in RAE memory")

# 5. Query RAE for lessons learned
print("Step 5: Querying lessons learned...")
lessons = rae.query_memory(
    query="What have we learned about complexity reduction?",
    filters={"type": "refactoring_outcome", "recipe": "reduce_complexity"}
)

for lesson in lessons:
    print(f"- {lesson['lesson_learned']}")
```

## Benefits of RAE Integration

### 1. Self-Awareness
Agents understand their own architecture, dependencies, and technical debt.

### 2. Contextual Reasoning
Decisions are informed by system context, not just local code patterns.

### 3. Continuous Learning
Past refactorings inform future suggestions, improving over time.

### 4. Confidence Scoring
RAE provides confidence scores based on past success rates.

### 5. Architectural Intelligence
Agents can reason about system-wide impacts of changes.

## Advanced: Custom RAE Queries

You can create custom queries for specific use cases:

```python
class CustomRAEQueries:
    def __init__(self, rae_client: RAEClient):
        self.rae = rae_client

    def find_blast_radius(self, module_name: str) -> dict:
        """Find all modules affected by changes to a given module."""
        return self.rae.query_self_model(
            f"What modules depend directly or indirectly on {module_name}?"
        )

    def suggest_test_strategy(self, changed_files: List[str]) -> dict:
        """Suggest testing strategy for changed files."""
        return self.rae.reason({
            "question": "What tests should I run for these changes?",
            "context": {
                "changed_files": changed_files,
                "self_model": "query"
            }
        })

    def estimate_refactoring_risk(self, recipe: str, target: str) -> dict:
        """Estimate risk of refactoring based on past outcomes."""
        past_outcomes = self.rae.query_memory(
            query=f"Find past {recipe} refactorings",
            filters={"type": "refactoring_outcome", "recipe": recipe}
        )

        success_rate = sum(1 for o in past_outcomes if o["success"]) / len(past_outcomes)

        return {
            "recipe": recipe,
            "target": target,
            "estimated_success_rate": success_rate,
            "risk_level": "LOW" if success_rate > 0.9 else "MEDIUM" if success_rate > 0.7 else "HIGH"
        }
```

## Security Considerations

### Authentication
Always use API keys for RAE communication:

```bash
RAE_API_KEY=your_secret_key_here
```

Never commit API keys to version control.

### Data Privacy
Be mindful of what data is sent to RAE:
- System models contain architectural information
- Meta-reflections may include code snippets
- Ensure RAE server has appropriate access controls

### Network Security
Use HTTPS for production:

```bash
RAE_BASE_URL=https://rae.example.com
```

## Troubleshooting

### RAE Connection Failed

**Error**: `Failed to connect to RAE at http://localhost:8000`

**Solutions**:
1. Ensure RAE server is running: `rae-server --port 8000`
2. Check firewall settings
3. Verify `RAE_BASE_URL` in `.env`

### Authentication Failed

**Error**: `RAE API authentication failed`

**Solutions**:
1. Check `RAE_API_KEY` in `.env`
2. Verify API key is valid: `curl -H "Authorization: Bearer $RAE_API_KEY" http://localhost:8000/api/health`
3. Regenerate API key if needed

### Upload Failed

**Error**: `Failed to upload system model to RAE`

**Solutions**:
1. Check RAE server logs for errors
2. Verify system model format
3. Ensure sufficient RAE storage capacity

## Summary

RAE integration transforms RAE-Feniks from a static analysis tool into a foundation for self-aware, continuously improving systems.

Key capabilities:
- ✅ Self-model awareness
- ✅ Historical memory
- ✅ Learning from outcomes
- ✅ Contextual reasoning
- ✅ Confidence scoring

With RAE integration, you enable agents that truly understand and improve themselves.

## Next Steps

- Review [Getting Started](./GETTING_STARTED.md) for setup
- Explore [Meta-Reflection concepts](./REFLECTION_AND_META_REFLECTION.md)
- Master [Enterprise Refactoring](./ENTERPRISE_REFACTORING.md)
- Check the [examples/](../examples/) directory for complete workflows
