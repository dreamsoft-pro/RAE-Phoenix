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
Tests for Cost Policy enforcement.
"""
from unittest.mock import MagicMock, patch

import pytest

from feniks.core.models.domain import CostProfile, SessionSummary
from feniks.core.policies.cost_policy import CostPolicyConfig, CostPolicyEnforcer


@pytest.fixture
def enforcer():
    """Create a CostPolicyEnforcer with default config."""
    config = CostPolicyConfig(max_session_cost=1.0, alert_threshold_percent=80.0, monthly_budget=100.0)
    return CostPolicyEnforcer(config)


def test_cost_policy_max_session_exceeded(enforcer):
    """Test dla przekroczenia max session cost."""
    session = SessionSummary(
        session_id="expensive-session",
        duration=120.0,
        success=True,
        cost_profile=CostProfile(
            total_tokens=100000, cost_usd=1.5, breakdown={"input": 0.5, "output": 1.0}  # Powyżej limitu 1.0
        ),
    )

    reflections = enforcer.check_session_cost(session)

    assert len(reflections) > 0, "Should generate reflection for exceeded cost"
    assert reflections[0].title == "Max Session Cost Exceeded"
    assert reflections[0].impact.value == "critical"
    assert "1.50" in reflections[0].content or "1.5" in reflections[0].content


def test_cost_policy_within_limits(enforcer):
    """Test dla sesji w ramach limitu kosztów."""
    session = SessionSummary(
        session_id="cheap-session",
        duration=30.0,
        success=True,
        cost_profile=CostProfile(
            total_tokens=5000, cost_usd=0.15, breakdown={"input": 0.05, "output": 0.10}  # Poniżej limitu 1.0
        ),
    )

    reflections = enforcer.check_session_cost(session)

    # Nie powinno być refleksji o przekroczeniu kosztu
    cost_exceeded = [r for r in reflections if "Max Session Cost Exceeded" in r.title]
    assert len(cost_exceeded) == 0, "Should not generate reflection for cost within limits"


def test_cost_policy_no_cost_profile(enforcer):
    """Test dla sesji bez cost profile."""
    session = SessionSummary(session_id="no-cost", duration=10.0, success=True, cost_profile=None)

    reflections = enforcer.check_session_cost(session)

    assert len(reflections) == 0, "Should not generate reflections without cost profile"


@patch("feniks.core.policies.cost_policy.get_cost_controller")
def test_budget_alert_threshold_warning(mock_get_controller, enforcer):
    """Test dla osiągnięcia progu ostrzeżenia budżetu (80%)."""
    mock_controller = MagicMock()
    mock_budget = MagicMock()
    mock_budget.utilization = 85.0  # 85% wykorzystania
    mock_controller.get_budget.return_value = mock_budget
    mock_get_controller.return_value = mock_controller
    enforcer.controller = mock_controller  # Explicitly inject mock

    reflections = enforcer.check_budget_health("test-project")

    assert len(reflections) > 0, "Should generate reflection for budget threshold"
    assert reflections[0].title == "Budget Threshold Reached"
    assert reflections[0].impact.value == "refactor-recommended"  # Nie critical, bo < 95%


@patch("feniks.core.policies.cost_policy.get_cost_controller")
def test_budget_alert_threshold_critical(mock_get_controller, enforcer):
    """Test dla osiągnięcia krytycznego progu budżetu (95%+)."""
    mock_controller = MagicMock()
    mock_budget = MagicMock()
    mock_budget.utilization = 96.0  # 96% wykorzystania
    mock_controller.get_budget.return_value = mock_budget
    mock_get_controller.return_value = mock_controller
    enforcer.controller = mock_controller  # Explicitly inject mock

    reflections = enforcer.check_budget_health("test-project")

    assert len(reflections) > 0, "Should generate reflection for critical budget"
    assert reflections[0].title == "Budget Threshold Reached"
    assert reflections[0].impact.value == "critical"  # Critical, bo >= 95%


@patch("feniks.core.policies.cost_policy.get_cost_controller")
def test_budget_health_no_budget(mock_get_controller, enforcer):
    """Test dla projektu bez zdefiniowanego budżetu."""
    mock_controller = MagicMock()
    mock_controller.get_budget.return_value = None
    mock_get_controller.return_value = mock_controller
    enforcer.controller = mock_controller  # Explicitly inject mock

    reflections = enforcer.check_budget_health("no-budget-project")

    assert len(reflections) == 0, "Should not generate reflections without budget"


def test_cost_policy_edge_case_exact_limit(enforcer):
    """Test dla sesji z kosztem równym limitowi."""
    session = SessionSummary(
        session_id="exact-limit",
        duration=60.0,
        success=True,
        cost_profile=CostProfile(total_tokens=50000, cost_usd=1.0, breakdown={}),  # Dokładnie limit
    )

    reflections = enforcer.check_session_cost(session)

    # Nie powinno być refleksji, bo limit to ">"
    cost_exceeded = [r for r in reflections if "Max Session Cost Exceeded" in r.title]
    assert len(cost_exceeded) == 0, "Should not trigger for cost equal to limit"


def test_cost_policy_recommendations():
    """Test dla treści rekomendacji w refleksjach."""
    config = CostPolicyConfig(max_session_cost=0.5)
    enforcer = CostPolicyEnforcer(config)

    session = SessionSummary(
        session_id="high-cost",
        duration=180.0,
        success=True,
        cost_profile=CostProfile(total_tokens=200000, cost_usd=3.0),
    )

    reflections = enforcer.check_session_cost(session)

    assert len(reflections) > 0
    assert len(reflections[0].recommendations) > 0
    # Sprawdź czy rekomendacje są sensowne
    recs_text = " ".join(reflections[0].recommendations).lower()
    assert "prompt" in recs_text or "context" in recs_text or "usage" in recs_text
