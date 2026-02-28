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
Qdrant Storage Backend - Vector database storage with semantic search.

Provides semantic search capabilities for:
- Finding similar scenarios
- Discovering reusable contracts
- Vector-based scenario recommendation
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from feniks.adapters.storage.base import (
    BehaviorStorageBackend,
    SemanticSearchMixin,
    VersionedStorageMixin,
    register_storage_backend,
)
from feniks.core.models.behavior import BehaviorCheckResult, BehaviorContract, BehaviorScenario, BehaviorSnapshot
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("adapters.storage.qdrant")

# Qdrant import with graceful fallback
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    log.warning("qdrant-client not installed. Qdrant backend will not be functional.")

# Sentence transformer for embeddings
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    log.warning("sentence-transformers not installed. Embeddings will not be available.")


class QdrantBackend(BehaviorStorageBackend, SemanticSearchMixin, VersionedStorageMixin):
    """
    Qdrant storage backend with semantic search.

    Features:
    - Vector-based semantic search
    - Scenario similarity matching
    - Contract recommendation
    - Full CRUD operations
    - Contract versioning
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_prefix: str = "feniks_behavior",
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_size: int = 384,
        **kwargs,
    ):
        """
        Initialize Qdrant backend.

        Args:
            host: Qdrant host
            port: Qdrant port
            collection_prefix: Prefix for collection names
            embedding_model: Sentence transformer model name
            vector_size: Embedding vector size
        """
        if not QDRANT_AVAILABLE:
            raise FeniksError("qdrant-client not installed. Install with: pip install qdrant-client")

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise FeniksError("sentence-transformers not installed. Install with: pip install sentence-transformers")

        self.client = QdrantClient(host=host, port=port)
        self.collection_prefix = collection_prefix
        self.vector_size = vector_size

        # Collection names
        self.scenarios_collection = f"{collection_prefix}_scenarios"
        self.snapshots_collection = f"{collection_prefix}_snapshots"
        self.contracts_collection = f"{collection_prefix}_contracts"
        self.results_collection = f"{collection_prefix}_results"

        # Initialize embedding model
        self.embedder = SentenceTransformer(embedding_model)

        # Create collections
        self._init_collections()

        log.info(f"QdrantBackend initialized (host={host}, model={embedding_model})")

    def _init_collections(self):
        """Create Qdrant collections if they don't exist."""
        collections = [
            self.scenarios_collection,
            self.snapshots_collection,
            self.contracts_collection,
            self.results_collection,
        ]

        for collection_name in collections:
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
                log.debug(f"Created collection: {collection_name}")

    def _embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        return self.embedder.encode(text).tolist()

    def _scenario_to_text(self, scenario: BehaviorScenario) -> str:
        """Convert scenario to searchable text."""
        parts = [scenario.name, scenario.description or "", scenario.category, f"project:{scenario.project_id}"]
        return " ".join(parts)

    def _contract_to_text(self, contract: BehaviorContract) -> str:
        """Convert contract to searchable text."""
        parts = [f"scenario:{contract.scenario_id}", f"version:{contract.version}", f"project:{contract.project_id}"]

        # Add criteria info
        if contract.success_criteria.http:
            parts.append("type:http")
        if contract.success_criteria.cli:
            parts.append("type:cli")
        if contract.success_criteria.dom:
            parts.append("type:dom")

        return " ".join(parts)

    # ========================================================================
    # Scenario Storage
    # ========================================================================

    def save_scenario(self, scenario: BehaviorScenario) -> None:
        """Save a behavior scenario."""
        text = self._scenario_to_text(scenario)
        vector = self._embed_text(text)

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "scenario_id": scenario.id,
                "project_id": scenario.project_id,
                "name": scenario.name,
                "category": scenario.category,
                "description": scenario.description,
                "data": scenario.model_dump(mode="json"),
                "created_at": scenario.created_at.isoformat(),
            },
        )

        self.client.upsert(collection_name=self.scenarios_collection, points=[point])

        log.info(f"Saved scenario: {scenario.id}")

    def load_scenario(self, scenario_id: str) -> Optional[BehaviorScenario]:
        """Load a behavior scenario by ID."""
        results = self.client.scroll(
            collection_name=self.scenarios_collection,
            scroll_filter=Filter(must=[FieldCondition(key="scenario_id", match=MatchValue(value=scenario_id))]),
            limit=1,
        )

        if results[0]:
            point = results[0][0]
            return BehaviorScenario(**point.payload["data"])
        return None

    def list_scenarios(self, project_id: Optional[str] = None) -> List[BehaviorScenario]:
        """List all scenarios, optionally filtered by project."""
        filter_conditions = []
        if project_id:
            filter_conditions.append(FieldCondition(key="project_id", match=MatchValue(value=project_id)))

        scroll_filter = Filter(must=filter_conditions) if filter_conditions else None

        results = self.client.scroll(collection_name=self.scenarios_collection, scroll_filter=scroll_filter, limit=1000)

        scenarios = []
        for point in results[0]:
            scenarios.append(BehaviorScenario(**point.payload["data"]))

        return scenarios

    def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario by ID."""
        results = self.client.scroll(
            collection_name=self.scenarios_collection,
            scroll_filter=Filter(must=[FieldCondition(key="scenario_id", match=MatchValue(value=scenario_id))]),
            limit=1,
        )

        if results[0]:
            point_id = results[0][0].id
            self.client.delete(collection_name=self.scenarios_collection, points_selector=[point_id])
            log.info(f"Deleted scenario: {scenario_id}")
            return True

        return False

    # ========================================================================
    # Semantic Search
    # ========================================================================

    def search_similar_scenarios(
        self, query: str, limit: int = 10, project_id: Optional[str] = None
    ) -> List[BehaviorScenario]:
        """Search for scenarios similar to query text."""
        vector = self._embed_text(query)

        filter_conditions = []
        if project_id:
            filter_conditions.append(FieldCondition(key="project_id", match=MatchValue(value=project_id)))

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        results = self.client.search(
            collection_name=self.scenarios_collection, query_vector=vector, query_filter=search_filter, limit=limit
        )

        scenarios = []
        for result in results:
            scenarios.append(BehaviorScenario(**result.payload["data"]))

        log.info(f"Found {len(scenarios)} similar scenarios for query: {query[:50]}")
        return scenarios

    def search_similar_contracts(self, scenario_id: str, limit: int = 5) -> List[BehaviorContract]:
        """Search for contracts similar to a scenario."""
        # Get scenario
        scenario = self.load_scenario(scenario_id)
        if not scenario:
            return []

        # Generate query from scenario
        query = self._scenario_to_text(scenario)
        vector = self._embed_text(query)

        results = self.client.search(collection_name=self.contracts_collection, query_vector=vector, limit=limit)

        contracts = []
        for result in results:
            contracts.append(BehaviorContract(**result.payload["data"]))

        log.info(f"Found {len(contracts)} similar contracts for scenario: {scenario_id}")
        return contracts

    # ========================================================================
    # Snapshot Storage (simplified - not vectorized)
    # ========================================================================

    def save_snapshot(self, snapshot: BehaviorSnapshot) -> None:
        """Save a behavior snapshot."""
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.0] * self.vector_size,  # Dummy vector
            payload={
                "snapshot_id": snapshot.id,
                "scenario_id": snapshot.scenario_id,
                "project_id": snapshot.project_id,
                "environment": snapshot.environment,
                "data": snapshot.model_dump(mode="json"),
                "created_at": snapshot.created_at.isoformat(),
            },
        )

        self.client.upsert(collection_name=self.snapshots_collection, points=[point])

        log.info(f"Saved snapshot: {snapshot.id}")

    def load_snapshots(
        self, scenario_id: str, environment: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorSnapshot]:
        """Load snapshots for a scenario."""
        filter_conditions = [FieldCondition(key="scenario_id", match=MatchValue(value=scenario_id))]

        if environment:
            filter_conditions.append(FieldCondition(key="environment", match=MatchValue(value=environment)))

        results = self.client.scroll(
            collection_name=self.snapshots_collection, scroll_filter=Filter(must=filter_conditions), limit=limit or 1000
        )

        snapshots = []
        for point in results[0]:
            snapshots.append(BehaviorSnapshot(**point.payload["data"]))

        return snapshots

    def save_snapshots_batch(self, snapshots: List[BehaviorSnapshot], output_path: Path) -> None:
        """Export snapshots to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for snapshot in snapshots:
                f.write(json.dumps(snapshot.model_dump(mode="json")) + "\n")

        log.info(f"Exported {len(snapshots)} snapshots to {output_path}")

    def load_snapshots_batch(self, input_path: Path) -> List[BehaviorSnapshot]:
        """Import snapshots from JSONL."""
        if not input_path.exists():
            raise FeniksError(f"Snapshot file not found: {input_path}")

        snapshots = []
        with input_path.open("r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    snapshot = BehaviorSnapshot(**data)
                    self.save_snapshot(snapshot)
                    snapshots.append(snapshot)

        log.info(f"Imported {len(snapshots)} snapshots from {input_path}")
        return snapshots

    # ========================================================================
    # Contract Storage (with Versioning and Search)
    # ========================================================================

    def save_contract(self, contract: BehaviorContract) -> None:
        """Save a behavior contract."""
        self.save_contract_version(contract)

    def save_contract_version(self, contract: BehaviorContract, version_notes: Optional[str] = None) -> str:
        """Save a new version of a contract."""
        text = self._contract_to_text(contract)
        vector = self._embed_text(text)

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "contract_id": contract.id,
                "version": contract.version,
                "scenario_id": contract.scenario_id,
                "project_id": contract.project_id,
                "data": contract.model_dump(mode="json"),
                "version_notes": version_notes or contract.version_notes,
                "created_at": contract.created_at.isoformat(),
            },
        )

        self.client.upsert(collection_name=self.contracts_collection, points=[point])

        log.info(f"Saved contract version: {contract.id} v{contract.version}")
        return contract.version

    def load_contract(self, contract_id: str) -> Optional[BehaviorContract]:
        """Load latest version of a contract."""
        versions = self.get_contract_versions(contract_id)
        if versions:
            return versions[0]["contract"]
        return None

    def get_contract_version(self, contract_id: str, version: str) -> Optional[BehaviorContract]:
        """Get specific version of a contract."""
        results = self.client.scroll(
            collection_name=self.contracts_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="contract_id", match=MatchValue(value=contract_id)),
                    FieldCondition(key="version", match=MatchValue(value=version)),
                ]
            ),
            limit=1,
        )

        if results[0]:
            return BehaviorContract(**results[0][0].payload["data"])
        return None

    def get_contract_versions(self, contract_id: str) -> List[dict]:
        """Get all versions of a contract."""
        results = self.client.scroll(
            collection_name=self.contracts_collection,
            scroll_filter=Filter(must=[FieldCondition(key="contract_id", match=MatchValue(value=contract_id))]),
            limit=1000,
        )

        versions = []
        for point in results[0]:
            payload = point.payload
            versions.append(
                {
                    "version": payload["version"],
                    "created_at": datetime.fromisoformat(payload["created_at"]),
                    "notes": payload.get("version_notes"),
                    "contract": BehaviorContract(**payload["data"]),
                }
            )

        # Sort by created_at descending
        versions.sort(key=lambda x: x["created_at"], reverse=True)
        return versions

    def load_contracts_for_scenario(self, scenario_id: str, version: Optional[str] = None) -> List[BehaviorContract]:
        """Load contracts for a scenario."""
        filter_conditions = [FieldCondition(key="scenario_id", match=MatchValue(value=scenario_id))]

        if version:
            filter_conditions.append(FieldCondition(key="version", match=MatchValue(value=version)))

        results = self.client.scroll(
            collection_name=self.contracts_collection, scroll_filter=Filter(must=filter_conditions), limit=1000
        )

        contracts = []
        for point in results[0]:
            contracts.append(BehaviorContract(**point.payload["data"]))

        return contracts

    def save_contracts_batch(self, contracts: List[BehaviorContract], output_path: Path) -> None:
        """Export contracts to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for contract in contracts:
                f.write(json.dumps(contract.model_dump(mode="json")) + "\n")

        log.info(f"Exported {len(contracts)} contracts to {output_path}")

    def load_contracts_batch(self, input_path: Path) -> List[BehaviorContract]:
        """Import contracts from JSONL."""
        if not input_path.exists():
            raise FeniksError(f"Contract file not found: {input_path}")

        contracts = []
        with input_path.open("r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    contract = BehaviorContract(**data)
                    self.save_contract(contract)
                    contracts.append(contract)

        log.info(f"Imported {len(contracts)} contracts from {input_path}")
        return contracts

    # ========================================================================
    # Check Result Storage (simplified)
    # ========================================================================

    def save_check_result(self, result: BehaviorCheckResult) -> None:
        """Save a behavior check result."""
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=[0.0] * self.vector_size,  # Dummy vector
            payload={
                "snapshot_id": result.snapshot_id,
                "contract_id": result.contract_id,
                "scenario_id": result.scenario_id,
                "passed": result.passed,
                "data": result.model_dump(mode="json"),
                "checked_at": result.checked_at.isoformat(),
            },
        )

        self.client.upsert(collection_name=self.results_collection, points=[point])

        log.info(f"Saved check result for snapshot: {result.snapshot_id}")

    def load_check_results(
        self, scenario_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorCheckResult]:
        """Load check results."""
        filter_conditions = []
        if scenario_id:
            filter_conditions.append(FieldCondition(key="scenario_id", match=MatchValue(value=scenario_id)))

        scroll_filter = Filter(must=filter_conditions) if filter_conditions else None

        results = self.client.scroll(
            collection_name=self.results_collection, scroll_filter=scroll_filter, limit=limit or 1000
        )

        check_results = []
        for point in results[0]:
            check_results.append(BehaviorCheckResult(**point.payload["data"]))

        return check_results

    def save_check_results_batch(self, results: List[BehaviorCheckResult], output_path: Path) -> None:
        """Export check results to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for result in results:
                f.write(json.dumps(result.model_dump(mode="json")) + "\n")

        log.info(f"Exported {len(results)} check results to {output_path}")

    def load_check_results_batch(self, input_path: Path) -> List[BehaviorCheckResult]:
        """Import check results from JSONL."""
        if not input_path.exists():
            raise FeniksError(f"Check results file not found: {input_path}")

        results = []
        with input_path.open("r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    result = BehaviorCheckResult(**data)
                    self.save_check_result(result)
                    results.append(result)

        log.info(f"Imported {len(results)} check results from {input_path}")
        return results


# Register Qdrant backend
register_storage_backend("qdrant", QdrantBackend)
