#!/usr/bin/env python3
# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
RAE Integration Example - Demonstrates synergistic use of Enhanced RAE Client and Memory Router.

This example shows:
1. Using Enhanced RAE Client for bidirectional sync
2. Memory Router for intelligent storage routing
3. Reflection enrichment with global insights
4. Cross-project learning from historical data
5. Feedback loops for continuous improvement

Prerequisites:
- RAE API running (default: http://localhost:8000)
- Qdrant running (local instance)
- Environment variables configured (.env)

Usage:
    python examples/rae_integration_example.py
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from feniks.adapters.rae_client.enhanced_client import create_enhanced_rae_client
from feniks.core.memory.router import FeniksMemoryRouter, RoutingStrategy, create_memory_router
from feniks.core.models.types import (
    MetaReflection,
    ReflectionImpact,
    ReflectionLevel,
    ReflectionScope,
)
from feniks.infra.logging import get_logger

log = get_logger("examples.rae_integration")


class RAEIntegrationDemo:
    """Demonstrates RAE integration capabilities."""

    def __init__(self):
        """Initialize demo with RAE client and memory router."""
        log.info("=== RAE Integration Demo ===")

        # Initialize Enhanced RAE Client
        self.rae_client = create_enhanced_rae_client(
            base_url=os.getenv("RAE_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("RAE_API_KEY"),
            tenant_id=os.getenv("RAE_TENANT_ID", "demo-tenant"),
        )

        if not self.rae_client:
            log.warning("RAE client not available - some features will be limited")

        # Initialize Memory Router (with mock Qdrant for demo)
        self.memory_router = self._create_demo_router()

        self.project_id = "feniks-demo-project"
        log.info(f"Initialized for project: {self.project_id}")

    def _create_demo_router(self) -> FeniksMemoryRouter:
        """Create demo memory router with mock Qdrant client."""

        class MockQdrantClient:
            """Mock Qdrant client for demonstration."""

            def search(self, collection_name: str, query_vector: Any, limit: int = 10):
                log.debug(f"Mock Qdrant search: collection={collection_name}, limit={limit}")
                return []

            def upsert(self, collection_name: str, points: List[Any]):
                log.debug(f"Mock Qdrant upsert: collection={collection_name}, points={len(points)}")
                return True

        return create_memory_router(
            qdrant_client=MockQdrantClient(), project_id=self.project_id, strategy=RoutingStrategy.HYBRID
        )

    def demo_1_basic_reflection_storage(self):
        """Demo 1: Store a reflection with intelligent routing."""
        log.info("\n--- Demo 1: Basic Reflection Storage ---")

        # Create a sample reflection
        reflection = MetaReflection(
            id="demo_refl_001",
            timestamp=datetime.now().isoformat(),
            project_id=self.project_id,
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.MODULE,
            impact=ReflectionImpact.REFACTOR_RECOMMENDED,
            title="High Cyclomatic Complexity in Authentication Module",
            content="Detected high cyclomatic complexity (score: 42) in authentication module with 350 lines of code. "
            "This indicates potential maintainability issues.",
            recommendations=[
                "Extract authentication logic into separate services",
                "Add unit tests for edge cases",
                "Consider implementing circuit breaker pattern",
            ],
            metadata={
                "module": "auth",
                "complexity_score": 42,
                "lines_of_code": 350,
            },
            tags=["code-quality", "complexity"],
        )

        # Store with memory router - it will intelligently decide where to store
        result = self.memory_router.store(
            data=reflection, data_type="reflection", metadata={"severity": "high", "project_id": self.project_id}
        )

        log.info(f"Storage result: {result['routing_decision'].reason}")
        log.info(f"Local ID: {result['local_id']}")
        log.info(f"Global ID: {result['global_id']}")

        if result["errors"]:
            log.warning(f"Errors during storage: {result['errors']}")

    def demo_2_enrich_reflection_with_rae(self):
        """Demo 2: Enrich local reflection with RAE global insights."""
        log.info("\n--- Demo 2: Reflection Enrichment ---")

        if not self.rae_client:
            log.warning("RAE client not available - skipping enrichment demo")
            return

        # Create a local reflection
        local_reflection = MetaReflection(
            id="demo_refl_002",
            timestamp=datetime.now().isoformat(),
            project_id=self.project_id,
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.PATTERN,
            impact=ReflectionImpact.REFACTOR_RECOMMENDED,
            title="Large Monolithic Function Refactoring Opportunity",
            content="The process_order function contains 250 lines and should be refactored for better maintainability.",
            recommendations=["Consider Extract Method refactoring"],
            metadata={"function": "process_order", "lines": 250, "refactor_type": "extract-method"},
            tags=["refactoring", "extract-method"],
        )

        log.info(f"Original reflection: {local_reflection.title}")
        log.info(f"Original recommendations: {len(local_reflection.recommendations)}")

        # Enrich with RAE insights
        try:
            enriched_reflection = self.rae_client.enrich_reflection(
                local_reflection=local_reflection,
                context={"project_id": self.project_id, "tags": ["python", "e-commerce"]},
            )

            log.info(f"\nEnriched reflection: {enriched_reflection.title}")
            log.info(f"Enriched recommendations: {len(enriched_reflection.recommendations)}")
            log.info(f"RAE enriched: {enriched_reflection.metadata.get('rae_enriched', False)}")

            if enriched_reflection.recommendations != local_reflection.recommendations:
                log.info("\nNew recommendations from RAE:")
                for rec in enriched_reflection.recommendations[len(local_reflection.recommendations) :]:
                    log.info(f"  - {rec}")

        except Exception as e:
            log.error(f"Enrichment failed: {e}")

    def demo_3_cross_project_learning(self):
        """Demo 3: Learn from cross-project patterns."""
        log.info("\n--- Demo 3: Cross-Project Learning ---")

        if not self.rae_client:
            log.warning("RAE client not available - skipping cross-project demo")
            return

        try:
            # Get refactoring patterns from other projects
            log.info("Querying cross-project refactoring patterns...")
            patterns = self.rae_client.get_cross_project_patterns(
                pattern_type="refactoring", min_confidence=0.7, limit=5
            )

            log.info(f"\nFound {len(patterns)} cross-project patterns:")
            for idx, pattern in enumerate(patterns, 1):
                log.info(f"\nPattern {idx}:")
                log.info(f"  Type: {pattern.get('pattern_type', 'unknown')}")
                log.info(f"  Confidence: {pattern.get('confidence', 0):.2%}")
                log.info(f"  Projects: {pattern.get('project_count', 0)}")
                log.info(f"  Description: {pattern.get('description', 'N/A')}")

            # Get historical refactorings
            log.info("\n\nQuerying historical refactorings...")
            refactorings = self.rae_client.get_historical_refactorings(
                refactor_type="extract-method", project_tags=["python"], min_success_rate=0.6, limit=5
            )

            log.info(f"\nFound {len(refactorings)} historical refactorings:")
            for idx, refactor in enumerate(refactorings, 1):
                log.info(f"\nRefactoring {idx}:")
                log.info(f"  Type: {refactor.get('refactor_type', 'unknown')}")
                log.info(f"  Success rate: {refactor.get('success_rate', 0):.0%}")
                log.info(f"  Project: {refactor.get('project_id', 'unknown')}")

        except Exception as e:
            log.error(f"Cross-project learning failed: {e}")

    def demo_4_refactor_outcome_feedback_loop(self):
        """Demo 4: Store refactoring outcome for feedback loop."""
        log.info("\n--- Demo 4: Refactoring Feedback Loop ---")

        if not self.rae_client:
            log.warning("RAE client not available - skipping feedback loop demo")
            return

        # Simulate a refactoring decision
        refactor_decision = {
            "refactor_id": "demo_refactor_001",
            "project_id": self.project_id,
            "refactor_type": "extract-method",
            "target": "process_order function",
            "reasoning": "High complexity, low cohesion",
            "confidence": 0.85,
            "timestamp": datetime.now().isoformat(),
        }

        # Simulate refactoring outcome
        outcome = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "complexity_before": 42,
                "complexity_after": 12,
                "test_coverage_before": 0.65,
                "test_coverage_after": 0.82,
                "lines_reduced": 150,
            },
            "issues": [],
            "rollback_required": False,
            "pattern_match": True,
            "context_score": 0.9,
        }

        try:
            # Store outcome in RAE for learning
            log.info(f"Storing refactor outcome: {refactor_decision['refactor_id']}")
            self.rae_client.store_refactor_outcome(refactor_decision=refactor_decision, outcome=outcome)

            log.info("✓ Outcome stored successfully")
            log.info(
                f"  Complexity reduced: {outcome['metrics']['complexity_before']} → {outcome['metrics']['complexity_after']}"
            )
            log.info(
                f"  Test coverage improved: {outcome['metrics']['test_coverage_before']:.0%} → {outcome['metrics']['test_coverage_after']:.0%}"
            )
            log.info("\nThis outcome will now help improve future refactoring recommendations!")

        except Exception as e:
            log.error(f"Failed to store refactor outcome: {e}")

    def demo_5_hybrid_search(self):
        """Demo 5: Hybrid search across local and global storage."""
        log.info("\n--- Demo 5: Hybrid Search ---")

        query = "authentication refactoring patterns"

        # Try different search strategies
        for strategy in ["local", "global", "hybrid"]:
            log.info(f"\nSearching with strategy: {strategy}")
            try:
                results = self.memory_router.retrieve(query=query, strategy=strategy, top_k=5)

                log.info(f"Found {len(results)} results")
                for idx, result in enumerate(results[:3], 1):
                    log.info(
                        f"  Result {idx}: source={result.get('source', 'unknown')}, score={result.get('score', 0):.3f}"
                    )

            except Exception as e:
                log.error(f"Search failed with {strategy} strategy: {e}")

    def demo_6_routing_decisions(self):
        """Demo 6: Demonstrate routing decision logic."""
        log.info("\n--- Demo 6: Routing Decisions ---")

        test_cases = [
            {"data_type": "reflection", "metadata": {"severity": "high"}},
            {"data_type": "reflection", "metadata": {"severity": "low", "temporary": True}},
            {"data_type": "system_model", "metadata": {}},
            {"data_type": "refactor_outcome", "metadata": {"success": True}},
            {"data_type": "analysis", "metadata": {"ephemeral": True}},
            {"data_type": "pattern", "metadata": {"cross_project": True}},
        ]

        log.info("Routing decisions for different data types:\n")
        for case in test_cases:
            decision = self.memory_router.route_storage(data_type=case["data_type"], metadata=case["metadata"])

            log.info(f"Data type: {case['data_type']}")
            log.info(f"Metadata: {case['metadata']}")
            log.info(f"Decision: {decision.strategy.value}")
            log.info(f"  → Local: {decision.store_local}, Global: {decision.store_global}")
            log.info(f"  → Reason: {decision.reason}\n")

    def run_all_demos(self):
        """Run all demonstration scenarios."""
        try:
            self.demo_1_basic_reflection_storage()
            self.demo_2_enrich_reflection_with_rae()
            self.demo_3_cross_project_learning()
            self.demo_4_refactor_outcome_feedback_loop()
            self.demo_5_hybrid_search()
            self.demo_6_routing_decisions()

            log.info("\n=== All Demos Completed ===")
            log.info("This demonstration showed:")
            log.info("  ✓ Intelligent storage routing (local vs global)")
            log.info("  ✓ Reflection enrichment with RAE insights")
            log.info("  ✓ Cross-project pattern learning")
            log.info("  ✓ Refactoring feedback loops")
            log.info("  ✓ Hybrid search strategies")
            log.info("\nFor production use, integrate these patterns into your Feniks workflows!")

        except KeyboardInterrupt:
            log.info("\n\nDemo interrupted by user")
        except Exception as e:
            log.error(f"\n\nDemo failed with error: {e}", exc_info=True)


def check_environment():
    """Check if required environment variables are set."""
    required = ["RAE_BASE_URL"]
    optional = ["RAE_API_KEY", "RAE_TENANT_ID"]

    log.info("Checking environment configuration...")

    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
            log.warning(f"  ✗ {var} not set")
        else:
            log.info(f"  ✓ {var} = {os.getenv(var)}")

    for var in optional:
        if os.getenv(var):
            log.info(f"  ✓ {var} = {'***' if 'KEY' in var else os.getenv(var)}")
        else:
            log.info(f"  ○ {var} not set (optional)")

    if missing:
        log.warning(f"\nMissing required variables: {', '.join(missing)}")
        log.warning("Some features may not work. Set them in .env file or environment.")
        return False

    return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("RAE Integration Example")
    print("=" * 60)
    print("\nThis example demonstrates the synergistic integration")
    print("between Feniks and RAE for intelligent memory management.\n")

    # Check environment
    env_ok = check_environment()
    if not env_ok:
        print("\n⚠️  Environment not fully configured")
        print("Continue anyway? (y/n): ", end="")
        if input().lower() != "y":
            print("Exiting.")
            return

    print("\nStarting demo...\n")

    # Run demos
    demo = RAEIntegrationDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()
