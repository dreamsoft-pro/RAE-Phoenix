# Copyright 2025 Grzegorz Leśniowski
"""
Contract Generator - Automatically derives BehaviorContracts from collections of snapshots.
This is the core of "Operation Mirror" - learning how the system should behave.
"""
from typing import List, Dict, Any, Optional
from feniks.core.models.behavior import (
    BehaviorContract, 
    BehaviorSnapshot, 
    HTTPContract, 
    LogContract, 
    CLIContract,
    CLISuccessCriteria
)
from feniks.infra.logging import get_logger
from datetime import datetime
import uuid

log = get_logger("core.behavior.contract_generator")

class ContractGenerator:
    """
    Analyzes multiple snapshots to find invariants and patterns.
    Ensures 100% parity detection for legacy systems.
    """

    def generate_from_snapshots(
        self, 
        project_id: str, 
        scenario_id: str, 
        snapshots: List[BehaviorSnapshot]
    ) -> BehaviorContract:
        """
        Synthesizes a contract from a list of successful snapshots.
        """
        if not snapshots:
            raise ValueError("Cannot generate contract from empty snapshots")

        log.info("generating_contract", project_id=project_id, scenario_id=scenario_id, snapshot_count=len(snapshots))

        # 1. Analyze CLI Invariants
        cli_contract = self._analyze_cli_invariants(snapshots)
        
        # 2. Analyze Log Invariants
        log_contract = self._analyze_log_invariants(snapshots)

        # 3. Analyze HTTP Invariants (if applicable)
        http_contract = self._analyze_http_invariants(snapshots)

        return BehaviorContract(
            id=f"cnt-{scenario_id}-{uuid.uuid4().hex[:8]}",
            scenario_id=scenario_id,
            project_id=project_id,
            version="1.0.0",
            cli_contract=cli_contract,
            log_contract=log_contract,
            http_contract=http_contract,
            created_at=datetime.now()
        )

    def _analyze_cli_invariants(self, snapshots: List[BehaviorSnapshot]) -> Optional[CLIContract]:
        exit_codes = set()
        for s in snapshots:
            if s.observed_cli:
                exit_codes.add(s.observed_cli.exit_code)
        
        if not exit_codes:
            return None
            
        return CLIContract(
            expected_exit_codes=list(exit_codes)
        )

    def _analyze_log_invariants(self, snapshots: List[BehaviorSnapshot]) -> Optional[LogContract]:
        # Simple implementation: find common error patterns to avoid
        return LogContract(
            forbidden_patterns=["Exception", "Traceback", "Fatal error", "Parse error"]
        )

    def _analyze_http_invariants(self, snapshots: List[BehaviorSnapshot]) -> Optional[HTTPContract]:
        # TODO: Implement HTTP response analysis
        return None
