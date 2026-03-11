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
Cost Policies - Declarative rules for cost management.
Enforces limits and generates reflections for violations.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from feniks.core.models.domain import SessionSummary
from feniks.core.models.types import (
    MetaReflection,
    ReflectionEvidence,
    ReflectionImpact,
    ReflectionLevel,
    ReflectionScope,
)
from feniks.core.policies.cost import get_cost_controller
from feniks.infra.logging import get_logger

log = get_logger("core.policies.cost_policy")


@dataclass
class CostPolicyConfig:
    """Configuration for cost policies."""

    max_session_cost: float = 1.0  # Max cost per session
    alert_threshold_percent: float = 80.0  # Alert when budget usage exceeds this %
    monthly_budget: Optional[float] = None


class CostPolicyEnforcer:
    """Enforces cost policies and generates meta-reflections."""

    def __init__(self, config: CostPolicyConfig = CostPolicyConfig()):
        self.config = config
        self.controller = get_cost_controller()

    def check_session_cost(self, session: SessionSummary) -> List[MetaReflection]:
        """
        Check if a completed session violated cost policies.
        """
        reflections = []

        if not session.cost_profile:
            return reflections

        cost = session.cost_profile.cost_usd

        # Rule 1: Max Session Cost
        if cost > self.config.max_session_cost:
            reflections.append(
                MetaReflection(
                    id=f"policy-cost-max-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="policy-enforcer",
                    level=ReflectionLevel.META_REFLECTION,
                    scope=ReflectionScope.SYSTEM,
                    impact=ReflectionImpact.CRITICAL,
                    title="Max Session Cost Exceeded",
                    content=f"Session cost ${cost:.2f} exceeded limit of ${self.config.max_session_cost:.2f}.",
                    evidence=[
                        ReflectionEvidence(
                            type="metric",
                            source="cost_policy",
                            value=cost,
                            context=f"limit={self.config.max_session_cost}",
                        )
                    ],
                    recommendations=["Optimize prompt length", "Reduce context window usage"],
                )
            )

        return reflections

    def check_budget_health(self, project_id: str) -> List[MetaReflection]:
        """
        Check overall budget health for a project.
        """
        reflections = []
        budget = self.controller.get_budget(project_id)

        if not budget:
            return reflections

        # Rule 2: Budget Alert Threshold
        if budget.utilization >= self.config.alert_threshold_percent:
            impact = ReflectionImpact.CRITICAL if budget.utilization >= 95 else ReflectionImpact.REFACTOR_RECOMMENDED
            reflections.append(
                MetaReflection(
                    id=f"policy-budget-alert-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id=project_id,
                    level=ReflectionLevel.META_REFLECTION,
                    scope=ReflectionScope.SYSTEM,
                    impact=impact,
                    title="Budget Threshold Reached",
                    content=f"Budget utilization is at {budget.utilization:.1f}% (Threshold: {self.config.alert_threshold_percent}%).",
                    evidence=[ReflectionEvidence(type="metric", source="cost_policy", value=budget.utilization)],
                    recommendations=["Increase budget", "Stop low-priority tasks"],
                )
            )

        return reflections
