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
Longitudinal Analysis Loop - analyzes trends across multiple sessions over time.
"""
import statistics
import uuid
from collections import Counter
from datetime import datetime
from typing import List, Optional

from feniks.core.models.behavior import BehaviorCheckResult
from feniks.core.models.domain import SessionSummary
from feniks.core.models.types import (
    MetaReflection,
    ReflectionEvidence,
    ReflectionImpact,
    ReflectionLevel,
    ReflectionScope,
)
from feniks.infra.logging import get_logger

log = get_logger("core.reflection.longitudinal")


class LongitudinalAnalyzer:
    """
    Analyzes trends across multiple sessions (Longitudinal).
    """

    def analyze_trends(
        self, sessions: List[SessionSummary], behavior_checks: Optional[List[BehaviorCheckResult]] = None
    ) -> List[MetaReflection]:
        """
        Analyze multiple sessions to detect trends.

        Args:
            sessions: List of session summaries (historical data).
            behavior_checks: Optional list of behavior check results over time.

        Returns:
            List[MetaReflection]: Trend-based reflections.
        """
        log.info(f"Starting Longitudinal analysis on {len(sessions)} sessions.")
        if len(sessions) < 2:
            log.info("Not enough sessions for longitudinal analysis.")
            return []

        reflections = []

        # 1. Success Rate Trend
        success_ref = self._analyze_success_rate(sessions)
        if success_ref:
            reflections.append(success_ref)

        # 2. Cost Trend
        cost_ref = self._analyze_cost_trend(sessions)
        if cost_ref:
            reflections.append(cost_ref)

        # 3. Behavior Check Trends (Legacy Behavior Guard integration)
        if behavior_checks and len(behavior_checks) >= 5:
            behavior_refs = self._analyze_behavior_trends(behavior_checks)
            reflections.extend(behavior_refs)

        log.info(f"Longitudinal analysis complete. Generated {len(reflections)} reflections.")
        return reflections

    def _analyze_success_rate(self, sessions: List[SessionSummary]) -> Optional[MetaReflection]:
        success_count = sum(1 for s in sessions if s.success)
        rate = success_count / len(sessions)

        if rate < 0.7:  # Below 70% success rate
            return MetaReflection(
                id=f"long-success-{uuid.uuid4()}",
                timestamp=datetime.now().isoformat(),
                project_id="longitudinal",
                level=ReflectionLevel.META_REFLECTION,
                scope=ReflectionScope.SYSTEM,
                impact=ReflectionImpact.CRITICAL,
                title="Low Global Success Rate",
                content=f"Global success rate is {rate:.1%} across {len(sessions)} sessions.",
                evidence=[ReflectionEvidence(type="metric", source="session_history", value=rate)],
                recommendations=["Conduct deep dive into failed sessions", "Review recent changes to agent logic"],
            )
        return None

    def _analyze_cost_trend(self, sessions: List[SessionSummary]) -> Optional[MetaReflection]:
        costs = [s.cost_profile.cost_usd for s in sessions if s.cost_profile]
        if not costs or len(costs) < 5:
            return None

        # Simple linear trend check (comparing avg of first half vs last half)
        mid = len(costs) // 2
        first_half_avg = statistics.mean(costs[:mid])
        last_half_avg = statistics.mean(costs[mid:])

        if last_half_avg > first_half_avg * 1.2:  # 20% increase
            return MetaReflection(
                id=f"long-cost-inc-{uuid.uuid4()}",
                timestamp=datetime.now().isoformat(),
                project_id="longitudinal",
                level=ReflectionLevel.REFLECTION,
                scope=ReflectionScope.TECHNICAL_DEBT,
                impact=ReflectionImpact.MONITOR,
                title="Rising Cost Trend",
                content=f"Average session cost increased from ${first_half_avg:.3f} to ${last_half_avg:.3f} (+{((last_half_avg/first_half_avg)-1)*100:.1f}%)",
                evidence=[ReflectionEvidence(type="trend", source="cost_history", value=last_half_avg)],
                recommendations=["Audit token usage", "Check for prompt bloating"],
            )
        return None

    def _analyze_behavior_trends(self, checks: List[BehaviorCheckResult]) -> List[MetaReflection]:
        """
        Analyze behavior check trends over time (Legacy Behavior Guard integration).

        Detects:
        - Declining pass rate (regression trend)
        - Rising risk scores (quality degradation)
        - Emerging violation patterns

        Args:
            checks: List of behavior check results ordered by time

        Returns:
            List of trend-based meta-reflections
        """
        reflections = []

        # 1. Analyze Pass Rate Trend
        mid = len(checks) // 2
        first_half = checks[:mid]
        last_half = checks[mid:]

        first_pass_rate = sum(1 for c in first_half if c.passed) / len(first_half)
        last_pass_rate = sum(1 for c in last_half if c.passed) / len(last_half)

        # Detect declining pass rate (> 15% decrease)
        if first_pass_rate - last_pass_rate > 0.15:
            reflections.append(
                MetaReflection(
                    id=f"long-behavior-decline-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="longitudinal",
                    level=ReflectionLevel.META_REFLECTION,
                    scope=ReflectionScope.SYSTEM,
                    impact=ReflectionImpact.CRITICAL,
                    title="Declining Behavior Check Pass Rate",
                    content=f"Pass rate declined from {first_pass_rate:.1%} to {last_pass_rate:.1%} (Δ-{(first_pass_rate-last_pass_rate)*100:.1f}%)",
                    evidence=[ReflectionEvidence(type="trend", source="behavior_checks", value=last_pass_rate)],
                    recommendations=[
                        "Halt refactoring efforts until regression root cause is identified",
                        "Review recent code changes for unintended behavioral modifications",
                        "Expand behavior contract coverage to catch more edge cases",
                    ],
                )
            )

        # 2. Analyze Risk Score Trend
        first_avg_risk = statistics.mean(c.risk_score for c in first_half)
        last_avg_risk = statistics.mean(c.risk_score for c in last_half)

        # Detect rising risk (> 25% increase)
        if last_avg_risk > first_avg_risk * 1.25:
            reflections.append(
                MetaReflection(
                    id=f"long-behavior-risk-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="longitudinal",
                    level=ReflectionLevel.REFLECTION,
                    scope=ReflectionScope.TECHNICAL_DEBT,
                    impact=ReflectionImpact.CRITICAL,
                    title="Rising Behavior Risk Scores",
                    content=f"Average risk score increased from {first_avg_risk:.2f} to {last_avg_risk:.2f} (+{((last_avg_risk/first_avg_risk)-1)*100:.1f}%)",
                    evidence=[ReflectionEvidence(type="trend", source="behavior_risk", value=last_avg_risk)],
                    recommendations=[
                        "Investigate severity escalation in violations",
                        "Check if refactoring is introducing high-risk changes",
                        "Consider rolling back recent changes",
                    ],
                )
            )

        # 3. Analyze Violation Pattern Trends
        first_violations = []
        last_violations = []
        for check in first_half:
            first_violations.extend(check.violations)
        for check in last_half:
            last_violations.extend(check.violations)

        if first_violations and last_violations:
            first_codes = Counter(v.code for v in first_violations)
            last_codes = Counter(v.code for v in last_violations)

            # Detect emerging violation types (new in last half)
            emerging = set(last_codes.keys()) - set(first_codes.keys())
            if emerging:
                reflections.append(
                    MetaReflection(
                        id=f"long-behavior-emerging-{uuid.uuid4()}",
                        timestamp=datetime.now().isoformat(),
                        project_id="longitudinal",
                        level=ReflectionLevel.REFLECTION,
                        scope=ReflectionScope.PATTERN,
                        impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                        title="Emerging Behavior Violation Patterns",
                        content=f"Detected {len(emerging)} new violation types in recent checks: {', '.join(list(emerging)[:3])}",
                        evidence=[
                            ReflectionEvidence(type="pattern", source="behavior_violations", value=list(emerging))
                        ],
                        recommendations=[
                            "Investigate what code changes introduced new violation types",
                            "Update behavior contracts if new patterns are expected",
                            "Implement preventive measures for emerging violations",
                        ],
                    )
                )

            # Detect escalating violation types (frequency increased >50%)
            escalating = []
            for code in set(first_codes.keys()) & set(last_codes.keys()):
                first_count = first_codes[code]
                last_count = last_codes[code]
                if last_count > first_count * 1.5:
                    escalating.append((code, first_count, last_count))

            if escalating:
                top_escalation = max(escalating, key=lambda x: x[2] / x[1])
                reflections.append(
                    MetaReflection(
                        id=f"long-behavior-escalate-{uuid.uuid4()}",
                        timestamp=datetime.now().isoformat(),
                        project_id="longitudinal",
                        level=ReflectionLevel.REFLECTION,
                        scope=ReflectionScope.PATTERN,
                        impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                        title="Escalating Behavior Violation Frequency",
                        content=f"Violation '{top_escalation[0]}' frequency increased from {top_escalation[1]} to {top_escalation[2]} (+{((top_escalation[2]/top_escalation[1])-1)*100:.0f}%)",
                        evidence=[
                            ReflectionEvidence(type="trend", source="behavior_violations", value=top_escalation[2])
                        ],
                        recommendations=[
                            f"Focus on resolving {top_escalation[0]} violations as priority",
                            "Check if recent changes amplified existing issues",
                            "Implement automated checks to prevent recurrence",
                        ],
                    )
                )

        log.debug(f"Behavior trend analysis generated {len(reflections)} reflections from {len(checks)} checks")
        return reflections
