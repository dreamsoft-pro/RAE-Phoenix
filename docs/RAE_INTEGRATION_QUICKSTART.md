# RAE Integration - Quick Start Guide

This guide helps you quickly start using the RAE (Reflective Agentic Engine) integration in Feniks for synergistic memory management and cross-project learning.

## 📋 Overview

The RAE integration provides:

- **Bidirectional Sync**: Read and write operations with RAE global memory
- **Intelligent Routing**: Dual-memory strategy (local Qdrant + global RAE)
- **Reflection Enrichment**: Enhance local insights with global knowledge
- **Cross-Project Learning**: Learn from patterns across all projects
- **Feedback Loops**: Refactoring outcomes improve future recommendations

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites

```bash
# RAE API running
curl http://localhost:8000/health

# Qdrant running (Feniks default)
# Python environment with Feniks dependencies
```

### 2. Configure Environment

Add to your `.env` file:

```bash
# RAE Integration
RAE_ENABLED=true
RAE_BASE_URL=http://localhost:8000
RAE_API_KEY=your-rae-api-key-here
RAE_TENANT_ID=your-tenant-id
RAE_TIMEOUT=30
```

### 3. Run the Example

```bash
# From Feniks root directory
python examples/rae_integration_example.py
```

This demonstrates:
- ✓ Intelligent storage routing
- ✓ Reflection enrichment
- ✓ Cross-project patterns
- ✓ Refactoring feedback loops
- ✓ Hybrid search strategies

## 📚 Core Components

### Enhanced RAE Client

Extends the base RAE client with bidirectional capabilities:

```python
from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client

# Initialize
rae_client = create_enhanced_rae_client()

# Query historical reflections
results = rae_client.query_reflections(
    project_id="my-project",
    query_text="authentication patterns",
    layer="semantic",
    top_k=10
)

# Get cross-project patterns
patterns = rae_client.get_cross_project_patterns(
    pattern_type="refactoring",
    min_confidence=0.7
)

# Enrich local reflection
enriched = rae_client.enrich_reflection(
    local_reflection=my_reflection,
    context={"project_id": "my-project", "tags": ["python"]}
)

# Store refactoring outcome (feedback loop)
rae_client.store_refactor_outcome(
    refactor_decision=decision,
    outcome=outcome_data
)
```

### Memory Router

Intelligently routes between local (Qdrant) and global (RAE) storage:

```python
from feniks.core.memory.router import create_memory_router, RoutingStrategy

# Initialize
router = create_memory_router(
    qdrant_client=my_qdrant_client,
    project_id="my-project",
    strategy=RoutingStrategy.HYBRID
)

# Store with intelligent routing
result = router.store(
    data=my_reflection,
    data_type="reflection",
    metadata={"severity": "high"}
)
# Automatically decides: local, global, or both

# Retrieve with hybrid search
results = router.retrieve(
    query="authentication issues",
    strategy="hybrid",  # searches both local and global
    top_k=10
)

# Enrich local result with global context
enriched = router.enrich_with_global_context(local_result)
```

## 🔄 Usage Patterns

### Pattern 1: Enrich Reflections During Analysis

```python
from feniks.core.reflection.engine import MetaReflectionEngine
from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client

# Your existing reflection engine
engine = MetaReflectionEngine()
rae_client = create_enhanced_rae_client()

# Generate local reflection
local_reflection = engine.generate_reflection(system_model)

# Enrich with RAE insights
if rae_client:
    enriched_reflection = rae_client.enrich_reflection(
        local_reflection=local_reflection,
        context={
            "project_id": project_id,
            "tags": ["python", "microservice"]
        }
    )
else:
    enriched_reflection = local_reflection

# Use enriched reflection
print(enriched_reflection.recommendations)
```

### Pattern 2: Learn from Historical Refactorings

```python
from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client

rae_client = create_enhanced_rae_client()

# Before applying a refactoring, check historical success
historical = rae_client.get_historical_refactorings(
    refactor_type="extract-method",
    project_tags=["python"],
    min_success_rate=0.6,
    limit=10
)

# Analyze success patterns
for refactor in historical:
    print(f"Success rate: {refactor['success_rate']}")
    print(f"Context: {refactor.get('context', {})}")

# Make informed decision based on history
if any(r['success_rate'] > 0.8 for r in historical):
    apply_refactoring()
```

### Pattern 3: Feedback Loop for Continuous Learning

```python
from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client

rae_client = create_enhanced_rae_client()

# 1. Plan refactoring
refactor_decision = {
    "refactor_id": generate_id(),
    "project_id": project_id,
    "refactor_type": "extract-method",
    "target": "complex_function",
    "confidence": 0.85
}

# 2. Apply refactoring
success = apply_refactoring(refactor_decision)

# 3. Measure outcome
outcome = {
    "success": success,
    "metrics": {
        "complexity_before": 42,
        "complexity_after": 12,
        "test_coverage_before": 0.65,
        "test_coverage_after": 0.82
    },
    "issues": [],
    "rollback_required": False
}

# 4. Store outcome for learning
rae_client.store_refactor_outcome(
    refactor_decision=refactor_decision,
    outcome=outcome
)
# This helps RAE improve future recommendations!
```

### Pattern 4: Intelligent Storage with Memory Router

```python
from feniks.core.memory.router import create_memory_router

router = create_memory_router(
    qdrant_client=qdrant_client,
    project_id=project_id
)

# High-value data → Dual-write (local + global)
router.store(
    data=critical_reflection,
    data_type="reflection",
    metadata={"severity": "high"}
)

# Temporary analysis → Local only
router.store(
    data=temp_analysis,
    data_type="analysis",
    metadata={"ephemeral": True, "ttl": 3600}
)

# Cross-project pattern → Global only
router.store(
    data=global_pattern,
    data_type="pattern",
    metadata={"cross_project": True}
)
```

## 🔧 Configuration

### Routing Strategies

```python
from feniks.core.memory.router import RoutingStrategy

# Available strategies:
RoutingStrategy.LOCAL_ONLY   # Fast, project-specific
RoutingStrategy.GLOBAL_ONLY  # Cross-project learning
RoutingStrategy.DUAL_WRITE   # Store in both (recommended for critical data)
RoutingStrategy.HYBRID       # Intelligent routing (default)
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RAE_ENABLED` | No | `false` | Enable RAE integration |
| `RAE_BASE_URL` | Yes* | - | RAE API URL |
| `RAE_API_KEY` | No | - | API authentication key |
| `RAE_TENANT_ID` | No | `"default-tenant"` | Multi-tenancy identifier |
| `RAE_TIMEOUT` | No | `30` | Request timeout (seconds) |

*Required only if `RAE_ENABLED=true`

## 📊 Monitoring

The integration provides detailed logging:

```python
# Enable debug logging
import logging
logging.getLogger("integrations.enhanced_rae_client").setLevel(logging.DEBUG)
logging.getLogger("core.memory.router").setLevel(logging.DEBUG)
```

Key metrics to monitor:
- Routing decisions (local/global/dual)
- Enrichment success rate
- RAE API latency
- Storage operation success/failure

## 🧪 Testing

Run the integration tests:

```bash
# Unit tests
pytest tests/test_enhanced_rae_client.py -v
pytest tests/test_memory_router.py -v

# Integration example (requires RAE running)
python examples/rae_integration_example.py
```

## 📖 Further Reading

- **[Full Integration Blueprint](RAE_INTEGRATION_BLUEPRINT.md)** - Complete architecture and implementation guide
- **[RAE Documentation](https://github.com/your-org/RAE-agentic-memory)** - RAE project documentation
- **[Feniks Architecture](ARCHITECTURE.md)** - Feniks Clean Architecture overview

## 🐛 Troubleshooting

### RAE Connection Failed

```bash
# Check RAE is running
curl http://localhost:8000/health

# Check environment variables
echo $RAE_BASE_URL
echo $RAE_ENABLED
```

### Enrichment Returns Original Reflection

This is expected behavior when:
- RAE client is not available (degrades gracefully)
- No relevant insights found (min_similarity threshold)
- RAE API error occurs (logs warning, continues)

### Memory Router Always Uses Local Storage

Check:
1. `RAE_ENABLED=true` in `.env`
2. RAE client initialized successfully (check logs)
3. Routing strategy is not `LOCAL_ONLY`

## 💡 Best Practices

1. **Use Dual-Write for Critical Data**: System models, refactor outcomes, high-severity reflections
2. **Enable Feedback Loops**: Always store refactoring outcomes to improve learning
3. **Monitor RAE Availability**: Implement graceful degradation when RAE is unavailable
4. **Tag Your Data**: Use consistent project tags for better cross-project learning
5. **Set Appropriate Thresholds**: Adjust `min_similarity` based on your domain

## 🤝 Contributing

To extend the integration:

1. **Add new RAE operations**: Extend `EnhancedRAEClient` in `feniks/adapters/rae_client/enhanced_client.py`
2. **Customize routing logic**: Modify `FeniksMemoryRouter.route_storage()` in `feniks/core/memory/router.py`
3. **Add tests**: Create tests in `tests/test_enhanced_rae_client.py` or `tests/test_memory_router.py`

## 📝 License

Copyright 2025 Grzegorz Leśniowski
Licensed under the Apache License, Version 2.0

---

**Next Steps:**
1. Run the example: `python examples/rae_integration_example.py`
2. Read the [Full Integration Blueprint](RAE_INTEGRATION_BLUEPRINT.md)
3. Integrate into your Feniks workflows
