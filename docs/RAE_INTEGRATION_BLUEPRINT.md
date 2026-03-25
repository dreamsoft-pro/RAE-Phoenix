# Feniks ↔ RAE: Przewodnik Integracji dla Deweloperów

**Wersja:** 1.0
**Data:** 2025-11-29
**Status:** Implementation Guide
**Dla:** Feniks Developers

---

## 🎯 Wstęp

Ten dokument jest **praktycznym przewodnikiem** dla deweloperów Feniksa, którzy chcą wykorzystać RAE (Reflective Agentic Memory Engine) do wzbogacenia funkcjonalności meta-refleksji i uczenia się między projektami.

### Co Zyskuje Feniks dzięki RAE?

- ✅ **Multi-Project Learning**: Ucz się z historii wszystkich projektów, nie tylko bieżącego
- ✅ **Intelligent Refactoring**: Decyzje oparte na danych historycznych, nie tylko regułach
- ✅ **Cross-Project Patterns**: Wykrywaj wzorce powtarzające się w różnych projektach
- ✅ **Self-Improvement**: System automatycznie ulepsza swoje reguły na podstawie feedbacku
- ✅ **Temporal Evolution**: Śledź ewolucję codebase w czasie (nie tylko snapshoty)

### Dla kogo jest ten dokument?

- Deweloperzy rozszerzający Feniksa o nowe funkcje
- Team members pracujący z `MetaReflectionEngine`
- Contributors dodający nowe `RefactorRecipes`
- DevOps konfigurujący deployment z RAE

---

## 📚 Architektura: Jak to działa?

### Obecna Architektura Feniksa (Bez RAE)

```
┌─────────────────────────────────────────────────────────┐
│                  FENIKS STANDALONE                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  feniks analyze project-a                              │
│       │                                                 │
│       ├─→ Parse code chunks                            │
│       ├─→ Store in Qdrant (local)                      │
│       ├─→ Generate meta-reflections (rules-based)      │
│       └─→ Output: JSONL file                           │
│                                                         │
│  ❌ NO cross-project learning                          │
│  ❌ NO historical context                              │
│  ❌ NO intelligence feedback loop                      │
└─────────────────────────────────────────────────────────┘
```

### Nowa Architektura (Feniks + RAE Synergy)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FENIKS + RAE SYNERGY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  feniks analyze project-a                                       │
│       │                                                         │
│       ├─→ Parse code chunks                                    │
│       │       ├─→ Qdrant (fast local search)                   │
│       │       └─→ RAE episodic (global timeline)               │
│       │                                                         │
│       ├─→ Generate meta-reflections                            │
│       │       ├─→ Local rules (Feniks)                         │
│       │       └─→ Query RAE for similar patterns               │
│       │                   │                                     │
│       │                   └─→ RAE returns:                     │
│       │                       • 15 similar projects            │
│       │                       • Historical success rates       │
│       │                       • Common pitfalls                │
│       │                                                         │
│       └─→ Enrich recommendations                               │
│               └─→ Original + RAE insights                      │
│                                                                 │
│  ✅ Cross-project learning enabled                             │
│  ✅ Historical context from all projects                       │
│  ✅ Feedback loop (outcomes → RAE → better decisions)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementacja: Krok po Kroku

### Step 1: Konfiguracja

**Plik**: `feniks/.env`

```bash
# RAE Integration
RAE_ENABLED=true
RAE_BASE_URL=http://localhost:8000
RAE_API_KEY=your-rae-api-key-here
RAE_TIMEOUT=30

# Project Context
RAE_PROJECT_ID=feniks-project-alpha
RAE_TENANT_ID=your-organization
```

**Plik**: `feniks/config/settings.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...

    # RAE Integration (NEW)
    rae_enabled: bool = False
    rae_base_url: Optional[str] = None
    rae_api_key: Optional[str] = None
    rae_project_id: str = "default-project"
    rae_tenant_id: str = "default-tenant"
    rae_timeout: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Step 2: Enhanced RAE Client

**Nowy plik**: `feniks/adapters/rae_client/enhanced_client.py`

(Kod został już pokazany w dokumencie RAE - [link do sekcji](#31-enhanced-rae-client))

Kluczowe nowe metody:
- `query_reflections()` - Pobierz refleksje z RAE
- `get_cross_project_patterns()` - Wzorce z innych projektów
- `get_historical_refactorings()` - Historia refaktoryzacji
- `enrich_reflection()` - Wzbogać lokalną refleksję insights z RAE
- `store_refactor_outcome()` - Feedback loop

### Step 3: Memory Router

**Nowy plik**: `feniks/adapters/memory_router.py`

```python
"""
Memory Router - inteligentny routing między Qdrant (local) a RAE (global).
"""
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum

from feniks.adapters.storage.qdrant import QdrantClient
from feniks.adapters.rae_client.enhanced_client import EnhancedRAEClient
from feniks.core.models.types import MetaReflection, CodeChunk
from feniks.infra.logging import get_logger

log = get_logger("adapters.memory_router")


class MemoryDestination(str, Enum):
    """Where to store memory."""
    QDRANT = "qdrant"
    RAE = "rae"
    BOTH = "both"


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    primary: MemoryDestination
    secondary: Optional[MemoryDestination]
    reason: str


class FeniksMemoryRouter:
    """
    Routes memory operations between local (Qdrant) and global (RAE) storage.

    Routing Strategy:
    ┌─────────────────────┬──────────┬─────────────────────────────┐
    │ Data Type           │ Storage  │ Reason                      │
    ├─────────────────────┼──────────┼─────────────────────────────┤
    │ Code chunks         │ Qdrant   │ Fast local semantic search  │
    │ Meta-reflections    │ BOTH     │ Local cache + global learn  │
    │ Refactor decisions  │ BOTH     │ Local history + insights    │
    │ System capabilities │ RAE      │ Cross-project patterns      │
    │ Architectural patt. │ RAE      │ GraphRAG connections        │
    │ Behavior snapshots  │ Qdrant   │ Project-specific tests      │
    └─────────────────────┴──────────┴─────────────────────────────┘
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        rae_client: Optional[EnhancedRAEClient] = None
    ):
        self.qdrant = qdrant_client
        self.rae = rae_client
        self.stats = {"qdrant": 0, "rae": 0, "both": 0}

    def route_storage(self, data_type: str, metadata: Dict[str, Any]) -> RoutingDecision:
        """
        Decide where to store data based on type and metadata.

        Args:
            data_type: Type of data (code_chunk, meta_reflection, etc.)
            metadata: Additional context for routing decision

        Returns:
            RoutingDecision with primary and optional secondary storage
        """
        if data_type == "code_chunk":
            return RoutingDecision(
                primary=MemoryDestination.QDRANT,
                secondary=None,
                reason="Fast local semantic search for code"
            )

        elif data_type == "meta_reflection":
            if self.rae and self.rae.base_url:
                return RoutingDecision(
                    primary=MemoryDestination.BOTH,
                    secondary=None,
                    reason="Local cache + global learning"
                )
            else:
                return RoutingDecision(
                    primary=MemoryDestination.QDRANT,
                    secondary=None,
                    reason="RAE not available, using local only"
                )

        elif data_type == "refactor_decision":
            return RoutingDecision(
                primary=MemoryDestination.BOTH,
                secondary=None,
                reason="Track locally + learn globally"
            )

        elif data_type == "system_capability":
            if self.rae:
                return RoutingDecision(
                    primary=MemoryDestination.RAE,
                    secondary=None,
                    reason="Cross-project pattern detection"
                )
            else:
                return RoutingDecision(
                    primary=MemoryDestination.QDRANT,
                    secondary=None,
                    reason="Fallback to local when RAE unavailable"
                )

        elif data_type == "behavior_snapshot":
            return RoutingDecision(
                primary=MemoryDestination.QDRANT,
                secondary=None,
                reason="Project-specific test snapshots"
            )

        else:
            log.warning(f"Unknown data type: {data_type}, defaulting to Qdrant")
            return RoutingDecision(
                primary=MemoryDestination.QDRANT,
                secondary=None,
                reason="Default fallback"
            )

    def store(self, data: Any, data_type: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Store data with smart routing.

        Args:
            data: Data to store (CodeChunk, MetaReflection, etc.)
            data_type: Type of data
            metadata: Additional metadata for routing

        Returns:
            Dict with storage IDs and status
        """
        metadata = metadata or {}
        decision = self.route_storage(data_type, metadata)

        result = {"decision": decision.reason, "stored": []}

        # Store in primary location
        if decision.primary == MemoryDestination.QDRANT:
            qdrant_id = self._store_qdrant(data, data_type)
            result["stored"].append({"storage": "qdrant", "id": qdrant_id})
            self.stats["qdrant"] += 1

        elif decision.primary == MemoryDestination.RAE:
            rae_id = self._store_rae(data, data_type)
            result["stored"].append({"storage": "rae", "id": rae_id})
            self.stats["rae"] += 1

        elif decision.primary == MemoryDestination.BOTH:
            qdrant_id = self._store_qdrant(data, data_type)
            rae_id = self._store_rae(data, data_type)
            result["stored"].append({"storage": "qdrant", "id": qdrant_id})
            result["stored"].append({"storage": "rae", "id": rae_id})
            self.stats["both"] += 1

        log.info(f"Stored {data_type}: {decision.reason}")
        return result

    def retrieve(
        self,
        query: str,
        strategy: Literal["local", "global", "hybrid"] = "hybrid",
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve data with smart strategy.

        Args:
            query: Search query
            strategy: Retrieval strategy
                - local: Fast Qdrant search only
                - global: RAE insights only
                - hybrid: Combine both + rerank
            top_k: Number of results

        Returns:
            List of results with relevance scores
        """
        if strategy == "local":
            return self._retrieve_qdrant(query, top_k)

        elif strategy == "global":
            if not self.rae:
                log.warning("RAE not available, falling back to local")
                return self._retrieve_qdrant(query, top_k)
            return self._retrieve_rae(query, top_k)

        elif strategy == "hybrid":
            local_results = self._retrieve_qdrant(query, top_k=top_k * 2)
            if self.rae:
                global_results = self._retrieve_rae(query, top_k=top_k)
                return self._hybrid_rerank(local_results, global_results, top_k)
            else:
                return local_results[:top_k]

    def _store_qdrant(self, data: Any, data_type: str) -> str:
        """Store in Qdrant."""
        # Implementation depends on Qdrant schema
        # This is a placeholder
        return f"qdrant-{id(data)}"

    def _store_rae(self, data: Any, data_type: str) -> str:
        """Store in RAE."""
        if not self.rae:
            raise ValueError("RAE client not configured")

        if data_type == "meta_reflection":
            response = self.rae.store_meta_reflection(data.dict())
            return response.get("id", "unknown")

        elif data_type == "system_capability":
            response = self.rae.store_system_capabilities(data.dict())
            return response.get("id", "unknown")

        else:
            # Generic storage
            response = self.rae.store_system_model({"data": data, "type": data_type})
            return response.get("id", "unknown")

    def _retrieve_qdrant(self, query: str, top_k: int) -> List[Dict]:
        """Retrieve from Qdrant."""
        # Placeholder
        return []

    def _retrieve_rae(self, query: str, top_k: int) -> List[Dict]:
        """Retrieve from RAE."""
        if not self.rae:
            return []

        results = self.rae.query_reflections(
            project=self.rae.settings.rae_project_id,
            query=query,
            layer="semantic",
            top_k=top_k
        )
        return results

    def _hybrid_rerank(
        self,
        local: List[Dict],
        global_insights: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """
        Combine and rerank results from both sources.

        Strategy:
        1. Merge results
        2. Boost global insights (learned patterns)
        3. Rerank by combined score
        4. Return top K
        """
        combined = []

        # Add local results with base score
        for item in local:
            item["source"] = "local"
            item["final_score"] = item.get("score", 0.5)
            combined.append(item)

        # Add global results with boost
        for item in global_insights:
            item["source"] = "global"
            item["final_score"] = item.get("score", 0.5) * 1.2  # 20% boost
            combined.append(item)

        # Sort by final score
        combined.sort(key=lambda x: x["final_score"], reverse=True)

        return combined[:top_k]

    def get_stats(self) -> Dict[str, int]:
        """Get routing statistics."""
        return self.stats.copy()


# ========================================================================
# FACTORY
# ========================================================================

def create_memory_router(
    qdrant_client: QdrantClient,
    rae_client: Optional[EnhancedRAEClient] = None
) -> FeniksMemoryRouter:
    """
    Factory function to create memory router.

    Args:
        qdrant_client: Qdrant client instance
        rae_client: Optional RAE client (if None, only local routing)

    Returns:
        Configured FeniksMemoryRouter
    """
    router = FeniksMemoryRouter(qdrant_client, rae_client)
    log.info(f"Memory router created: RAE={'enabled' if rae_client else 'disabled'}")
    return router
```

### Step 4: Integracja z MetaReflectionEngine

**Zaktualizuj**: `feniks/core/reflection/engine.py`

```python
from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client

class MetaReflectionEngine:
    """Engine for generating meta-reflections from system analysis."""

    def __init__(self):
        self.rule_set = ReflectionRuleSet()
        self.post_mortem = PostMortemAnalyzer()
        self.longitudinal = LongitudinalAnalyzer()
        self.self_model = SelfModelAnalyzer()
        self.policy_manager = PolicyManager()

        # NEW: RAE integration
        self.rae_client = create_enhanced_rae_client()
        if self.rae_client:
            log.info("RAE integration enabled for reflection enrichment")
        else:
            log.info("RAE integration disabled, using local-only mode")

    def generate_reflections(
        self,
        system_model: SystemModel,
        enrich_with_rae: bool = True  # NEW parameter
    ) -> List[MetaReflection]:
        """
        Generate meta-reflections for a system model.

        Args:
            system_model: The system model to analyze
            enrich_with_rae: Whether to enrich with RAE insights (default: True)

        Returns:
            List[MetaReflection]: Generated meta-reflections
        """
        log.info(f"Generating meta-reflections for project: {system_model.project}")

        # Step 1: Generate local reflections (existing logic)
        reflections = self.rule_set.evaluate(system_model)

        # Step 2: Enrich with RAE insights (NEW)
        if enrich_with_rae and self.rae_client:
            reflections = self._enrich_reflections_with_rae(
                reflections,
                system_model
            )

        # Step 3: Sort by impact and level (existing logic)
        reflections.sort(
            key=lambda r: (
                ["critical", "refactor-recommended", "monitor", "informational"].index(r.impact.value),
                -r.level.value,
            )
        )

        log.info(f"Generated {len(reflections)} meta-reflections")
        return reflections

    def _enrich_reflections_with_rae(
        self,
        reflections: List[MetaReflection],
        system_model: SystemModel
    ) -> List[MetaReflection]:
        """
        Enrich local reflections with RAE insights.

        Process:
        1. For each reflection, query RAE for similar patterns
        2. Add cross-project insights to recommendations
        3. Adjust confidence based on historical data
        4. Mark enriched reflections with metadata

        Args:
            reflections: Local Feniks reflections
            system_model: System model for context

        Returns:
            Enriched reflections
        """
        enriched = []

        for reflection in reflections:
            try:
                # Enrich with RAE
                enriched_reflection = self.rae_client.enrich_reflection(
                    local_reflection=reflection,
                    context={
                        "project": system_model.project,
                        "project_tags": system_model.tags,
                        "module_count": len(system_model.modules),
                        "complexity_avg": system_model.average_complexity
                    }
                )

                enriched.append(enriched_reflection)

                log.debug(f"Enriched reflection: {reflection.id}")

            except Exception as e:
                log.warning(f"Failed to enrich reflection {reflection.id}: {e}")
                enriched.append(reflection)  # Keep original on error

        # Log enrichment stats
        enriched_count = sum(
            1 for r in enriched
            if r.metadata.get("rae_enrichment")
        )
        log.info(f"Enriched {enriched_count}/{len(reflections)} reflections with RAE insights")

        return enriched
```

### Step 5: Feedback Loop w RefactorEngine

**Zaktualizuj**: `feniks/core/refactor/engine.py`

```python
from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client

class RefactorEngine:
    """Engine for executing refactoring recipes."""

    def __init__(self):
        # ... existing init ...
        self.rae_client = create_enhanced_rae_client()

    def execute_refactoring(
        self,
        recipe: RefactorRecipe,
        target: RefactorTarget,
        dry_run: bool = True
    ) -> RefactorResult:
        """
        Execute a refactoring recipe.

        Args:
            recipe: Refactoring recipe to execute
            target: Target code to refactor
            dry_run: If True, don't apply changes (default)

        Returns:
            RefactorResult with outcome and metrics
        """
        log.info(f"Executing refactoring: {recipe.name} (dry_run={dry_run})")

        # STEP 1: Query RAE for historical data (NEW)
        if self.rae_client:
            historical_data = self._get_historical_insights(recipe, target)
            log.info(f"Found {len(historical_data)} similar refactorings in history")
        else:
            historical_data = []

        # STEP 2: Execute recipe (existing logic)
        result = recipe.execute(target, dry_run=dry_run)

        # STEP 3: Run validation
        validation_result = self._validate_refactoring(result, target)
        result.validation = validation_result

        # STEP 4: Store outcome to RAE (NEW - feedback loop)
        if not dry_run and self.rae_client:
            self._store_refactor_outcome(recipe, target, result)

        return result

    def _get_historical_insights(
        self,
        recipe: RefactorRecipe,
        target: RefactorTarget
    ) -> List[Dict[str, Any]]:
        """
        Get historical refactoring insights from RAE.

        Args:
            recipe: Recipe being executed
            target: Target code

        Returns:
            List of similar historical refactorings
        """
        if not self.rae_client:
            return []

        try:
            historical = self.rae_client.get_historical_refactorings(
                refactor_type=recipe.type,
                project_tags=target.metadata.get("tags", []),
                limit=50
            )

            # Log success rate
            if historical:
                total = len(historical)
                successful = sum(1 for h in historical if h.get("outcome") == "success")
                success_rate = (successful / total * 100) if total > 0 else 0
                log.info(f"Historical success rate for {recipe.type}: {success_rate:.1f}% ({successful}/{total})")

            return historical

        except Exception as e:
            log.warning(f"Failed to get historical insights: {e}")
            return []

    def _store_refactor_outcome(
        self,
        recipe: RefactorRecipe,
        target: RefactorTarget,
        result: RefactorResult
    ) -> None:
        """
        Store refactoring outcome to RAE for learning.

        Creates feedback loop: execute → store → RAE learns → better future decisions

        Args:
            recipe: Recipe that was executed
            target: Target that was refactored
            result: Execution result
        """
        if not self.rae_client:
            return

        try:
            outcome = {
                "status": "success" if result.success else "failure",
                "test_results": result.validation.get("test_results"),
                "metrics": {
                    "complexity_before": target.metrics.get("complexity"),
                    "complexity_after": result.metrics.get("complexity"),
                    "files_changed": result.metrics.get("files_changed"),
                    "lines_changed": result.metrics.get("lines_changed"),
                },
                "lessons": result.metadata.get("lessons_learned", []),
                "warnings": result.metadata.get("warnings", [])
            }

            refactor_decision = RefactorDecision(
                id=result.id,
                type=recipe.type,
                project=target.project,
                recipe_name=recipe.name,
                timestamp=result.timestamp
            )

            self.rae_client.store_refactor_outcome(refactor_decision, outcome)

            log.info(f"Stored refactor outcome to RAE: {result.id}")

        except Exception as e:
            log.warning(f"Failed to store refactor outcome: {e}")
```

---

## 💻 Przykłady Użycia

### Przykład 1: Analiza z Wzbogaceniem RAE

```bash
# CLI command
feniks analyze my-angular-project --enrich-with-rae

# Co się dzieje:
# 1. Feniks parsuje kod → Qdrant
# 2. Generuje lokalne refleksje
# 3. Query RAE: "Similar Angular projects?"
# 4. RAE zwraca 15 projektów z insights
# 5. Wzbogaca refleksje: "Based on 15 similar projects..."
# 6. Output: Enhanced meta_reflections.jsonl
```

### Przykład 2: Refaktoryzacja z Historycznym Kontekstem

```python
from feniks.core.refactor.engine import RefactorEngine
from feniks.core.refactor.recipes import AngularToReactMigration

engine = RefactorEngine()  # Automatic RAE integration

# Recipe gets historical insights automatically
recipe = AngularToReactMigration()
target = RefactorTarget(project_path="./my-angular-app")

# Execute with dry-run (safe)
result = engine.execute_refactoring(recipe, target, dry_run=True)

# RAE automatically queries history:
# - "Found 15 Angular→React migrations"
# - "Success rate: 80%"
# - "Common pitfall: State management"

print(f"Confidence: {result.confidence}")  # Based on historical data
print(f"Warnings: {result.warnings}")      # From similar projects
```

### Przykład 3: Programatyczny Dostęp do RAE Insights

```python
from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client

# Create client
rae = create_enhanced_rae_client()

# Query for patterns
patterns = rae.get_cross_project_patterns(
    pattern_type="extract_method",
    min_confidence=0.8,
    limit=10
)

for pattern in patterns:
    print(f"Pattern: {pattern['name']}")
    print(f"Success rate: {pattern['success_rate']}%")
    print(f"Used in {pattern['project_count']} projects")
    print(f"Recommendation: {pattern['recommendation']}")
    print("---")

# Query historical refactorings
history = rae.get_historical_refactorings(
    refactor_type="angular_to_react",
    project_tags=["spa", "enterprise"],
    limit=50
)

success_count = sum(1 for h in history if h["outcome"] == "success")
total = len(history)
print(f"Angular→React: {success_count}/{total} successful ({success_count/total*100:.1f}%)")
```

---

## 🧪 Testing

### Unit Tests dla Enhanced RAE Client

**Plik**: `feniks/tests/adapters/test_enhanced_rae_client.py`

```python
import pytest
from unittest.mock import Mock, patch
from feniks.adapters.rae_client.enhanced_client import EnhancedRAEClient
from feniks.core.models.types import MetaReflection

@pytest.fixture
def mock_rae_client():
    """Mock RAE client for testing."""
    with patch('feniks.adapters.rae_client.enhanced_client.requests.Session') as mock_session:
        client = EnhancedRAEClient(
            base_url="http://localhost:8000",
            api_key="test-key"
        )
        yield client, mock_session

def test_query_reflections(mock_rae_client):
    """Test querying reflections from RAE."""
    client, mock_session = mock_rae_client

    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {"id": "ref-1", "content": "High complexity detected", "score": 0.95},
            {"id": "ref-2", "content": "Missing tests", "score": 0.87}
        ]
    }
    mock_response.status_code = 200
    mock_session.return_value.request.return_value = mock_response

    # Execute
    results = client.query_reflections(
        project="test-project",
        query="complexity issues",
        layer="semantic",
        top_k=2
    )

    # Assert
    assert len(results) == 2
    assert results[0]["content"] == "High complexity detected"
    assert results[0]["score"] == 0.95

def test_enrich_reflection(mock_rae_client):
    """Test reflection enrichment with RAE insights."""
    client, mock_session = mock_rae_client

    # Create local reflection
    local_reflection = MetaReflection(
        id="local-1",
        project="test-project",
        content="High complexity in auth module",
        recommendations=["Refactor into smaller functions"],
        confidence=0.7,
        tags=["complexity", "refactor"]
    )

    # Mock RAE responses
    mock_session.return_value.request.side_effect = [
        # Query similar reflections
        Mock(json=lambda: {"results": [{"id": "r1"}, {"id": "r2"}]}, status_code=200),
        # Get patterns for "complexity"
        Mock(json=lambda: {"patterns": [{"recommendation": "Extract methods"}]}, status_code=200),
        # Get patterns for "refactor"
        Mock(json=lambda: {"patterns": []}, status_code=200),
    ]

    # Execute
    enriched = client.enrich_reflection(local_reflection)

    # Assert
    assert len(enriched.recommendations) > len(local_reflection.recommendations)
    assert enriched.confidence >= local_reflection.confidence
    assert "rae_enrichment" in enriched.metadata

def test_store_refactor_outcome(mock_rae_client):
    """Test storing refactoring outcome for learning."""
    client, mock_session = mock_rae_client

    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {"status": "success", "id": "outcome-1"}
    mock_response.status_code = 200
    mock_session.return_value.request.return_value = mock_response

    # Create refactor decision
    from feniks.core.models.types import RefactorDecision
    decision = RefactorDecision(
        id="refactor-1",
        type="extract_method",
        project="test-project"
    )

    outcome = {
        "status": "success",
        "test_results": {"passed": 10, "failed": 0},
        "metrics": {"complexity_reduction": 25}
    }

    # Execute
    result = client.store_refactor_outcome(decision, outcome)

    # Assert
    assert result["status"] == "success"
    assert result["id"] == "outcome-1"
```

### Integration Tests

**Plik**: `feniks/tests/integration/test_rae_integration.py`

```python
import pytest
from feniks.core.reflection.engine import MetaReflectionEngine
from feniks.core.models.types import SystemModel

@pytest.mark.integration
def test_end_to_end_with_rae(test_system_model):
    """Test complete flow: analyze → enrich → store."""

    # Create engine (will auto-connect to RAE if available)
    engine = MetaReflectionEngine()

    # Generate reflections
    reflections = engine.generate_reflections(
        system_model=test_system_model,
        enrich_with_rae=True  # Enable RAE enrichment
    )

    # Verify reflections were enriched
    enriched_count = sum(
        1 for r in reflections
        if r.metadata.get("rae_enrichment")
    )

    if engine.rae_client:
        assert enriched_count > 0, "RAE enabled but no reflections enriched"
    else:
        pytest.skip("RAE not available, skipping enrichment test")
```

---

## 📊 Monitoring & Observability

### Grafana Dashboard - RAE Integration Metrics

**Kluczowe metryki**:

```python
# feniks/infra/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# RAE Integration Metrics
rae_queries_total = Counter(
    'feniks_rae_queries_total',
    'Total RAE queries',
    ['query_type', 'status']
)

rae_query_duration_seconds = Histogram(
    'feniks_rae_query_duration_seconds',
    'RAE query duration',
    ['query_type']
)

rae_enrichment_count = Counter(
    'feniks_rae_enrichment_count',
    'Reflections enriched with RAE',
    ['project']
)

rae_confidence_boost = Histogram(
    'feniks_rae_confidence_boost',
    'Confidence boost from RAE insights',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.5, 1.0]
)

# Memory Router Metrics
memory_router_storage = Counter(
    'feniks_memory_router_storage_total',
    'Memory storage operations',
    ['destination']  # qdrant, rae, both
)

memory_router_retrieval_strategy = Counter(
    'feniks_memory_router_retrieval_total',
    'Memory retrieval operations',
    ['strategy']  # local, global, hybrid
)
```

---

## 🔗 Cross-Reference

### Dokumentacja RAE
Zobacz: `RAE-agentic-memory/docs/integrations/FENIKS_INTEGRATION_BLUEPRINT.md`

Sekcje szczególnie istotne dla Feniksa:
- [Część 2.3: Data Flow](#) - Szczegółowy przepływ danych
- [Część 3: Implementacja](#) - Kod Enhanced RAE Client (pełna wersja)
- [Część 4: Use Cases](#) - Real-world scenarios

### Dokumentacja Feniksa
- [Architecture](./ARCHITECTURE.md) - Feniks Clean Architecture
- [Overview](./OVERVIEW.md) - Feniks capabilities
- [Contributing](./CONTRIBUTING.md) - Development guidelines

---

## 🚀 Quick Start Checklist

Krok po kroku setup:

- [ ] 1. **Uruchom RAE API**
  ```bash
  cd RAE-agentic-memory
  docker-compose -f docker-compose.lite.yml up -d
  ```

- [ ] 2. **Skonfiguruj .env w Feniksie**
  ```bash
  cp .env.example .env
  # Edit .env:
  RAE_ENABLED=true
  RAE_BASE_URL=http://localhost:8000
  RAE_API_KEY=your-key
  ```

- [ ] 3. **Dodaj Enhanced RAE Client**
  ```bash
  # Copy code from blueprint
  cp docs/RAE_INTEGRATION_BLUEPRINT.md feniks/adapters/rae_client/enhanced_client.py
  ```

- [ ] 4. **Update MetaReflectionEngine**
  ```bash
  # Add RAE enrichment logic (see Step 4)
  ```

- [ ] 5. **Run Tests**
  ```bash
  pytest tests/adapters/test_enhanced_rae_client.py -v
  pytest tests/integration/test_rae_integration.py -v -m integration
  ```

- [ ] 6. **Analyze First Project**
  ```bash
  feniks analyze ./my-project --enrich-with-rae
  ```

- [ ] 7. **Verify RAE Storage**
  ```bash
  curl http://localhost:8000/v2/memories/query \
    -H "Content-Type: application/json" \
    -H "X-Tenant-Id: default-tenant" \
    -d '{"query":"my-project","top_k":5}'
  ```

---

## 📝 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-29 | Initial implementation guide |

---

## 👥 Contributors

- Feniks Team
- RAE Integration Team
- Implementation guide created with Claude Code

---

**Next Steps**:
1. Implement Phase 1 (see RAE blueprint document)
2. Create PR with Enhanced RAE Client
3. Add integration tests
4. Update CI/CD for RAE dependency

