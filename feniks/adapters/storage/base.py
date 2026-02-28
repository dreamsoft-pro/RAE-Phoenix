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
Storage Abstraction Layer - Base interfaces for behavior storage backends.

Provides abstract base classes for pluggable storage implementations:
- File-based (JSONL)
- Relational (Postgres)
- Vector (Qdrant)
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from feniks.core.models.behavior import BehaviorCheckResult, BehaviorContract, BehaviorScenario, BehaviorSnapshot


class BehaviorStorageBackend(ABC):
    """
    Abstract base class for behavior storage backends.

    All storage implementations must implement this interface to ensure
    interoperability across file, database, and vector storage systems.
    """

    # ========================================================================
    # Scenario Storage
    # ========================================================================

    @abstractmethod
    def save_scenario(self, scenario: BehaviorScenario) -> None:
        """Save a behavior scenario."""
        pass

    @abstractmethod
    def load_scenario(self, scenario_id: str) -> Optional[BehaviorScenario]:
        """Load a behavior scenario by ID."""
        pass

    @abstractmethod
    def list_scenarios(self, project_id: Optional[str] = None) -> List[BehaviorScenario]:
        """List all scenarios, optionally filtered by project."""
        pass

    @abstractmethod
    def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario by ID. Returns True if deleted, False if not found."""
        pass

    # ========================================================================
    # Snapshot Storage
    # ========================================================================

    @abstractmethod
    def save_snapshot(self, snapshot: BehaviorSnapshot) -> None:
        """Save a behavior snapshot."""
        pass

    @abstractmethod
    def load_snapshots(
        self, scenario_id: str, environment: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorSnapshot]:
        """Load snapshots for a scenario, optionally filtered by environment."""
        pass

    @abstractmethod
    def save_snapshots_batch(self, snapshots: List[BehaviorSnapshot], output_path: Path) -> None:
        """Save snapshots to batch file (JSONL for file-based, export for DB)."""
        pass

    @abstractmethod
    def load_snapshots_batch(self, input_path: Path) -> List[BehaviorSnapshot]:
        """Load snapshots from batch file."""
        pass

    # ========================================================================
    # Contract Storage
    # ========================================================================

    @abstractmethod
    def save_contract(self, contract: BehaviorContract) -> None:
        """Save a behavior contract."""
        pass

    @abstractmethod
    def load_contract(self, contract_id: str) -> Optional[BehaviorContract]:
        """Load a behavior contract by ID."""
        pass

    @abstractmethod
    def load_contracts_for_scenario(self, scenario_id: str, version: Optional[str] = None) -> List[BehaviorContract]:
        """Load all contracts for a scenario, optionally filtered by version."""
        pass

    @abstractmethod
    def save_contracts_batch(self, contracts: List[BehaviorContract], output_path: Path) -> None:
        """Save contracts to batch file."""
        pass

    @abstractmethod
    def load_contracts_batch(self, input_path: Path) -> List[BehaviorContract]:
        """Load contracts from batch file."""
        pass

    # ========================================================================
    # Check Result Storage
    # ========================================================================

    @abstractmethod
    def save_check_result(self, result: BehaviorCheckResult) -> None:
        """Save a behavior check result."""
        pass

    @abstractmethod
    def load_check_results(
        self, scenario_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorCheckResult]:
        """Load check results, optionally filtered by scenario."""
        pass

    @abstractmethod
    def save_check_results_batch(self, results: List[BehaviorCheckResult], output_path: Path) -> None:
        """Save check results to batch file."""
        pass

    @abstractmethod
    def load_check_results_batch(self, input_path: Path) -> List[BehaviorCheckResult]:
        """Load check results from batch file."""
        pass


class SemanticSearchMixin(ABC):
    """
    Mixin for storage backends that support semantic search (e.g., Qdrant).

    Provides vector-based similarity search for scenarios and contracts.
    """

    @abstractmethod
    def search_similar_scenarios(
        self, query: str, limit: int = 10, project_id: Optional[str] = None
    ) -> List[BehaviorScenario]:
        """
        Search for scenarios similar to query text.

        Args:
            query: Natural language query
            limit: Maximum number of results
            project_id: Optional project filter

        Returns:
            List of scenarios ranked by similarity
        """
        pass

    @abstractmethod
    def search_similar_contracts(self, scenario_id: str, limit: int = 5) -> List[BehaviorContract]:
        """
        Search for contracts similar to a scenario.

        Useful for finding reusable contracts from similar scenarios.

        Args:
            scenario_id: Reference scenario ID
            limit: Maximum number of results

        Returns:
            List of contracts ranked by similarity
        """
        pass


class VersionedStorageMixin(ABC):
    """
    Mixin for storage backends that support contract versioning.

    Provides version management and history tracking for contracts.
    """

    @abstractmethod
    def save_contract_version(self, contract: BehaviorContract, version_notes: Optional[str] = None) -> str:
        """
        Save a new version of a contract.

        Args:
            contract: Contract to version
            version_notes: Optional version description

        Returns:
            Version identifier (e.g., "1.0.0", "2.1.3")
        """
        pass

    @abstractmethod
    def get_contract_versions(self, contract_id: str) -> List[dict]:
        """
        Get all versions of a contract.

        Args:
            contract_id: Contract identifier

        Returns:
            List of version metadata dictionaries with keys:
            - version: Version identifier
            - created_at: Timestamp
            - notes: Version notes
            - contract: Full contract object
        """
        pass

    @abstractmethod
    def get_contract_version(self, contract_id: str, version: str) -> Optional[BehaviorContract]:
        """
        Get specific version of a contract.

        Args:
            contract_id: Contract identifier
            version: Version identifier

        Returns:
            Contract at specified version, or None if not found
        """
        pass


# ============================================================================
# Storage Factory
# ============================================================================

_storage_registry = {}


def register_storage_backend(name: str, backend_class: type):
    """
    Register a storage backend implementation.

    Args:
        name: Backend name (e.g., "file", "postgres", "qdrant")
        backend_class: Class implementing BehaviorStorageBackend
    """
    _storage_registry[name] = backend_class


def create_storage_backend(backend_type: str, **kwargs) -> BehaviorStorageBackend:
    """
    Create storage backend instance.

    Args:
        backend_type: Type of backend ("file", "postgres", "qdrant")
        **kwargs: Backend-specific configuration

    Returns:
        Storage backend instance

    Raises:
        ValueError: If backend_type not registered
    """
    if backend_type not in _storage_registry:
        raise ValueError(f"Unknown storage backend: {backend_type}. " f"Available: {list(_storage_registry.keys())}")

    backend_class = _storage_registry[backend_type]
    return backend_class(**kwargs)
