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
Postgres Storage Backend - Relational database storage for behavior models.

Provides enterprise-grade storage with:
- ACID transactions
- Advanced querying
- Foreign key relationships
- Contract versioning
"""
import json
from pathlib import Path
from typing import List, Optional

from feniks.adapters.storage.base import BehaviorStorageBackend, VersionedStorageMixin, register_storage_backend
from feniks.core.models.behavior import BehaviorCheckResult, BehaviorContract, BehaviorScenario, BehaviorSnapshot
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("adapters.storage.postgres")

# Postgres import with graceful fallback
try:
    import psycopg2
    from psycopg2.extras import Json, RealDictCursor

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    log.warning("psycopg2 not installed. Postgres backend will not be functional.")


# SQL Schema
SCHEMA_SQL = """
-- Scenarios table
CREATE TABLE IF NOT EXISTS behavior_scenarios (
    id VARCHAR(255) PRIMARY KEY,
    project_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    input JSONB NOT NULL,
    success_criteria JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_id (project_id),
    INDEX idx_category (category)
);

-- Snapshots table
CREATE TABLE IF NOT EXISTS behavior_snapshots (
    id VARCHAR(255) PRIMARY KEY,
    scenario_id VARCHAR(255) NOT NULL REFERENCES behavior_scenarios(id) ON DELETE CASCADE,
    project_id VARCHAR(255) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    observed_http JSONB,
    observed_cli JSONB,
    observed_dom JSONB,
    observed_logs JSONB,
    duration_ms INTEGER,
    success BOOLEAN NOT NULL,
    violations JSONB,
    error_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL,
    recorded_by VARCHAR(100),
    INDEX idx_scenario_env (scenario_id, environment),
    INDEX idx_created_at (created_at DESC)
);

-- Contracts table (with versioning)
CREATE TABLE IF NOT EXISTS behavior_contracts (
    id VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    scenario_id VARCHAR(255) NOT NULL REFERENCES behavior_scenarios(id) ON DELETE CASCADE,
    project_id VARCHAR(255) NOT NULL,
    success_criteria JSONB NOT NULL,
    max_duration_ms INTEGER,
    created_from_snapshots INTEGER,
    confidence_score REAL,
    created_at TIMESTAMP NOT NULL,
    version_notes TEXT,
    PRIMARY KEY (id, version),
    INDEX idx_scenario_id (scenario_id),
    INDEX idx_version (version)
);

-- Check results table
CREATE TABLE IF NOT EXISTS behavior_check_results (
    id SERIAL PRIMARY KEY,
    snapshot_id VARCHAR(255) NOT NULL REFERENCES behavior_snapshots(id) ON DELETE CASCADE,
    contract_id VARCHAR(255) NOT NULL,
    contract_version VARCHAR(50) NOT NULL,
    scenario_id VARCHAR(255) NOT NULL,
    passed BOOLEAN NOT NULL,
    violations JSONB,
    risk_score REAL NOT NULL,
    checked_at TIMESTAMP NOT NULL,
    FOREIGN KEY (contract_id, contract_version) REFERENCES behavior_contracts(id, version) ON DELETE CASCADE,
    INDEX idx_scenario_checked (scenario_id, checked_at DESC),
    INDEX idx_passed (passed)
);
"""


class PostgresBackend(BehaviorStorageBackend, VersionedStorageMixin):
    """
    Postgres storage backend for behavior models.

    Features:
    - Relational storage with foreign keys
    - Contract versioning
    - Advanced querying
    - ACID transactions
    - Batch operations
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "feniks",
        user: str = "postgres",
        password: str = "",
        **kwargs,
    ):
        """
        Initialize Postgres backend.

        Args:
            host: Postgres host
            port: Postgres port
            database: Database name
            user: Database user
            password: Database password
        """
        if not POSTGRES_AVAILABLE:
            raise FeniksError("psycopg2 not installed. Install with: pip install psycopg2-binary")

        self.connection_params = {"host": host, "port": port, "database": database, "user": user, "password": password}

        # Test connection and create schema
        try:
            self._execute_schema()
            log.info(f"PostgresBackend initialized (host={host}, database={database})")
        except Exception as e:
            raise FeniksError(f"Failed to initialize Postgres backend: {e}")

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.connection_params)

    def _execute_schema(self):
        """Create database schema."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
            log.debug("Database schema created/verified")
        finally:
            conn.close()

    # ========================================================================
    # Scenario Storage
    # ========================================================================

    def save_scenario(self, scenario: BehaviorScenario) -> None:
        """Save a behavior scenario."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO behavior_scenarios
                    (id, project_id, name, category, description, input, success_criteria, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        input = EXCLUDED.input,
                        success_criteria = EXCLUDED.success_criteria,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (
                        scenario.id,
                        scenario.project_id,
                        scenario.name,
                        scenario.category,
                        scenario.description,
                        Json(scenario.input.model_dump(mode="json")),
                        Json(scenario.success_criteria.model_dump(mode="json")),
                        Json(scenario.metadata or {}),
                        scenario.created_at,
                    ),
                )
            conn.commit()
            log.info(f"Saved scenario: {scenario.id}")
        finally:
            conn.close()

    def load_scenario(self, scenario_id: str) -> Optional[BehaviorScenario]:
        """Load a behavior scenario by ID."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM behavior_scenarios WHERE id = %s
                """,
                    (scenario_id,),
                )
                row = cur.fetchone()

                if row:
                    return BehaviorScenario(**dict(row))
                return None
        finally:
            conn.close()

    def list_scenarios(self, project_id: Optional[str] = None) -> List[BehaviorScenario]:
        """List all scenarios, optionally filtered by project."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if project_id:
                    cur.execute(
                        """
                        SELECT * FROM behavior_scenarios WHERE project_id = %s
                        ORDER BY created_at DESC
                    """,
                        (project_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM behavior_scenarios ORDER BY created_at DESC
                    """
                    )

                rows = cur.fetchall()
                return [BehaviorScenario(**dict(row)) for row in rows]
        finally:
            conn.close()

    def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario by ID. Returns True if deleted, False if not found."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM behavior_scenarios WHERE id = %s
                """,
                    (scenario_id,),
                )
                deleted = cur.rowcount > 0
            conn.commit()

            if deleted:
                log.info(f"Deleted scenario: {scenario_id}")
            return deleted
        finally:
            conn.close()

    # ========================================================================
    # Snapshot Storage
    # ========================================================================

    def save_snapshot(self, snapshot: BehaviorSnapshot) -> None:
        """Save a behavior snapshot."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO behavior_snapshots
                    (id, scenario_id, project_id, environment, observed_http, observed_cli,
                     observed_dom, observed_logs, duration_ms, success, violations,
                     error_count, metadata, created_at, recorded_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        observed_http = EXCLUDED.observed_http,
                        observed_cli = EXCLUDED.observed_cli,
                        observed_dom = EXCLUDED.observed_dom,
                        observed_logs = EXCLUDED.observed_logs,
                        duration_ms = EXCLUDED.duration_ms,
                        success = EXCLUDED.success,
                        violations = EXCLUDED.violations,
                        error_count = EXCLUDED.error_count,
                        metadata = EXCLUDED.metadata
                """,
                    (
                        snapshot.id,
                        snapshot.scenario_id,
                        snapshot.project_id,
                        snapshot.environment,
                        Json(snapshot.observed_http.model_dump(mode="json")) if snapshot.observed_http else None,
                        Json(snapshot.observed_cli.model_dump(mode="json")) if snapshot.observed_cli else None,
                        Json(snapshot.observed_dom.model_dump(mode="json")) if snapshot.observed_dom else None,
                        Json(snapshot.observed_logs.model_dump(mode="json")) if snapshot.observed_logs else None,
                        snapshot.duration_ms,
                        snapshot.success,
                        Json([v.model_dump(mode="json") for v in snapshot.violations]),
                        snapshot.error_count,
                        Json(snapshot.metadata or {}),
                        snapshot.created_at,
                        snapshot.recorded_by,
                    ),
                )
            conn.commit()
            log.info(f"Saved snapshot: {snapshot.id}")
        finally:
            conn.close()

    def load_snapshots(
        self, scenario_id: str, environment: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorSnapshot]:
        """Load snapshots for a scenario, optionally filtered by environment."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT * FROM behavior_snapshots
                    WHERE scenario_id = %s
                """
                params = [scenario_id]

                if environment:
                    query += " AND environment = %s"
                    params.append(environment)

                query += " ORDER BY created_at DESC"

                if limit:
                    query += " LIMIT %s"
                    params.append(limit)

                cur.execute(query, params)
                rows = cur.fetchall()
                return [BehaviorSnapshot(**dict(row)) for row in rows]
        finally:
            conn.close()

    def save_snapshots_batch(self, snapshots: List[BehaviorSnapshot], output_path: Path) -> None:
        """Save snapshots to batch file (JSONL export)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for snapshot in snapshots:
                f.write(json.dumps(snapshot.model_dump(mode="json")) + "\n")

        log.info(f"Exported {len(snapshots)} snapshots to {output_path}")

    def load_snapshots_batch(self, input_path: Path) -> List[BehaviorSnapshot]:
        """Load snapshots from batch file (JSONL import)."""
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
    # Contract Storage (with Versioning)
    # ========================================================================

    def save_contract(self, contract: BehaviorContract) -> None:
        """Save a behavior contract (creates new version)."""
        self.save_contract_version(contract)

    def save_contract_version(self, contract: BehaviorContract, version_notes: Optional[str] = None) -> str:
        """Save a new version of a contract."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO behavior_contracts
                    (id, version, scenario_id, project_id, success_criteria, max_duration_ms,
                     created_from_snapshots, confidence_score, created_at, version_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id, version) DO UPDATE SET
                        success_criteria = EXCLUDED.success_criteria,
                        max_duration_ms = EXCLUDED.max_duration_ms,
                        created_from_snapshots = EXCLUDED.created_from_snapshots,
                        confidence_score = EXCLUDED.confidence_score,
                        version_notes = EXCLUDED.version_notes
                """,
                    (
                        contract.id,
                        contract.version,
                        contract.scenario_id,
                        contract.project_id,
                        Json(contract.success_criteria.model_dump(mode="json")),
                        contract.max_duration_ms,
                        contract.created_from_snapshots,
                        contract.confidence_score,
                        contract.created_at,
                        version_notes or contract.version_notes,
                    ),
                )
            conn.commit()
            log.info(f"Saved contract version: {contract.id} v{contract.version}")
            return contract.version
        finally:
            conn.close()

    def load_contract(self, contract_id: str) -> Optional[BehaviorContract]:
        """Load latest version of a contract."""
        versions = self.get_contract_versions(contract_id)
        if versions:
            return versions[0]["contract"]
        return None

    def get_contract_version(self, contract_id: str, version: str) -> Optional[BehaviorContract]:
        """Get specific version of a contract."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM behavior_contracts
                    WHERE id = %s AND version = %s
                """,
                    (contract_id, version),
                )
                row = cur.fetchone()

                if row:
                    return BehaviorContract(**dict(row))
                return None
        finally:
            conn.close()

    def get_contract_versions(self, contract_id: str) -> List[dict]:
        """Get all versions of a contract."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM behavior_contracts
                    WHERE id = %s
                    ORDER BY created_at DESC
                """,
                    (contract_id,),
                )
                rows = cur.fetchall()

                return [
                    {
                        "version": row["version"],
                        "created_at": row["created_at"],
                        "notes": row["version_notes"],
                        "contract": BehaviorContract(**dict(row)),
                    }
                    for row in rows
                ]
        finally:
            conn.close()

    def load_contracts_for_scenario(self, scenario_id: str, version: Optional[str] = None) -> List[BehaviorContract]:
        """Load all contracts for a scenario, optionally filtered by version."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if version:
                    cur.execute(
                        """
                        SELECT * FROM behavior_contracts
                        WHERE scenario_id = %s AND version = %s
                        ORDER BY created_at DESC
                    """,
                        (scenario_id, version),
                    )
                else:
                    # Get latest version of each contract
                    cur.execute(
                        """
                        SELECT DISTINCT ON (id) *
                        FROM behavior_contracts
                        WHERE scenario_id = %s
                        ORDER BY id, created_at DESC
                    """,
                        (scenario_id,),
                    )

                rows = cur.fetchall()
                return [BehaviorContract(**dict(row)) for row in rows]
        finally:
            conn.close()

    def save_contracts_batch(self, contracts: List[BehaviorContract], output_path: Path) -> None:
        """Save contracts to batch file (JSONL export)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for contract in contracts:
                f.write(json.dumps(contract.model_dump(mode="json")) + "\n")

        log.info(f"Exported {len(contracts)} contracts to {output_path}")

    def load_contracts_batch(self, input_path: Path) -> List[BehaviorContract]:
        """Load contracts from batch file (JSONL import)."""
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
    # Check Result Storage
    # ========================================================================

    def save_check_result(self, result: BehaviorCheckResult) -> None:
        """Save a behavior check result."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO behavior_check_results
                    (snapshot_id, contract_id, contract_version, scenario_id, passed,
                     violations, risk_score, checked_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        result.snapshot_id,
                        result.contract_id,
                        "1.0.0",  # Default version if not specified
                        result.scenario_id,
                        result.passed,
                        Json([v.model_dump(mode="json") for v in result.violations]),
                        result.risk_score,
                        result.checked_at,
                    ),
                )
            conn.commit()
            log.info(f"Saved check result for snapshot: {result.snapshot_id}")
        finally:
            conn.close()

    def load_check_results(
        self, scenario_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[BehaviorCheckResult]:
        """Load check results, optionally filtered by scenario."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM behavior_check_results"
                params = []

                if scenario_id:
                    query += " WHERE scenario_id = %s"
                    params.append(scenario_id)

                query += " ORDER BY checked_at DESC"

                if limit:
                    query += " LIMIT %s"
                    params.append(limit)

                cur.execute(query, params)
                rows = cur.fetchall()
                return [BehaviorCheckResult(**dict(row)) for row in rows]
        finally:
            conn.close()

    def save_check_results_batch(self, results: List[BehaviorCheckResult], output_path: Path) -> None:
        """Save check results to batch file (JSONL export)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            for result in results:
                f.write(json.dumps(result.model_dump(mode="json")) + "\n")

        log.info(f"Exported {len(results)} check results to {output_path}")

    def load_check_results_batch(self, input_path: Path) -> List[BehaviorCheckResult]:
        """Load check results from batch file (JSONL import)."""
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


# Register Postgres backend
register_storage_backend("postgres", PostgresBackend)
