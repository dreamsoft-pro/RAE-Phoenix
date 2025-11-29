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
Behavior Risk Policies for Legacy Behavior Guard.

These policies enforce acceptable risk levels when refactoring legacy systems
without traditional tests. They analyze BehaviorCheckResult data and prevent
merge/deployment when behavior regressions exceed thresholds.
"""
from typing import Optional

from pydantic import BaseModel

from feniks.config.settings import settings
from feniks.core.models.domain import FeniksReport
from feniks.core.models.types import MetaReflection, ReflectionImpact


class PolicyEvaluationResult(BaseModel):
    """
    Result of policy evaluation.
    """

    passed: bool
    reason: str
    severity: Optional[str] = None  # For compatibility with reflection system


class MaxBehaviorRiskPolicy:
    """
    Policy that prevents deployment/merge if behavior risk exceeds acceptable thresholds.

    Checks:
    - max_risk_score: Maximum acceptable risk score (0.0-1.0)
    - max_failed_scenarios: Maximum number of failed behavior scenarios
    - require_checks: Whether behavior checks are required at all

    Risk Score Interpretation:
    - 0.0-0.3: Low risk (minor differences, acceptable)
    - 0.3-0.7: Medium risk (notable changes, review recommended)
    - 0.7-1.0: High/Critical risk (major regressions, blocking)

    Usage:
        policy = MaxBehaviorRiskPolicy(max_risk_score=0.5, max_failed_scenarios=2)
        result = policy.evaluate(feniks_report)
        if not result.passed:
            print(f"Policy failed: {result.reason}")
    """

    def __init__(self, max_risk_score: float = 0.5, max_failed_scenarios: int = 0, require_checks: bool = True):
        """
        Initialize MaxBehaviorRiskPolicy.

        Args:
            max_risk_score: Maximum acceptable risk score (default: 0.5 = medium risk)
            max_failed_scenarios: Maximum number of scenarios that can fail (default: 0)
            require_checks: Whether behavior checks are mandatory (default: True)
        """
        self.max_risk_score = max_risk_score
        self.max_failed_scenarios = max_failed_scenarios
        self.require_checks = require_checks

    def evaluate(self, report: FeniksReport) -> PolicyEvaluationResult:
        """
        Evaluate FeniksReport against behavior risk policy.

        Args:
            report: FeniksReport containing behavior checks summary

        Returns:
            PolicyEvaluationResult with pass/fail and reason
        """
        summary = report.behavior_checks_summary

        # Check if behavior checks were performed
        if not summary:
            if self.require_checks:
                return PolicyEvaluationResult(
                    passed=False,
                    reason="No behavior checks were executed. Behavior checks are required by policy.",
                    severity="critical",
                )
            else:
                # Checks not required, policy passes
                return PolicyEvaluationResult(passed=True, reason="Behavior checks not required by policy.")

        # Check max risk score threshold
        if summary.max_risk_score > self.max_risk_score:
            return PolicyEvaluationResult(
                passed=False,
                reason=(
                    f"Behavior risk score {summary.max_risk_score:.2f} exceeds "
                    f"threshold {self.max_risk_score:.2f}. "
                    f"Review behavior violations before proceeding."
                ),
                severity="critical" if summary.max_risk_score >= 0.7 else "high",
            )

        # Check failed scenarios threshold
        if summary.total_failed > self.max_failed_scenarios:
            return PolicyEvaluationResult(
                passed=False,
                reason=(
                    f"{summary.total_failed} behavior scenario(s) failed "
                    f"(threshold: {self.max_failed_scenarios}). "
                    f"Fix regressions before merge."
                ),
                severity="high",
            )

        # All checks passed
        return PolicyEvaluationResult(
            passed=True,
            reason=(
                f"Behavior risk within acceptable limits. "
                f"Risk score: {summary.max_risk_score:.2f}, "
                f"Failed scenarios: {summary.total_failed}/{summary.total_scenarios_checked}"
            ),
        )

    def check_violations(self, report: FeniksReport) -> list[MetaReflection]:
        """
        Check for policy violations and return as MetaReflections.

        This method integrates with Feniks reflection system, converting
        policy violations into actionable meta-reflections.

        Args:
            report: FeniksReport containing behavior checks summary

        Returns:
            List of MetaReflections for policy violations (empty if passed)
        """
        result = self.evaluate(report)
        reflections = []

        if not result.passed:
            # Determine impact level based on severity
            if result.severity == "critical":
                impact = ReflectionImpact.CRITICAL
            elif result.severity == "high":
                impact = ReflectionImpact.REFACTOR_RECOMMENDED
            else:
                impact = ReflectionImpact.WARNING

            # Create meta-reflection for policy violation
            import uuid
            from datetime import datetime

            from feniks.core.models.types import ReflectionLevel, ReflectionScope

            reflection = MetaReflection(
                id=str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                project_id=report.project_id,
                level=ReflectionLevel.META_REFLECTION,
                scope=ReflectionScope.SYSTEM,
                title="Behavior Risk Policy Violation",
                content=result.reason,
                impact=impact,
                metadata={
                    "policy": "MaxBehaviorRiskPolicy",
                    "max_risk_score": self.max_risk_score,
                    "max_failed_scenarios": self.max_failed_scenarios,
                    "actual_risk_score": (
                        report.behavior_checks_summary.max_risk_score if report.behavior_checks_summary else None
                    ),
                    "actual_failed": (
                        report.behavior_checks_summary.total_failed if report.behavior_checks_summary else None
                    ),
                },
                recommendations=[
                    "Review behavior violations in the report",
                    "Fix failing scenarios before proceeding with merge",
                    "Consider rolling back changes if regressions are critical",
                    "Run manual tests on high-risk scenarios",
                ],
            )
            reflections.append(reflection)

        return reflections


class MinimumCoverageBehaviorPolicy:
    """
    Policy that requires minimum number of behavior scenarios to be checked.

    Ensures that refactoring is covered by sufficient behavior tests.
    Useful for preventing "silent" refactorings without validation.

    Usage:
        policy = MinimumCoverageBehaviorPolicy(min_scenarios=5)
        result = policy.evaluate(feniks_report)
    """

    def __init__(self, min_scenarios: int = 1):
        """
        Initialize MinimumCoverageBehaviorPolicy.

        Args:
            min_scenarios: Minimum number of scenarios that must be checked
        """
        self.min_scenarios = min_scenarios

    def evaluate(self, report: FeniksReport) -> PolicyEvaluationResult:
        """
        Evaluate minimum coverage requirement.

        Args:
            report: FeniksReport containing behavior checks summary

        Returns:
            PolicyEvaluationResult with pass/fail and reason
        """
        summary = report.behavior_checks_summary

        if not summary:
            return PolicyEvaluationResult(
                passed=False,
                reason=f"No behavior checks executed. Minimum {self.min_scenarios} scenario(s) required.",
                severity="high",
            )

        if summary.total_scenarios_checked < self.min_scenarios:
            return PolicyEvaluationResult(
                passed=False,
                reason=(
                    f"Only {summary.total_scenarios_checked} scenario(s) checked. "
                    f"Minimum {self.min_scenarios} required for adequate coverage."
                ),
                severity="medium",
            )

        return PolicyEvaluationResult(
            passed=True, reason=f"Coverage requirement met: {summary.total_scenarios_checked} scenario(s) checked."
        )


class ZeroRegressionPolicy:
    """
    Strict policy that requires 100% of behavior scenarios to pass.

    No regressions allowed - all scenarios must pass without violations.
    Suitable for critical production systems or stable legacy code.

    Usage:
        policy = ZeroRegressionPolicy()
        result = policy.evaluate(feniks_report)
    """

    def evaluate(self, report: FeniksReport) -> PolicyEvaluationResult:
        """
        Evaluate zero regression requirement.

        Args:
            report: FeniksReport containing behavior checks summary

        Returns:
            PolicyEvaluationResult with pass/fail and reason
        """
        summary = report.behavior_checks_summary

        if not summary:
            return PolicyEvaluationResult(
                passed=False,
                reason="No behavior checks executed. Zero regression policy requires checks.",
                severity="critical",
            )

        if summary.total_failed > 0:
            return PolicyEvaluationResult(
                passed=False,
                reason=(
                    f"Zero regression policy violated. "
                    f"{summary.total_failed} scenario(s) failed. "
                    f"All scenarios must pass without violations."
                ),
                severity="critical",
            )

        if summary.max_risk_score > 0.0:
            return PolicyEvaluationResult(
                passed=False,
                reason=(
                    f"Zero regression policy violated. "
                    f"Risk score {summary.max_risk_score:.2f} detected. "
                    f"All scenarios must have 0.0 risk."
                ),
                severity="critical",
            )

        return PolicyEvaluationResult(
            passed=True,
            reason=f"Zero regression policy satisfied. All {summary.total_scenarios_checked} scenario(s) passed.",
        )


# ============================================================================
# Factory Functions (Settings Integration)
# ============================================================================


def create_max_behavior_risk_policy(
    max_risk_score: Optional[float] = None,
    max_failed_scenarios: Optional[int] = None,
    require_checks: Optional[bool] = None,
) -> MaxBehaviorRiskPolicy:
    """
    Create MaxBehaviorRiskPolicy using settings defaults.

    Args:
        max_risk_score: Override settings.behavior_max_risk_threshold
        max_failed_scenarios: Override default (0)
        require_checks: Override default (True)

    Returns:
        MaxBehaviorRiskPolicy instance
    """
    return MaxBehaviorRiskPolicy(
        max_risk_score=max_risk_score if max_risk_score is not None else settings.behavior_max_risk_threshold,
        max_failed_scenarios=max_failed_scenarios if max_failed_scenarios is not None else 0,
        require_checks=require_checks if require_checks is not None else True,
    )


def create_minimum_coverage_policy(min_scenarios: Optional[int] = None) -> MinimumCoverageBehaviorPolicy:
    """
    Create MinimumCoverageBehaviorPolicy using settings defaults.

    Args:
        min_scenarios: Override settings.behavior_min_coverage_scenarios

    Returns:
        MinimumCoverageBehaviorPolicy instance
    """
    return MinimumCoverageBehaviorPolicy(
        min_scenarios=min_scenarios if min_scenarios is not None else settings.behavior_min_coverage_scenarios
    )


def create_zero_regression_policy() -> ZeroRegressionPolicy:
    """
    Create ZeroRegressionPolicy.

    Returns:
        ZeroRegressionPolicy instance
    """
    return ZeroRegressionPolicy()
