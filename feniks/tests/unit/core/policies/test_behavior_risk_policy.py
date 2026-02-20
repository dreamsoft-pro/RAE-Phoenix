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
Unit tests for Behavior Risk Policies.
"""
from datetime import datetime

import pytest

from feniks.core.models.behavior import BehaviorChecksSummary
from feniks.core.models.domain import FeniksReport, SessionSummary
from feniks.core.policies.behavior_risk_policy import (
    MaxBehaviorRiskPolicy,
    MinimumCoverageBehaviorPolicy,
    PolicyEvaluationResult,
    ZeroRegressionPolicy,
)


@pytest.fixture
def base_report():
    """Base FeniksReport without behavior checks."""
    return FeniksReport(
        project_id="test-project",
        timestamp=datetime.now().isoformat(),
        summary=SessionSummary(session_id="test-session", duration=100.0, success=True, reasoning_traces=[]),
        metrics={},
        recommendations=[],
    )


# ============================================================================
# MaxBehaviorRiskPolicy Tests
# ============================================================================


def test_max_behavior_risk_policy_no_checks_required(base_report):
    """Test policy when checks not required and no checks performed."""
    policy = MaxBehaviorRiskPolicy(require_checks=False)
    result = policy.evaluate(base_report)

    assert result.passed is True
    assert "not required" in result.reason.lower()


def test_max_behavior_risk_policy_no_checks_but_required(base_report):
    """Test policy failure when checks required but not performed."""
    policy = MaxBehaviorRiskPolicy(require_checks=True)
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "no behavior checks" in result.reason.lower()
    assert result.severity == "critical"


def test_max_behavior_risk_policy_low_risk_passes(base_report):
    """Test policy passes with low risk score."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=5,
        total_snapshots_checked=20,
        total_passed=20,
        total_failed=0,
        max_risk_score=0.15,  # Low risk
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5)
    result = policy.evaluate(base_report)

    assert result.passed is True
    assert "within acceptable limits" in result.reason.lower()


def test_max_behavior_risk_policy_high_risk_fails(base_report):
    """Test policy fails with high risk score."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=5,
        total_snapshots_checked=20,
        total_passed=15,
        total_failed=5,
        max_risk_score=0.85,  # High risk
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5)
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "0.85" in result.reason
    assert "exceeds" in result.reason.lower()
    assert result.severity in ["critical", "high"]


def test_max_behavior_risk_policy_exact_threshold(base_report):
    """Test policy at exact risk threshold."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=5,
        total_snapshots_checked=20,
        total_passed=18,
        total_failed=2,
        max_risk_score=0.5,  # Exactly at threshold
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5, max_failed_scenarios=2)
    result = policy.evaluate(base_report)

    # Should pass - threshold is inclusive (not exceeded)
    assert result.passed is True


def test_max_behavior_risk_policy_failed_scenarios_exceeds(base_report):
    """Test policy fails when too many scenarios fail."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10,
        total_snapshots_checked=50,
        total_passed=45,
        total_failed=5,  # 5 failed > threshold of 2
        max_risk_score=0.3,  # Risk score is fine
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5, max_failed_scenarios=2)
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "5" in result.reason
    assert "failed" in result.reason.lower()
    assert result.severity == "high"


def test_max_behavior_risk_policy_failed_scenarios_at_threshold(base_report):
    """Test policy passes when failed scenarios at threshold."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10,
        total_snapshots_checked=50,
        total_passed=48,
        total_failed=2,  # Exactly at threshold
        max_risk_score=0.2,
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5, max_failed_scenarios=2)
    result = policy.evaluate(base_report)

    # Should pass - at threshold
    assert result.passed is True


def test_max_behavior_risk_policy_zero_tolerance(base_report):
    """Test policy with zero tolerance for failures."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10,
        total_snapshots_checked=50,
        total_passed=49,
        total_failed=1,  # Even 1 failure is too many
        max_risk_score=0.1,
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5, max_failed_scenarios=0)
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "1" in result.reason


def test_max_behavior_risk_policy_check_violations_integration(base_report):
    """Test check_violations method integration with reflection system."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=5,
        total_snapshots_checked=20,
        total_passed=15,
        total_failed=5,
        max_risk_score=0.9,  # Critical risk
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5)
    reflections = policy.check_violations(base_report)

    assert len(reflections) == 1
    reflection = reflections[0]
    assert reflection.title == "Behavior Risk Policy Violation"
    assert reflection.impact.value == "critical"
    assert "0.9" in reflection.content.lower() or "0.90" in reflection.content.lower()
    assert len(reflection.recommendations) > 0


def test_max_behavior_risk_policy_check_violations_passes(base_report):
    """Test check_violations returns empty list when policy passes."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=5, total_snapshots_checked=20, total_passed=20, total_failed=0, max_risk_score=0.1
    )

    policy = MaxBehaviorRiskPolicy(max_risk_score=0.5)
    reflections = policy.check_violations(base_report)

    assert len(reflections) == 0


# ============================================================================
# MinimumCoverageBehaviorPolicy Tests
# ============================================================================


def test_minimum_coverage_policy_no_checks(base_report):
    """Test minimum coverage policy fails with no checks."""
    policy = MinimumCoverageBehaviorPolicy(min_scenarios=5)
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "no behavior checks" in result.reason.lower()
    assert "5" in result.reason


def test_minimum_coverage_policy_insufficient_scenarios(base_report):
    """Test policy fails with insufficient scenario coverage."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=3,  # Only 3, need 5
        total_snapshots_checked=10,
        total_passed=10,
        total_failed=0,
        max_risk_score=0.0,
    )

    policy = MinimumCoverageBehaviorPolicy(min_scenarios=5)
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "3" in result.reason
    assert "5" in result.reason


def test_minimum_coverage_policy_sufficient_scenarios(base_report):
    """Test policy passes with sufficient scenario coverage."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10,  # More than required 5
        total_snapshots_checked=50,
        total_passed=45,
        total_failed=5,
        max_risk_score=0.3,
    )

    policy = MinimumCoverageBehaviorPolicy(min_scenarios=5)
    result = policy.evaluate(base_report)

    assert result.passed is True
    assert "10" in result.reason
    assert "coverage requirement met" in result.reason.lower()


def test_minimum_coverage_policy_exact_threshold(base_report):
    """Test policy passes at exact minimum threshold."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=5,  # Exactly at threshold
        total_snapshots_checked=20,
        total_passed=20,
        total_failed=0,
        max_risk_score=0.0,
    )

    policy = MinimumCoverageBehaviorPolicy(min_scenarios=5)
    result = policy.evaluate(base_report)

    assert result.passed is True


# ============================================================================
# ZeroRegressionPolicy Tests
# ============================================================================


def test_zero_regression_policy_no_checks(base_report):
    """Test zero regression policy fails with no checks."""
    policy = ZeroRegressionPolicy()
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "no behavior checks" in result.reason.lower()
    assert result.severity == "critical"


def test_zero_regression_policy_perfect_score(base_report):
    """Test zero regression policy passes with perfect results."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10,
        total_snapshots_checked=50,
        total_passed=50,
        total_failed=0,
        max_risk_score=0.0,  # Perfect - no risk
    )

    policy = ZeroRegressionPolicy()
    result = policy.evaluate(base_report)

    assert result.passed is True
    assert "zero regression policy satisfied" in result.reason.lower()
    assert "10" in result.reason


def test_zero_regression_policy_one_failure(base_report):
    """Test zero regression policy fails with even one failure."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10,
        total_snapshots_checked=50,
        total_passed=49,
        total_failed=1,  # Just one failure
        max_risk_score=0.2,
    )

    policy = ZeroRegressionPolicy()
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "1" in result.reason
    assert "failed" in result.reason.lower()
    assert result.severity == "critical"


def test_zero_regression_policy_any_risk_score(base_report):
    """Test zero regression policy fails with any risk score > 0."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10,
        total_snapshots_checked=50,
        total_passed=50,
        total_failed=0,  # No failures
        max_risk_score=0.1,  # But non-zero risk
    )

    policy = ZeroRegressionPolicy()
    result = policy.evaluate(base_report)

    assert result.passed is False
    assert "0.1" in result.reason or "0.10" in result.reason
    assert "risk" in result.reason.lower()
    assert result.severity == "critical"


# ============================================================================
# Policy Combinations and Edge Cases
# ============================================================================


def test_multiple_policies_combined(base_report):
    """Test combining multiple policies."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=10, total_snapshots_checked=50, total_passed=45, total_failed=5, max_risk_score=0.4
    )

    # All three policies
    max_risk_policy = MaxBehaviorRiskPolicy(max_risk_score=0.5, max_failed_scenarios=5)
    min_coverage_policy = MinimumCoverageBehaviorPolicy(min_scenarios=5)
    zero_regression_policy = ZeroRegressionPolicy()

    # MaxBehaviorRiskPolicy should pass (within limits)
    assert max_risk_policy.evaluate(base_report).passed is True

    # MinimumCoverageBehaviorPolicy should pass (10 >= 5)
    assert min_coverage_policy.evaluate(base_report).passed is True

    # ZeroRegressionPolicy should fail (has failures and risk)
    assert zero_regression_policy.evaluate(base_report).passed is False


def test_policy_with_empty_summary_fields(base_report):
    """Test policies handle edge case of zero scenarios checked."""
    base_report.behavior_checks_summary = BehaviorChecksSummary(
        total_scenarios_checked=0, total_snapshots_checked=0, total_passed=0, total_failed=0, max_risk_score=0.0
    )

    # Should fail minimum coverage
    min_coverage = MinimumCoverageBehaviorPolicy(min_scenarios=1)
    assert min_coverage.evaluate(base_report).passed is False

    # ZeroRegressionPolicy should technically pass (no failures)
    zero_regression = ZeroRegressionPolicy()
    result = zero_regression.evaluate(base_report)
    assert result.passed is True  # 0 failed, 0 risk = pass


def test_policy_evaluation_result_structure():
    """Test PolicyEvaluationResult model structure."""
    result = PolicyEvaluationResult(passed=False, reason="Test reason", severity="high")

    assert result.passed is False
    assert result.reason == "Test reason"
    assert result.severity == "high"

    # Test without severity
    result2 = PolicyEvaluationResult(passed=True, reason="All good")
    assert result2.passed is True
    assert result2.severity is None
