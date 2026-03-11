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
Post-Mortem Analysis Loop - analyzes completed sessions to identify failures and inefficiencies.
"""
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

log = get_logger("core.reflection.post_mortem")


class PostMortemAnalyzer:
    """
    Analyzes individual sessions (Post-Mortem) to generate insights and recommendations.
    """

    def analyze_session(
        self, session_summary: SessionSummary, behavior_checks: Optional[List[BehaviorCheckResult]] = None
    ) -> List[MetaReflection]:
        """
        Analyze a single session and generate meta-reflections.

        Args:
            session_summary: The session summary to analyze.
            behavior_checks: Optional list of behavior check results for this session.

        Returns:
            List[MetaReflection]: List of generated meta-reflections.
        """
        log.info(f"Starting Post-Mortem analysis for session: {session_summary.session_id}")
        reflections = []

        # 1. Analyze Success/Failure
        if not session_summary.success:
            reflections.append(self._create_failure_reflection(session_summary))

        # 2. Analyze Cost
        if session_summary.cost_profile:
            cost_ref = self._analyze_cost(session_summary)
            if cost_ref:
                reflections.append(cost_ref)

        # 3. Analyze Reasoning Traces (e.g. loops, empty thoughts)
        trace_refs = self._analyze_traces(session_summary)
        reflections.extend(trace_refs)

        # 4. Analyze Behavior Checks (Legacy Behavior Guard integration)
        if behavior_checks:
            behavior_refs = self._analyze_behavior_checks(behavior_checks)
            reflections.extend(behavior_refs)

        log.info(f"Post-Mortem analysis complete. Generated {len(reflections)} reflections.")
        return reflections

    def _create_failure_reflection(self, session: SessionSummary) -> MetaReflection:
        return MetaReflection(
            id=f"pm-fail-{uuid.uuid4()}",
            timestamp=datetime.now().isoformat(),
            project_id="post-mortem",  # Context dependent, maybe passed in
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.TECHNICAL_DEBT,  # Or PROCESS
            impact=ReflectionImpact.CRITICAL,
            title="Session Failure Detected",
            content=f"Session {session.session_id} marked as failed.",
            evidence=[ReflectionEvidence(type="status", source="session_summary", value=False)],
            recommendations=["Investigate logs for errors", "Check reasoning trace for abandonment"],
        )

    def _analyze_cost(self, session: SessionSummary) -> Optional[MetaReflection]:
        # Simple heuristic: Cost > $0.50 is high for a single session (example threshold)
        cost_threshold = 0.50
        if session.cost_profile.cost_usd > cost_threshold:
            return MetaReflection(
                id=f"pm-cost-{uuid.uuid4()}",
                timestamp=datetime.now().isoformat(),
                project_id="post-mortem",
                level=ReflectionLevel.OBSERVATION,
                scope=ReflectionScope.TECHNICAL_DEBT,
                impact=ReflectionImpact.MONITOR,
                title="High Session Cost",
                content=f"Session cost ${session.cost_profile.cost_usd:.2f} exceeded threshold ${cost_threshold:.2f}",
                evidence=[
                    ReflectionEvidence(type="metric", source="cost_profile", value=session.cost_profile.cost_usd)
                ],
                recommendations=["Review prompt verbosity", "Check for reasoning loops"],
            )
        return None

    def _analyze_traces(self, session: SessionSummary) -> List[MetaReflection]:
        reflections = []
        traces = session.reasoning_traces
        if not traces:
            return reflections

        # Check for empty thoughts
        empty_thoughts = [t for t in traces if not t.thought.strip()]
        if empty_thoughts:
            reflections.append(
                MetaReflection(
                    id=f"pm-empty-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="post-mortem",
                    level=ReflectionLevel.REFLECTION,
                    scope=ReflectionScope.PATTERN,
                    impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                    title="Empty Reasoning Steps",
                    content=f"Found {len(empty_thoughts)} steps with empty reasoning thoughts.",
                    recommendations=["Improve prompt instructions to enforce reasoning before action"],
                )
            )

        # Detect simple repetitions (loops) - consecutive identical actions
        for i in range(1, len(traces)):
            if traces[i].action == traces[i - 1].action and traces[i].action.strip():
                reflections.append(
                    MetaReflection(
                        id=f"pm-loop-{uuid.uuid4()}",
                        timestamp=datetime.now().isoformat(),
                        project_id="post-mortem",
                        level=ReflectionLevel.META_REFLECTION,
                        scope=ReflectionScope.PATTERN,
                        impact=ReflectionImpact.CRITICAL,
                        title="Reasoning Loop Detected",
                        content=f"Identical action repeated at step {traces[i].step_id}: {traces[i].action}",
                        recommendations=[
                            "Implement loop detection mechanism in agent core",
                            "Increase penalties for repeated actions",
                        ],
                    )
                )
                break  # Report one loop per session to avoid noise

        return reflections

    def _analyze_behavior_checks(self, checks: List[BehaviorCheckResult]) -> List[MetaReflection]:
        """
        Analyze behavior check results (Legacy Behavior Guard integration).

        Generates reflections for:
        - Failed behavior checks (regression risks)
        - High-risk violations (critical/high severity)
        - Patterns in violation types

        Args:
            checks: List of behavior check results

        Returns:
            List of meta-reflections for behavior violations
        """
        reflections = []

        # Count failures and high-risk checks
        failed_checks = [c for c in checks if not c.passed]
        high_risk_checks = [c for c in checks if c.risk_score >= 0.7]

        # Generate reflection for failed checks
        if failed_checks:
            total_violations = sum(len(c.violations) for c in failed_checks)
            avg_risk = sum(c.risk_score for c in failed_checks) / len(failed_checks)

            reflections.append(
                MetaReflection(
                    id=f"pm-behavior-fail-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="post-mortem",
                    level=ReflectionLevel.REFLECTION,
                    scope=ReflectionScope.TECHNICAL_DEBT,
                    impact=ReflectionImpact.CRITICAL if avg_risk >= 0.7 else ReflectionImpact.REFACTOR_RECOMMENDED,
                    title="Behavior Regression Detected",
                    content=f"Found {len(failed_checks)} failed behavior checks with {total_violations} violations (avg risk: {avg_risk:.2f})",
                    evidence=[ReflectionEvidence(type="metric", source="behavior_checks", value=len(failed_checks))],
                    recommendations=[
                        "Review behavior violations before deployment",
                        "Investigate root cause of behavioral changes",
                        "Update contracts if behavior changes are intentional",
                    ],
                )
            )

        # Analyze violation patterns
        all_violations = []
        for check in checks:
            all_violations.extend(check.violations)

        if all_violations:
            # Count violation types
            violation_codes = Counter(v.code for v in all_violations)
            most_common = violation_codes.most_common(3)

            # Generate reflection for common violation patterns
            if most_common[0][1] >= 3:  # At least 3 occurrences
                reflections.append(
                    MetaReflection(
                        id=f"pm-behavior-pattern-{uuid.uuid4()}",
                        timestamp=datetime.now().isoformat(),
                        project_id="post-mortem",
                        level=ReflectionLevel.META_REFLECTION,
                        scope=ReflectionScope.PATTERN,
                        impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                        title="Repeated Behavior Violation Pattern",
                        content=f"Violation '{most_common[0][0]}' occurred {most_common[0][1]} times across scenarios",
                        evidence=[
                            ReflectionEvidence(type="pattern", source="behavior_violations", value=most_common[0][0])
                        ],
                        recommendations=[
                            f"Investigate systematic cause of {most_common[0][0]} violations",
                            "Check if refactoring introduced unintended side effects",
                            "Consider updating test scenarios if pattern is expected",
                        ],
                    )
                )

        # High-risk warning
        if high_risk_checks:
            critical_violations = []
            for check in high_risk_checks:
                critical_violations.extend([v for v in check.violations if v.severity in ["critical", "high"]])

            if critical_violations:
                reflections.append(
                    MetaReflection(
                        id=f"pm-behavior-risk-{uuid.uuid4()}",
                        timestamp=datetime.now().isoformat(),
                        project_id="post-mortem",
                        level=ReflectionLevel.REFLECTION,
                        scope=ReflectionScope.TECHNICAL_DEBT,
                        impact=ReflectionImpact.CRITICAL,
                        title="High-Risk Behavior Changes Detected",
                        content=f"Found {len(high_risk_checks)} checks with risk score >= 0.7, including {len(critical_violations)} critical/high severity violations",
                        evidence=[
                            ReflectionEvidence(type="metric", source="behavior_risk", value=len(high_risk_checks))
                        ],
                        recommendations=[
                            "Block deployment until violations are resolved",
                            "Perform manual testing of affected scenarios",
                            "Review changes with domain experts",
                        ],
                    )
                )

        log.debug(f"Behavior analysis generated {len(reflections)} reflections from {len(checks)} checks")
        return reflections
