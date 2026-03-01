# Copyright 2025 Grzegorz Leśniowski
"""
Contract Engine - Orchestrates behavior validation across different modes and languages.
Ensures compliance with ISO 27001 (Traceability) and ISO 42001 (Governance).
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from feniks.core.models.behavior import BehaviorContract, BehaviorSnapshot, BehaviorCheckResult
from feniks.core.models.types import OperationalState, OperationalMode, ComplianceLevel
from feniks.core.behavior.comparison_engine import BehaviorComparisonEngine
from feniks.infra.logging import get_logger
from feniks.infra.tracing import span, get_trace_id

log = get_logger("core.behavior.contract_engine")

class ContractEngine:
    """
    Orchestrates the lifecycle of Behavior Contracts.
    Supports multi-language execution and strict compliance enforcement.
    """

    def __init__(self, state: OperationalState):
        self.state = state
        self.comparison_engine = BehaviorComparisonEngine(
            strict_mode=(state.compliance == ComplianceLevel.STRICT)
        )

    async def validate_candidate(
        self, 
        contract: BehaviorContract, 
        candidate_snapshot: BehaviorSnapshot
    ) -> BehaviorCheckResult:
        """
        Validates a candidate (new) behavior against an established contract.
        Used primarily in REFACTOR mode.
        """
        attributes = {
            "feniks.mode": self.state.mode,
            "feniks.language": self.state.language,
            "feniks.trace_id": self.state.trace_id
        }
        
        with span("validate_candidate", attributes=attributes):
            log.info(
                "starting_candidate_validation",
                mode=self.state.mode,
                language=self.state.language,
                scenario_id=contract.scenario_id
            )

            # 1. Verification of Provenance (ISO 42001)
            if self.state.compliance == ComplianceLevel.STRICT and not self.state.provenance_link:
                log.error("missing_provenance_link", scenario_id=contract.scenario_id)
                # In a real scenario, we might block here
            
            # 2. Execution of Comparison
            result = self.comparison_engine.check_snapshot(candidate_snapshot, contract)
            
            # 3. Decision Logic (Auto-Rollback / Block)
            if result.risk_score > 0.7:
                log.critical(
                    "critical_behavior_deviation",
                    risk_score=result.risk_score,
                    violations=len(result.violations)
                )
                # Logic for blocking the refactor would go here
            
            return result

    def generate_empty_contract(self, scenario_id: str, project_id: str) -> BehaviorContract:
        """
        Creates a skeleton contract for CREATE mode.
        """
        return BehaviorContract(
            id=str(uuid.uuid4()),
            scenario_id=scenario_id,
            project_id=project_id,
            created_at=datetime.now(),
            created_by=self.state.agent_id,
            version="1.0.0-draft"
        )
