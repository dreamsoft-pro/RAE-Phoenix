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
Policy Manager - Orchestrates execution of all policies.
Integrates Cost and Quality policies into a single enforcement point.
"""
from typing import List

from feniks.core.models.domain import SessionSummary
from feniks.core.models.types import MetaReflection
from feniks.core.policies.cost_policy import CostPolicyEnforcer
from feniks.core.policies.quality_policy import QualityPolicyEnforcer
from feniks.infra.logging import get_logger

log = get_logger("core.policies.manager")


class PolicyManager:
    """
    Central entry point for checking compliance with all system policies.
    """

    def __init__(self):
        self.cost_enforcer = CostPolicyEnforcer()
        self.quality_enforcer = QualityPolicyEnforcer()
        log.info("PolicyManager initialized")

    def check_session_compliance(self, session: SessionSummary, project_id: str) -> List[MetaReflection]:
        """
        Run all policy checks for a completed session.

        Args:
            session: The session summary to check.
            project_id: The project ID associated with the session.

        Returns:
            List[MetaReflection]: List of policy violations (as meta-reflections).
        """
        log.info(f"Checking policy compliance for session {session.session_id}")
        violations = []

        # 1. Check Cost Policies (Session limits)
        violations.extend(self.cost_enforcer.check_session_cost(session))

        # 2. Check Cost Policies (Budget health)
        violations.extend(self.cost_enforcer.check_budget_health(project_id))

        # 3. Check Quality Policies
        violations.extend(self.quality_enforcer.check_trace_quality(session))

        log.info(f"Policy checks complete. Found {len(violations)} violations.")
        return violations
