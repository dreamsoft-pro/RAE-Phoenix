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
Unit tests for Feniks Memory Router.
"""
from unittest.mock import Mock, patch

import pytest

from feniks.core.memory.router import (
    FeniksMemoryRouter,
    RoutingDecision,
    RoutingStrategy,
    create_memory_router,
)


class MockQdrantClient:
    """Mock Qdrant client for testing."""

    def __init__(self):
        self.stored_data = []
        self.search_results = []

    def search(self, collection_name, query_vector, limit=10):
        return self.search_results[:limit]

    def upsert(self, collection_name, points):
        self.stored_data.extend(points)
        return True


class TestFeniksMemoryRouter:
    """Test Memory Router functionality."""

    @pytest.fixture
    def mock_qdrant(self):
        """Create mock Qdrant client."""
        return MockQdrantClient()

    @pytest.fixture
    def mock_rae_client(self):
        """Create mock Enhanced RAE client."""
        mock_rae = Mock()
        mock_rae.query_reflections.return_value = []
        mock_rae.store_meta_reflection.return_value = {"id": "rae_001"}
        mock_rae.store_refactor_outcome.return_value = {"id": "outcome_001"}
        mock_rae.store_system_model.return_value = {"id": "model_001"}
        return mock_rae

    @pytest.fixture
    def router(self, mock_qdrant, mock_rae_client):
        """Create memory router with mocks."""
        return FeniksMemoryRouter(
            qdrant_client=mock_qdrant,
            rae_client=mock_rae_client,
            default_strategy=RoutingStrategy.HYBRID,
            project_id="test_project",
        )

    @pytest.fixture
    def router_no_rae(self, mock_qdrant):
        """Create memory router without RAE client."""
        return FeniksMemoryRouter(
            qdrant_client=mock_qdrant,
            rae_client=None,
            default_strategy=RoutingStrategy.HYBRID,
            project_id="test_project",
        )

    def test_router_initialization(self, router):
        """Test router initializes correctly."""
        assert router.qdrant is not None
        assert router.rae is not None
        assert router.default_strategy == RoutingStrategy.HYBRID
        assert router.project_id == "test_project"

    def test_route_system_model_dual_write(self, router):
        """Test system models route to dual-write."""
        decision = router.route_storage(data_type="system_model", metadata={})

        assert decision.strategy == RoutingStrategy.DUAL_WRITE
        assert decision.store_local is True
        assert decision.store_global is True
        assert "critical for learning" in decision.reason.lower()

    def test_route_refactor_outcome_dual_write(self, router):
        """Test refactor outcomes route to dual-write."""
        decision = router.route_storage(data_type="refactor_outcome", metadata={})

        assert decision.strategy == RoutingStrategy.DUAL_WRITE
        assert decision.store_local is True
        assert decision.store_global is True

    def test_route_high_severity_reflection_dual_write(self, router):
        """Test high severity reflections route to dual-write."""
        decision = router.route_storage(data_type="reflection", metadata={"severity": "high"})

        assert decision.strategy == RoutingStrategy.DUAL_WRITE
        assert decision.store_local is True
        assert decision.store_global is True
        assert "high severity" in decision.reason.lower()

    def test_route_ephemeral_data_local_only(self, router):
        """Test ephemeral data routes to local only."""
        decision = router.route_storage(data_type="analysis", metadata={"ephemeral": True})

        assert decision.strategy == RoutingStrategy.LOCAL_ONLY
        assert decision.store_local is True
        assert decision.store_global is False
        assert "ephemeral" in decision.reason.lower()

    def test_route_cross_project_global_only(self, router):
        """Test cross-project data routes to global only."""
        decision = router.route_storage(data_type="pattern", metadata={"cross_project": True})

        assert decision.strategy == RoutingStrategy.GLOBAL_ONLY
        assert decision.store_local is False
        assert decision.store_global is True

    def test_route_without_rae_falls_back_to_local(self, router_no_rae):
        """Test routing without RAE client falls back to local."""
        decision = router_no_rae.route_storage(data_type="reflection", metadata={"severity": "high"})

        assert decision.strategy == RoutingStrategy.LOCAL_ONLY
        assert decision.store_local is True
        assert decision.store_global is False
        assert "unavailable" in decision.reason.lower()

    def test_store_with_local_only_routing(self, router):
        """Test storage with local-only routing."""
        data = {"content": "test data"}

        with patch.object(router, "route_storage") as mock_route:
            mock_route.return_value = RoutingDecision(
                strategy=RoutingStrategy.LOCAL_ONLY,
                store_local=True,
                store_global=False,
                reason="Test",
                metadata={},
            )

            with patch.object(router, "_store_local", return_value="local_123"):
                result = router.store(data=data, data_type="test", metadata={})

                assert result["local_id"] == "local_123"
                assert result["global_id"] is None

    def test_store_with_global_only_routing(self, router):
        """Test storage with global-only routing."""
        data = {"content": "test data"}

        with patch.object(router, "route_storage") as mock_route:
            mock_route.return_value = RoutingDecision(
                strategy=RoutingStrategy.GLOBAL_ONLY,
                store_local=False,
                store_global=True,
                reason="Test",
                metadata={},
            )

            with patch.object(router, "_store_global", return_value="global_123"):
                result = router.store(data=data, data_type="test", metadata={})

                assert result["local_id"] is None
                assert result["global_id"] == "global_123"

    def test_store_with_dual_write(self, router):
        """Test storage with dual-write routing."""
        data = {"content": "test data"}

        with patch.object(router, "route_storage") as mock_route:
            mock_route.return_value = RoutingDecision(
                strategy=RoutingStrategy.DUAL_WRITE,
                store_local=True,
                store_global=True,
                reason="Test",
                metadata={},
            )

            with patch.object(router, "_store_local", return_value="local_123"):
                with patch.object(router, "_store_global", return_value="global_123"):
                    result = router.store(data=data, data_type="test", metadata={})

                    assert result["local_id"] == "local_123"
                    assert result["global_id"] == "global_123"

    def test_store_handles_local_failure_gracefully(self, router):
        """Test storage handles local failure without crashing."""
        data = {"content": "test data"}

        with patch.object(router, "route_storage") as mock_route:
            mock_route.return_value = RoutingDecision(
                strategy=RoutingStrategy.DUAL_WRITE,
                store_local=True,
                store_global=True,
                reason="Test",
                metadata={},
            )

            with patch.object(router, "_store_local", side_effect=Exception("Local storage failed")):
                with patch.object(router, "_store_global", return_value="global_123"):
                    result = router.store(data=data, data_type="test", metadata={})

                    # Should continue and store globally
                    assert result["local_id"] is None
                    assert result["global_id"] == "global_123"
                    assert len(result["errors"]) == 1
                    assert "Local" in result["errors"][0]

    def test_store_handles_global_failure_gracefully(self, router):
        """Test storage handles global failure without crashing."""
        data = {"content": "test data"}

        with patch.object(router, "route_storage") as mock_route:
            mock_route.return_value = RoutingDecision(
                strategy=RoutingStrategy.DUAL_WRITE,
                store_local=True,
                store_global=True,
                reason="Test",
                metadata={},
            )

            with patch.object(router, "_store_local", return_value="local_123"):
                with patch.object(router, "_store_global", side_effect=Exception("Global storage failed")):
                    result = router.store(data=data, data_type="test", metadata={})

                    # Should continue and store locally
                    assert result["local_id"] == "local_123"
                    assert result["global_id"] is None
                    assert len(result["errors"]) == 1
                    assert "Global" in result["errors"][0]

    def test_retrieve_local_strategy(self, router):
        """Test retrieval with local strategy."""
        with patch.object(router, "_retrieve_local", return_value=[{"id": "local_1", "score": 0.9}]) as mock_local:
            results = router.retrieve(query="test query", strategy="local", top_k=10)

            assert len(results) == 1
            assert results[0]["id"] == "local_1"
            mock_local.assert_called_once()

    def test_retrieve_global_strategy(self, router):
        """Test retrieval with global strategy."""
        with patch.object(router, "_retrieve_global", return_value=[{"id": "global_1", "score": 0.85}]) as mock_global:
            results = router.retrieve(query="test query", strategy="global", top_k=10)

            assert len(results) == 1
            assert results[0]["id"] == "global_1"
            mock_global.assert_called_once()

    def test_retrieve_hybrid_strategy(self, router):
        """Test retrieval with hybrid strategy."""
        with patch.object(router, "_retrieve_hybrid", return_value=[{"id": "hybrid_1", "score": 0.92}]) as mock_hybrid:
            results = router.retrieve(query="test query", strategy="hybrid", top_k=10)

            assert len(results) == 1
            assert results[0]["id"] == "hybrid_1"
            mock_hybrid.assert_called_once()

    def test_enrich_with_global_context(self, router, mock_rae_client):
        """Test enriching local result with global context."""
        local_result = {"id": "local_1", "content": "test content"}

        mock_rae_client.query_reflections.return_value = [
            {"id": "rae_1", "context": "related insight 1"},
            {"id": "rae_2", "context": "related insight 2"},
        ]

        enriched = router.enrich_with_global_context(local_result)

        assert enriched["enriched"] is True
        assert "rae_context" in enriched
        assert len(enriched["rae_context"]) == 2

    def test_enrich_without_rae_returns_original(self, router_no_rae):
        """Test enrichment without RAE returns original result."""
        local_result = {"id": "local_1", "content": "test content"}

        enriched = router_no_rae.enrich_with_global_context(local_result)

        assert enriched == local_result
        assert "enriched" not in enriched

    def test_calculate_learning_value_high(self, router):
        """Test learning value calculation for high-value data."""
        value = router._calculate_learning_value(
            data_type="refactor_outcome",
            metadata={"success_rate": 0.9, "cross_project_applicable": True, "severity": "high"},
        )

        assert value > 0.7

    def test_calculate_learning_value_low(self, router):
        """Test learning value calculation for low-value data."""
        value = router._calculate_learning_value(data_type="analysis", metadata={})

        assert value < 0.7

    def test_hybrid_routing_decision_high_learning(self, router):
        """Test hybrid routing for high learning value data."""
        decision = router._hybrid_routing_decision(
            data_type="reflection", metadata={"cross_project_applicable": True, "severity": "high"}
        )

        assert decision.strategy == RoutingStrategy.DUAL_WRITE
        assert decision.store_local is True
        assert decision.store_global is True

    def test_factory_function_creates_router(self, mock_qdrant):
        """Test factory function creates router successfully."""
        with patch("feniks.core.memory.router.create_enhanced_rae_client", return_value=Mock()):
            router = create_memory_router(qdrant_client=mock_qdrant, project_id="test_project")

            assert router is not None
            assert isinstance(router, FeniksMemoryRouter)
            assert router.project_id == "test_project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
