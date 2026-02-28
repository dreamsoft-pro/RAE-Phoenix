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
Cost Controller - Manages budgets and cost limits for operations.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("governance.cost_controller")


@dataclass
class Budget:
    """Budget for a project or operation."""

    project_id: str
    total_budget: float  # Total budget in cost units
    spent: float = 0.0
    operations: Dict[str, int] = field(default_factory=dict)  # operation_type -> count
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, any] = field(default_factory=dict)

    @property
    def remaining(self) -> float:
        """Remaining budget."""
        return max(0.0, self.total_budget - self.spent)

    @property
    def utilization(self) -> float:
        """Budget utilization percentage."""
        return (self.spent / self.total_budget * 100) if self.total_budget > 0 else 0.0

    def can_afford(self, cost: float) -> bool:
        """Check if budget can afford operation."""
        return self.remaining >= cost


class BudgetExceededError(FeniksError):
    """Exception raised when budget is exceeded."""

    pass


class CostController:
    """
    Controls costs and enforces budgets.

    Features:
    - Per-project budgets
    - Operation cost tracking
    - Budget alerts and limits
    - Cost reporting
    """

    # Default operation costs (in arbitrary units)
    DEFAULT_COSTS = {
        "ingest": 1.0,  # Per 1000 chunks
        "analyze": 2.0,  # Per analysis
        "refactor": 5.0,  # Per refactoring
    }

    def __init__(self):
        """Initialize cost controller."""
        self.budgets: Dict[str, Budget] = {}
        self.operation_costs = self.DEFAULT_COSTS.copy()
        log.info("CostController initialized")

    def set_budget(self, project_id: str, total_budget: float):
        """
        Set budget for a project.

        Args:
            project_id: Project identifier
            total_budget: Total budget in cost units
        """
        if project_id in self.budgets:
            # Update existing budget
            budget = self.budgets[project_id]
            budget.total_budget = total_budget
            log.info(f"Updated budget for project {project_id}: {total_budget}")
        else:
            # Create new budget
            budget = Budget(project_id=project_id, total_budget=total_budget)
            self.budgets[project_id] = budget
            log.info(f"Created budget for project {project_id}: {total_budget}")

    def get_budget(self, project_id: str) -> Optional[Budget]:
        """
        Get budget for a project.

        Args:
            project_id: Project identifier

        Returns:
            Budget or None if no budget set
        """
        return self.budgets.get(project_id)

    def check_budget(self, project_id: str, operation: str, quantity: int = 1) -> tuple[bool, float]:
        """
        Check if operation is within budget.

        Args:
            project_id: Project identifier
            operation: Operation type
            quantity: Operation quantity (e.g., number of chunks)

        Returns:
            Tuple of (can_proceed, estimated_cost)

        Raises:
            BudgetExceededError: If budget would be exceeded
        """
        budget = self.budgets.get(project_id)

        # No budget set - allow operation
        if not budget:
            return True, 0.0

        # Calculate cost
        unit_cost = self.operation_costs.get(operation, 1.0)
        estimated_cost = unit_cost * quantity

        # Check if budget can afford it
        can_afford = budget.can_afford(estimated_cost)

        if not can_afford:
            raise BudgetExceededError(
                f"Budget exceeded for project {project_id}. "
                f"Remaining: {budget.remaining:.2f}, Required: {estimated_cost:.2f}"
            )

        return can_afford, estimated_cost

    def charge_operation(self, project_id: str, operation: str, quantity: int = 1, actual_cost: Optional[float] = None):
        """
        Charge budget for an operation.

        Args:
            project_id: Project identifier
            operation: Operation type
            quantity: Operation quantity
            actual_cost: Actual cost (if different from estimate)
        """
        budget = self.budgets.get(project_id)

        # No budget set - nothing to charge
        if not budget:
            return

        # Calculate cost
        if actual_cost is not None:
            cost = actual_cost
        else:
            unit_cost = self.operation_costs.get(operation, 1.0)
            cost = unit_cost * quantity

        # Update budget
        budget.spent += cost

        # Track operations
        if operation not in budget.operations:
            budget.operations[operation] = 0
        budget.operations[operation] += quantity

        log.info(
            f"Charged {cost:.2f} to project {project_id} for {operation} " f"(utilization: {budget.utilization:.1f}%)"
        )

        # Alert if budget is running low
        if budget.utilization > 90:
            log.warning(f"Budget alert: Project {project_id} has used {budget.utilization:.1f}% of budget")

    def get_cost_report(self, project_id: Optional[str] = None) -> Dict[str, any]:
        """
        Get cost report.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            Dict with cost information
        """
        if project_id:
            budget = self.budgets.get(project_id)
            if not budget:
                return {"project_id": project_id, "budget": None}

            return {
                "project_id": project_id,
                "budget": {
                    "total": budget.total_budget,
                    "spent": budget.spent,
                    "remaining": budget.remaining,
                    "utilization": budget.utilization,
                    "operations": budget.operations,
                },
            }

        # All projects
        return {
            "projects": {
                pid: {
                    "total": b.total_budget,
                    "spent": b.spent,
                    "remaining": b.remaining,
                    "utilization": b.utilization,
                    "operations": b.operations,
                }
                for pid, b in self.budgets.items()
            },
            "total_spent": sum(b.spent for b in self.budgets.values()),
        }

    def export_costs(self, output_path: Path):
        """
        Export cost data to JSON file.

        Args:
            output_path: Path to export costs
        """
        report = self.get_cost_report()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        log.info(f"Cost report exported to {output_path}")

    def set_operation_cost(self, operation: str, cost: float):
        """
        Set cost for an operation type.

        Args:
            operation: Operation type
            cost: Cost per unit
        """
        self.operation_costs[operation] = cost
        log.info(f"Set cost for {operation}: {cost}")


# Global instance
_cost_controller: Optional[CostController] = None


def get_cost_controller() -> CostController:
    """Get global cost controller instance."""
    global _cost_controller
    if _cost_controller is None:
        _cost_controller = CostController()
    return _cost_controller
