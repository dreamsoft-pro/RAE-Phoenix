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
Unit tests for Behavior Contract Models.
"""
from datetime import datetime

from feniks.core.models.behavior import (  # Input models; Criteria; Scenario; Observations; Violations and Snapshots; Contracts; Check result
    APIRequest,
    BehaviorCheckResult,
    BehaviorChecksSummary,
    BehaviorContract,
    BehaviorInput,
    BehaviorScenario,
    BehaviorSnapshot,
    BehaviorSuccessCriteria,
    BehaviorViolation,
    CLICommand,
    DOMContract,
    DOMCriteria,
    HTTPContract,
    HTTPCriteria,
    LogContract,
    LogCriteria,
    ObservedDOM,
    ObservedHTTP,
    ObservedLogs,
    UIAction,
)

# ============================================================================
# Input Models Tests
# ============================================================================


def test_ui_action_click():
    """Test UI action for click event."""
    action = UIAction(action_type="click", selector="#submit-button")
    assert action.action_type == "click"
    assert action.selector == "#submit-button"
    assert action.text is None


def test_ui_action_type_text():
    """Test UI action for typing text."""
    action = UIAction(action_type="type", selector="input[name='email']", text="user@example.com")
    assert action.action_type == "type"
    assert action.text == "user@example.com"


def test_ui_action_navigate():
    """Test UI action for navigation."""
    action = UIAction(action_type="navigate", url="/dashboard")
    assert action.action_type == "navigate"
    assert action.url == "/dashboard"


def test_api_request_post():
    """Test API request specification for POST."""
    request = APIRequest(
        method="POST",
        url="/api/orders",
        headers={"Authorization": "Bearer token123"},
        body={"product_id": 123, "quantity": 2},
    )
    assert request.method == "POST"
    assert request.url == "/api/orders"
    assert request.headers["Authorization"] == "Bearer token123"
    assert request.body["product_id"] == 123


def test_api_request_get():
    """Test API request specification for GET."""
    request = APIRequest(method="GET", url="/api/products?category=books")
    assert request.method == "GET"
    assert request.body is None


def test_cli_command():
    """Test CLI command specification."""
    cmd = CLICommand(command="python", args=["main.py", "--config", "config.yml"], env={"ENV": "test", "DEBUG": "1"})
    assert cmd.command == "python"
    assert len(cmd.args) == 3
    assert cmd.env["ENV"] == "test"


def test_behavior_input_ui():
    """Test BehaviorInput with UI actions."""
    actions = [
        UIAction(action_type="navigate", url="/login"),
        UIAction(action_type="type", selector="#username", text="admin"),
        UIAction(action_type="click", selector="#submit"),
    ]
    input_spec = BehaviorInput(ui_actions=actions)
    assert len(input_spec.ui_actions) == 3
    assert input_spec.api_request is None
    assert input_spec.cli_command is None


def test_behavior_input_api():
    """Test BehaviorInput with API request."""
    request = APIRequest(method="GET", url="/api/health")
    input_spec = BehaviorInput(api_request=request)
    assert input_spec.api_request.method == "GET"
    assert input_spec.ui_actions is None


# ============================================================================
# Criteria Tests
# ============================================================================


def test_http_criteria_default():
    """Test HTTP criteria with default values."""
    criteria = HTTPCriteria()
    assert 200 in criteria.expected_status_codes
    assert 500 in criteria.forbidden_status_codes


def test_http_criteria_custom():
    """Test HTTP criteria with custom values."""
    criteria = HTTPCriteria(expected_status_codes=[200, 201], must_contain_json_paths=["$.data.id", "$.data.name"])
    assert 201 in criteria.expected_status_codes
    assert len(criteria.must_contain_json_paths) == 2


def test_dom_criteria():
    """Test DOM criteria specification."""
    criteria = DOMCriteria(
        required_selectors=["#success-message", ".confirmation"],
        forbidden_selectors=[".error-banner", ".warning-popup"],
        required_text_snippets=["Order placed successfully"],
    )
    assert "#success-message" in criteria.required_selectors
    assert ".error-banner" in criteria.forbidden_selectors
    assert len(criteria.required_text_snippets) == 1


def test_log_criteria():
    """Test log criteria specification."""
    criteria = LogCriteria(
        forbidden_patterns=["ERROR", "Exception", "Traceback"], required_patterns=["Request completed"]
    )
    assert "ERROR" in criteria.forbidden_patterns
    assert "Request completed" in criteria.required_patterns


def test_behavior_success_criteria_combined():
    """Test combined success criteria."""
    criteria = BehaviorSuccessCriteria(
        http=HTTPCriteria(expected_status_codes=[200]),
        dom=DOMCriteria(required_selectors=["#content"]),
        logs=LogCriteria(forbidden_patterns=["ERROR"]),
    )
    assert criteria.http.expected_status_codes == [200]
    assert criteria.dom.required_selectors == ["#content"]
    assert criteria.logs.forbidden_patterns == ["ERROR"]


# ============================================================================
# Scenario Tests
# ============================================================================


def test_behavior_scenario_ui():
    """Test BehaviorScenario for UI category."""
    scenario = BehaviorScenario(
        id="scenario-login",
        project_id="legacy-app",
        category="ui",
        name="User Login Flow",
        description="Test user login with valid credentials",
        environment="legacy",
        tags=["authentication", "critical"],
        input=BehaviorInput(
            ui_actions=[
                UIAction(action_type="navigate", url="/login"),
                UIAction(action_type="type", selector="#username", text="admin"),
                UIAction(action_type="click", selector="#submit"),
            ]
        ),
        success_criteria=BehaviorSuccessCriteria(dom=DOMCriteria(required_selectors=["#dashboard"])),
        created_at=datetime.now(),
    )
    assert scenario.category == "ui"
    assert len(scenario.tags) == 2
    assert len(scenario.input.ui_actions) == 3


def test_behavior_scenario_api():
    """Test BehaviorScenario for API category."""
    scenario = BehaviorScenario(
        id="scenario-create-order",
        project_id="legacy-api",
        category="api",
        name="Create Order API",
        description="Test order creation endpoint",
        environment="legacy",
        input=BehaviorInput(
            api_request=APIRequest(method="POST", url="/api/orders", body={"product_id": 123, "quantity": 1})
        ),
        success_criteria=BehaviorSuccessCriteria(
            http=HTTPCriteria(expected_status_codes=[201], must_contain_json_paths=["$.order_id"])
        ),
        created_at=datetime.now(),
    )
    assert scenario.category == "api"
    assert scenario.input.api_request.method == "POST"


# ============================================================================
# Observation Tests
# ============================================================================


def test_observed_http():
    """Test ObservedHTTP model."""
    observed = ObservedHTTP(
        status_code=200, headers={"Content-Type": "application/json"}, body={"status": "success", "data": {"id": 123}}
    )
    assert observed.status_code == 200
    assert observed.headers["Content-Type"] == "application/json"
    assert observed.body["data"]["id"] == 123


def test_observed_dom():
    """Test ObservedDOM model."""
    observed = ObservedDOM(
        present_selectors=["#dashboard", ".user-info"],
        missing_selectors=[".error-message"],
        present_text_snippets=["Welcome, Admin"],
    )
    assert "#dashboard" in observed.present_selectors
    assert ".error-message" in observed.missing_selectors


def test_observed_logs():
    """Test ObservedLogs model."""
    observed = ObservedLogs(
        lines=["INFO: Request started", "INFO: Request completed"],
        matched_forbidden_patterns=[],
        matched_required_patterns=["Request completed"],
    )
    assert len(observed.lines) == 2
    assert len(observed.matched_forbidden_patterns) == 0


# ============================================================================
# Violation and Snapshot Tests
# ============================================================================


def test_behavior_violation():
    """Test BehaviorViolation model."""
    violation = BehaviorViolation(
        code="HTTP_STATUS_MISMATCH",
        message="Expected status 200, got 500",
        severity="critical",
        details={"expected": 200, "actual": 500},
    )
    assert violation.code == "HTTP_STATUS_MISMATCH"
    assert violation.severity == "critical"
    assert violation.details["actual"] == 500


def test_behavior_snapshot_success():
    """Test BehaviorSnapshot with successful execution."""
    snapshot = BehaviorSnapshot(
        id="snapshot-123",
        scenario_id="scenario-login",
        project_id="legacy-app",
        environment="legacy",
        observed_http=ObservedHTTP(status_code=200, headers={}, body={"success": True}),
        duration_ms=150,
        success=True,
        violations=[],
        created_at=datetime.now(),
    )
    assert snapshot.success is True
    assert len(snapshot.violations) == 0
    assert snapshot.duration_ms == 150


def test_behavior_snapshot_with_violations():
    """Test BehaviorSnapshot with violations."""
    violations = [
        BehaviorViolation(
            code="DOM_ELEMENT_MISSING",
            message="Required selector '#success-message' not found",
            severity="high",
            details={"selector": "#success-message"},
        )
    ]
    snapshot = BehaviorSnapshot(
        id="snapshot-456",
        scenario_id="scenario-checkout",
        project_id="legacy-app",
        environment="candidate",
        observed_dom=ObservedDOM(present_selectors=["#cart"], missing_selectors=["#success-message"]),
        success=False,
        violations=violations,
        error_count=1,
        created_at=datetime.now(),
    )
    assert snapshot.success is False
    assert len(snapshot.violations) == 1
    assert snapshot.violations[0].code == "DOM_ELEMENT_MISSING"


# ============================================================================
# Contract Tests
# ============================================================================


def test_http_contract():
    """Test HTTPContract model."""
    contract = HTTPContract(
        required_status_codes=[200, 201], forbidden_status_codes=[500, 502], required_json_paths=["$.data"]
    )
    assert 200 in contract.required_status_codes
    assert 500 in contract.forbidden_status_codes


def test_dom_contract():
    """Test DOMContract model."""
    contract = DOMContract(
        must_have_selectors=["#header", "#footer"],
        must_not_have_selectors=[".error-banner"],
        must_have_text_snippets=["Copyright 2025"],
    )
    assert "#header" in contract.must_have_selectors
    assert ".error-banner" in contract.must_not_have_selectors


def test_log_contract():
    """Test LogContract model."""
    contract = LogContract(forbidden_patterns=["Exception", "ERROR"], required_patterns=["Request successful"])
    assert "Exception" in contract.forbidden_patterns


def test_behavior_contract():
    """Test BehaviorContract model."""
    contract = BehaviorContract(
        id="contract-login",
        scenario_id="scenario-login",
        project_id="legacy-app",
        version="1.0.0",
        environment_scope=["legacy", "candidate"],
        http_contract=HTTPContract(required_status_codes=[200]),
        dom_contract=DOMContract(must_have_selectors=["#dashboard"]),
        max_error_rate=0.05,
        max_duration_ms_p95=500,
        derived_from_snapshot_ids=["snap-1", "snap-2", "snap-3"],
        created_at=datetime.now(),
    )
    assert contract.version == "1.0.0"
    assert contract.max_error_rate == 0.05
    assert len(contract.derived_from_snapshot_ids) == 3


# ============================================================================
# Check Result Tests
# ============================================================================


def test_behavior_check_result_passed():
    """Test BehaviorCheckResult with passed check."""
    result = BehaviorCheckResult(
        snapshot_id="snap-123",
        contract_id="contract-login",
        project_id="legacy-app",
        passed=True,
        violations=[],
        risk_score=0.0,
        checked_at=datetime.now(),
    )
    assert result.passed is True
    assert result.risk_score == 0.0
    assert len(result.violations) == 0


def test_behavior_check_result_failed():
    """Test BehaviorCheckResult with failed check."""
    violations = [
        BehaviorViolation(
            code="HTTP_STATUS_MISMATCH", message="Expected 200, got 500", severity="critical", details={}
        ),
        BehaviorViolation(code="DOM_ELEMENT_MISSING", message="Required element missing", severity="high", details={}),
    ]
    result = BehaviorCheckResult(
        snapshot_id="snap-456",
        contract_id="contract-checkout",
        project_id="legacy-app",
        passed=False,
        violations=violations,
        risk_score=0.85,
        checked_at=datetime.now(),
    )
    assert result.passed is False
    assert result.risk_score == 0.85
    assert len(result.violations) == 2


def test_behavior_checks_summary():
    """Test BehaviorChecksSummary aggregation."""
    summary = BehaviorChecksSummary(
        total_scenarios_checked=10, total_snapshots_checked=50, total_passed=45, total_failed=5, max_risk_score=0.65
    )
    assert summary.total_scenarios_checked == 10
    assert summary.total_passed == 45
    assert summary.max_risk_score == 0.65


def test_behavior_checks_summary_all_passed():
    """Test BehaviorChecksSummary with all checks passed."""
    summary = BehaviorChecksSummary(
        total_scenarios_checked=5, total_snapshots_checked=20, total_passed=20, total_failed=0, max_risk_score=0.0
    )
    assert summary.total_failed == 0
    assert summary.max_risk_score == 0.0


# ============================================================================
# Integration Tests - Complete Flow
# ============================================================================


def test_complete_scenario_execution_flow():
    """Test complete flow: scenario → snapshot → contract → check."""
    # 1. Define scenario
    scenario = BehaviorScenario(
        id="test-scenario",
        project_id="test-project",
        category="api",
        name="Health Check",
        description="Test health endpoint",
        environment="legacy",
        input=BehaviorInput(api_request=APIRequest(method="GET", url="/health")),
        success_criteria=BehaviorSuccessCriteria(http=HTTPCriteria(expected_status_codes=[200])),
        created_at=datetime.now(),
    )

    # 2. Execute and capture snapshot
    snapshot = BehaviorSnapshot(
        id="test-snapshot",
        scenario_id=scenario.id,
        project_id=scenario.project_id,
        environment="legacy",
        observed_http=ObservedHTTP(
            status_code=200, headers={"Content-Type": "application/json"}, body={"status": "healthy"}
        ),
        duration_ms=50,
        success=True,
        created_at=datetime.now(),
    )

    # 3. Build contract from snapshot(s)
    contract = BehaviorContract(
        id="test-contract",
        scenario_id=scenario.id,
        project_id=scenario.project_id,
        http_contract=HTTPContract(required_status_codes=[200]),
        derived_from_snapshot_ids=[snapshot.id],
        created_at=datetime.now(),
    )

    # 4. Check new snapshot against contract
    check_result = BehaviorCheckResult(
        snapshot_id=snapshot.id,
        contract_id=contract.id,
        project_id=scenario.project_id,
        passed=True,
        violations=[],
        risk_score=0.0,
        checked_at=datetime.now(),
    )

    # Verify flow
    assert scenario.id == snapshot.scenario_id
    assert snapshot.scenario_id == contract.scenario_id
    assert check_result.contract_id == contract.id
    assert check_result.passed is True


def test_regression_detection_flow():
    """Test regression detection: legacy passes, candidate fails."""
    scenario_id = "test-regression"

    # Legacy snapshot (passes)
    legacy_snapshot = BehaviorSnapshot(
        id="legacy-snap",
        scenario_id=scenario_id,
        project_id="test-project",
        environment="legacy",
        observed_http=ObservedHTTP(status_code=200, headers={}, body={"ok": True}),
        success=True,
        created_at=datetime.now(),
    )

    # Contract from legacy
    contract = BehaviorContract(
        id="test-contract",
        scenario_id=scenario_id,
        project_id="test-project",
        http_contract=HTTPContract(required_status_codes=[200]),
        derived_from_snapshot_ids=[legacy_snapshot.id],
        created_at=datetime.now(),
    )

    # Candidate snapshot (fails - regression!)
    candidate_snapshot = BehaviorSnapshot(
        id="candidate-snap",
        scenario_id=scenario_id,
        project_id="test-project",
        environment="candidate",
        observed_http=ObservedHTTP(status_code=500, headers={}, body={"error": "Internal Server Error"}),
        success=False,
        violations=[
            BehaviorViolation(
                code="HTTP_STATUS_MISMATCH",
                message="Expected 200, got 500",
                severity="critical",
                details={"expected": 200, "actual": 500},
            )
        ],
        created_at=datetime.now(),
    )

    # Check result (regression detected)
    check_result = BehaviorCheckResult(
        snapshot_id=candidate_snapshot.id,
        contract_id=contract.id,
        project_id="test-project",
        passed=False,
        violations=candidate_snapshot.violations,
        risk_score=0.9,  # High risk - critical regression
        checked_at=datetime.now(),
    )

    # Verify regression detected
    assert legacy_snapshot.success is True
    assert candidate_snapshot.success is False
    assert check_result.passed is False
    assert check_result.risk_score >= 0.7  # High risk threshold
    assert len(check_result.violations) > 0
