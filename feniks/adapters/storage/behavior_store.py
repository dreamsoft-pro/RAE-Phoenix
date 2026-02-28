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
Behavior Storage - Storage layer for BehaviorScenarios, Snapshots, and Contracts.

Provides file-based storage (JSONL) with future extensibility to Postgres/Qdrant.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from feniks.adapters.storage.base import BehaviorStorageBackend, register_storage_backend
from feniks.core.models.behavior import BehaviorCheckResult, BehaviorContract, BehaviorScenario, BehaviorSnapshot
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("adapters.storage.behavior")


class BehaviorStore(BehaviorStorageBackend):
    """
    Storage adapter for Behavior models.

    Currently uses file-based JSONL storage. Can be extended to:
    - Postgres for relational storage
    - Qdrant for vector-based similarity search
    """

    def __init__(self, storage_dir: str = "data/behavior"):
        """
        Initialize behavior store.

        Args:
            storage_dir: Base directory for storing behavior data
        """
        self.storage_dir = Path(storage_dir)
        self.scenarios_dir = self.storage_dir / "scenarios"
        self.snapshots_dir = self.storage_dir / "snapshots"
        self.contracts_dir = self.storage_dir / "contracts"
        self.results_dir = self.storage_dir / "results"

        # Create directories
        for dir_path in [self.scenarios_dir, self.snapshots_dir, self.contracts_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        log.info(f"BehaviorStore initialized: {self.storage_dir}")

    # ========================================================================
    # Scenario Storage
    # ========================================================================

    def save_scenario(self, scenario: BehaviorScenario) -> None:
        """Save a behavior scenario."""
        file_path = self.scenarios_dir / f"{scenario.id}.json"

        with file_path.open("w") as f:
            json.dump(scenario.model_dump(mode="json"), f, indent=2)

        log.info(f"Saved scenario: {scenario.id}")

    def load_scenario(self, scenario_id: str) -> Optional[BehaviorScenario]:
        """Load a behavior scenario by ID."""
        file_path = self.scenarios_dir / f"{scenario_id}.json"

        if not file_path.exists():
            log.warning(f"Scenario not found: {scenario_id}")
            return None

        with file_path.open("r") as f:
            data = json.load(f)

        return BehaviorScenario(**data)

    def list_scenarios(self, project_id: Optional[str] = None) -> List[BehaviorScenario]:
        """List all scenarios, optionally filtered by project."""
        scenarios = []

        for file_path in self.scenarios_dir.glob("*.json"):
            with file_path.open("r") as f:
                data = json.load(f)

            scenario = BehaviorScenario(**data)

            if project_id is None or scenario.project_id == project_id:
                scenarios.append(scenario)

        return scenarios

    def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario by ID. Returns True if deleted, False if not found."""
        file_path = self.scenarios_dir / f"{scenario_id}.json"

        if file_path.exists():
            file_path.unlink()
            log.info(f"Deleted scenario: {scenario_id}")
            return True
        else:
            log.warning(f"Scenario not found for deletion: {scenario_id}")
            return False

    # ========================================================================
    # Snapshot Storage
    # ========================================================================

    def save_snapshot(self, snapshot: BehaviorSnapshot) -> None:
        """Save a behavior snapshot."""
        # Organize by scenario_id/environment
        scenario_dir = self.snapshots_dir / snapshot.scenario_id / snapshot.environment
        scenario_dir.mkdir(parents=True, exist_ok=True)

        file_path = scenario_dir / f"{snapshot.id}.json"

        with file_path.open("w") as f:
            json.dump(snapshot.model_dump(mode="json"), f, indent=2)

        log.info(f"Saved snapshot: {snapshot.id} (scenario={snapshot.scenario_id}, env={snapshot.environment})")

    def load_snapshots(
        self, scenario_id: str, environment: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorSnapshot]:
        """Load all snapshots for a scenario, optionally filtered by environment."""
        snapshots = []
        scenario_dir = self.snapshots_dir / scenario_id

        if not scenario_dir.exists():
            return []

        # Iterate through environments
        for env_dir in scenario_dir.iterdir():
            if not env_dir.is_dir():
                continue

            # Filter by environment if specified
            if environment and env_dir.name != environment:
                continue

            # Load all snapshots in this environment
            for file_path in env_dir.glob("*.json"):
                with file_path.open("r") as f:
                    data = json.load(f)

                snapshots.append(BehaviorSnapshot(**data))

        # Apply limit if specified
        if limit is not None and len(snapshots) > limit:
            snapshots = snapshots[:limit]

        return snapshots

    def save_snapshots_batch(self, snapshots: List[BehaviorSnapshot], output_path: Path) -> None:
        """Save snapshots to batch file (JSONL)."""
        self.save_snapshots_jsonl(snapshots, output_path)

    def save_snapshots_jsonl(self, snapshots: List[BehaviorSnapshot], output_path: Path) -> None:
        """Save snapshots to JSONL file (for CLI output)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for snapshot in snapshots:
                f.write(json.dumps(snapshot.model_dump(mode="json")) + "\n")

        log.info(f"Saved {len(snapshots)} snapshots to {output_path}")

    def load_snapshots_batch(self, input_path: Path) -> List[BehaviorSnapshot]:
        """Load snapshots from batch file (JSONL)."""
        return self.load_snapshots_jsonl(input_path)

    def load_snapshots_jsonl(self, input_path: Path) -> List[BehaviorSnapshot]:
        """Load snapshots from JSONL file."""
        if not input_path.exists():
            raise FeniksError(f"Snapshot file not found: {input_path}")

        snapshots = []

        with input_path.open("r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    snapshots.append(BehaviorSnapshot(**data))

        log.info(f"Loaded {len(snapshots)} snapshots from {input_path}")
        return snapshots

    # ========================================================================
    # Contract Storage
    # ========================================================================

    def save_contract(self, contract: BehaviorContract) -> None:
        """Save a behavior contract."""
        # Organize by scenario_id
        scenario_dir = self.contracts_dir / contract.scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)

        file_path = scenario_dir / f"{contract.id}.json"

        with file_path.open("w") as f:
            json.dump(contract.model_dump(mode="json"), f, indent=2)

        log.info(f"Saved contract: {contract.id} (scenario={contract.scenario_id})")

    def load_contract(self, contract_id: str) -> Optional[BehaviorContract]:
        """Load a behavior contract by ID."""
        # Search all scenario directories
        for scenario_dir in self.contracts_dir.iterdir():
            if not scenario_dir.is_dir():
                continue

            file_path = scenario_dir / f"{contract_id}.json"
            if file_path.exists():
                with file_path.open("r") as f:
                    data = json.load(f)
                return BehaviorContract(**data)

        log.warning(f"Contract not found: {contract_id}")
        return None

    def load_contracts_for_scenario(self, scenario_id: str, version: Optional[str] = None) -> List[BehaviorContract]:
        """Load all contracts for a scenario, optionally filtered by version."""
        contracts = []
        scenario_dir = self.contracts_dir / scenario_id

        if not scenario_dir.exists():
            return []

        for file_path in scenario_dir.glob("*.json"):
            with file_path.open("r") as f:
                data = json.load(f)
            contract = BehaviorContract(**data)

            # Filter by version if specified
            if version is None or contract.version == version:
                contracts.append(contract)

        return contracts

    def save_contracts_batch(self, contracts: List[BehaviorContract], output_path: Path) -> None:
        """Save contracts to batch file (JSONL)."""
        self.save_contracts_jsonl(contracts, output_path)

    def save_contracts_jsonl(self, contracts: List[BehaviorContract], output_path: Path) -> None:
        """Save contracts to JSONL file (for CLI output)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for contract in contracts:
                f.write(json.dumps(contract.model_dump(mode="json")) + "\n")

        log.info(f"Saved {len(contracts)} contracts to {output_path}")

    def load_contracts_batch(self, input_path: Path) -> List[BehaviorContract]:
        """Load contracts from batch file (JSONL)."""
        return self.load_contracts_jsonl(input_path)

    def load_contracts_jsonl(self, input_path: Path) -> List[BehaviorContract]:
        """Load contracts from JSONL file."""
        if not input_path.exists():
            raise FeniksError(f"Contract file not found: {input_path}")

        contracts = []

        with input_path.open("r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    contracts.append(BehaviorContract(**data))

        log.info(f"Loaded {len(contracts)} contracts from {input_path}")
        return contracts

    # ========================================================================
    # Check Result Storage
    # ========================================================================

    def save_check_result(self, result: BehaviorCheckResult) -> None:
        """Save a behavior check result."""
        # Organize by timestamp
        date_dir = self.results_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        file_path = date_dir / f"{result.snapshot_id}.json"

        with file_path.open("w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2)

        log.info(f"Saved check result for snapshot: {result.snapshot_id}")

    def load_check_results(
        self, scenario_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorCheckResult]:
        """Load check results, optionally filtered by scenario."""
        results = []

        # Iterate through date directories
        for date_dir in sorted(self.results_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            for file_path in date_dir.glob("*.json"):
                with file_path.open("r") as f:
                    data = json.load(f)
                result = BehaviorCheckResult(**data)

                # Filter by scenario if specified
                if scenario_id is None or result.scenario_id == scenario_id:
                    results.append(result)

                    # Check limit
                    if limit is not None and len(results) >= limit:
                        return results

        return results

    def save_check_results_batch(self, results: List[BehaviorCheckResult], output_path: Path) -> None:
        """Save check results to batch file (JSONL)."""
        self.save_check_results_jsonl(results, output_path)

    def save_check_results_jsonl(self, results: List[BehaviorCheckResult], output_path: Path) -> None:
        """Save check results to JSONL file (for CLI output)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for result in results:
                f.write(json.dumps(result.model_dump(mode="json")) + "\n")

        log.info(f"Saved {len(results)} check results to {output_path}")

    def load_check_results_batch(self, input_path: Path) -> List[BehaviorCheckResult]:
        """Load check results from batch file (JSONL)."""
        return self.load_check_results_jsonl(input_path)

    def load_check_results_jsonl(self, input_path: Path) -> List[BehaviorCheckResult]:
        """Load check results from JSONL file."""
        if not input_path.exists():
            raise FeniksError(f"Check results file not found: {input_path}")

        results = []

        with input_path.open("r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    results.append(BehaviorCheckResult(**data))

        log.info(f"Loaded {len(results)} check results from {input_path}")
        return results


# ============================================================================
# Factory Function & Registration
# ============================================================================

_behavior_store_instance = None


def get_behavior_store(storage_dir: str = "data/behavior") -> BehaviorStore:
    """
    Get or create singleton BehaviorStore instance.

    Args:
        storage_dir: Base directory for behavior storage

    Returns:
        BehaviorStore instance
    """
    global _behavior_store_instance

    if _behavior_store_instance is None:
        _behavior_store_instance = BehaviorStore(storage_dir=storage_dir)

    return _behavior_store_instance


# Register file-based backend
register_storage_backend("file", BehaviorStore)
