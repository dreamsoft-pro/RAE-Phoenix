from dataclasses import dataclass
from typing import Any, Dict, List

from feniks.core.models.types import SystemModel
from feniks.infra.logging import get_logger

log = get_logger("governance.engine")


@dataclass
class ComplianceViolation:
    rule_id: str
    description: str
    severity: str
    location: str


class GovernanceEngine:
    """
    Enforces architectural and compliance rules across the codebase.
    """

    def __init__(self):
        self.rules = []

    def run_checks(self, system_model: SystemModel) -> Dict[str, Any]:
        """
        Run governance checks on the system model.
        """
        violations = []

        # Example Rule 1: Circular Dependencies
        cycles = self._check_circular_dependencies(system_model)
        if cycles:
            for cycle in cycles:
                violations.append(
                    ComplianceViolation(
                        rule_id="ARCH-001",
                        description=f"Circular dependency detected: {cycle}",
                        severity="HIGH",
                        location="SystemModel",
                    )
                )

        return {"status": "FAILED" if violations else "PASSED", "violations": [v.__dict__ for v in violations]}

    def _check_circular_dependencies(self, model: SystemModel) -> List[str]:
        """Simple DFS cycle detection stub."""
        # In a real scenario, we would traverse model.dependencies
        return []
