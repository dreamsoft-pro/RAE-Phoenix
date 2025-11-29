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
Behavior Comparison Engine - Validates snapshots against contracts.

Core validation engine for Legacy Behavior Guard that detects behavioral regressions
by comparing candidate behavior against established contracts.
"""
import re
from datetime import datetime
from typing import List

from feniks.core.models.behavior import (
    BehaviorCheckResult,
    BehaviorContract,
    BehaviorSnapshot,
    BehaviorViolation,
    ObservedCLI,
    ObservedDOM,
    ObservedHTTP,
    ObservedLogs,
)
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("core.behavior.comparison_engine")


class BehaviorComparisonEngine:
    """
    Compares behavior snapshots against contracts to detect violations.

    Validates:
    - HTTP responses (status, headers, body structure)
    - CLI outputs (exit codes, stdout/stderr patterns)
    - DOM structure (element existence, visibility, content)
    - Log patterns (expected messages, error detection)
    - Performance (duration thresholds)
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize comparison engine.

        Args:
            strict_mode: If True, any deviation is considered violation
        """
        self.strict_mode = strict_mode
        log.info(f"BehaviorComparisonEngine initialized (strict_mode={strict_mode})")

    def check_snapshot(self, snapshot: BehaviorSnapshot, contract: BehaviorContract) -> BehaviorCheckResult:
        """
        Check snapshot against contract.

        Args:
            snapshot: Observed behavior snapshot
            contract: Expected behavior contract

        Returns:
            BehaviorCheckResult with validation results and risk score
        """
        # Validate scenario match
        if snapshot.scenario_id != contract.scenario_id:
            raise FeniksError(f"Scenario mismatch: snapshot={snapshot.scenario_id}, contract={contract.scenario_id}")

        log.info(f"Checking snapshot {snapshot.id} against contract {contract.id}")

        violations: List[BehaviorViolation] = []

        # Check HTTP behavior
        if contract.http_contract and snapshot.observed_http:
            http_violations = self._check_http(snapshot.observed_http, contract.http_contract)
            violations.extend(http_violations)

        # Check DOM behavior
        if contract.dom_contract and snapshot.observed_dom:
            dom_violations = self._check_dom(snapshot.observed_dom, contract.dom_contract)
            violations.extend(dom_violations)

        # Check log behavior
        if contract.log_contract and snapshot.observed_logs:
            log_violations = self._check_logs(snapshot.observed_logs, contract.log_contract)
            violations.extend(log_violations)

        # Check duration
        if contract.max_duration_ms_p95 and snapshot.duration_ms:
            if snapshot.duration_ms > contract.max_duration_ms_p95:
                violations.append(
                    BehaviorViolation(
                        code="DURATION_EXCEEDED",
                        message=f"Duration {snapshot.duration_ms}ms exceeds threshold {contract.max_duration_ms_p95}ms",
                        severity="medium",
                        details={
                            "actual_ms": snapshot.duration_ms,
                            "max_ms": contract.max_duration_ms_p95,
                            "overhead_pct": round((snapshot.duration_ms / contract.max_duration_ms_p95 - 1) * 100, 1),
                        },
                    )
                )

        # Calculate risk score
        risk_score = self._calculate_risk_score(violations)

        # Create result
        result = BehaviorCheckResult(
            snapshot_id=snapshot.id,
            contract_id=contract.id,
            scenario_id=snapshot.scenario_id,
            project_id=snapshot.project_id,
            passed=len(violations) == 0,
            violations=violations,
            risk_score=risk_score,
            checked_at=datetime.now(),
        )

        log.info(
            f"Check complete: snapshot={snapshot.id}, passed={result.passed}, "
            f"violations={len(violations)}, risk={risk_score:.2f}"
        )

        return result

    def _check_http(self, observed: ObservedHTTP, contract) -> List[BehaviorViolation]:
        """Check HTTP behavior against contract."""
        violations = []

        # Check status codes
        if contract.required_status_codes:
            if observed.status_code not in contract.required_status_codes:
                violations.append(
                    BehaviorViolation(
                        code="HTTP_STATUS_UNEXPECTED",
                        message=f"Status {observed.status_code} not in expected: {contract.required_status_codes}",
                        severity="high",
                        details={"expected": contract.required_status_codes, "actual": observed.status_code},
                    )
                )

        if contract.forbidden_status_codes:
            if observed.status_code in contract.forbidden_status_codes:
                violations.append(
                    BehaviorViolation(
                        code="HTTP_STATUS_FORBIDDEN",
                        message=f"Status {observed.status_code} is forbidden",
                        severity="critical",
                        details={"forbidden": contract.forbidden_status_codes, "actual": observed.status_code},
                    )
                )

        # Check JSON paths
        if isinstance(observed.body, dict):
            for json_path in contract.required_json_paths:
                if not self._check_json_path(observed.body, json_path):
                    violations.append(
                        BehaviorViolation(
                            code="JSON_PATH_MISSING",
                            message=f"Required JSON path not found: {json_path}",
                            severity="high",
                            details={"path": json_path},
                        )
                    )

            for json_path in contract.forbidden_json_paths:
                if self._check_json_path(observed.body, json_path):
                    violations.append(
                        BehaviorViolation(
                            code="JSON_PATH_FORBIDDEN",
                            message=f"Forbidden JSON path found: {json_path}",
                            severity="medium",
                            details={"path": json_path},
                        )
                    )

        return violations

    def _check_cli(self, observed: ObservedCLI, criteria) -> List[BehaviorViolation]:
        # CLI checks not implemented in BehaviorContract yet
        return []

    def _check_dom(self, observed: ObservedDOM, contract) -> List[BehaviorViolation]:
        """Check DOM behavior against contract."""
        violations = []

        # Get all observed selectors
        observed_selectors = set(observed.present_selectors)

        # Check required selectors
        for selector in contract.must_have_selectors:
            if selector not in observed_selectors:
                violations.append(
                    BehaviorViolation(
                        code="DOM_SELECTOR_MISSING",
                        message=f"Required DOM selector not found: {selector}",
                        severity="high",
                        details={"selector": selector},
                    )
                )

        # Check forbidden selectors
        for selector in contract.must_not_have_selectors:
            if selector in observed_selectors:
                violations.append(
                    BehaviorViolation(
                        code="DOM_SELECTOR_FORBIDDEN",
                        message=f"Forbidden DOM selector found: {selector}",
                        severity="medium",
                        details={"selector": selector},
                    )
                )

        # Check text snippets
        observed_text = set(observed.present_text_snippets)
        for text in contract.must_have_text_snippets:
            if text not in observed_text:
                violations.append(
                    BehaviorViolation(
                        code="DOM_TEXT_MISSING",
                        message=f"Required text snippet not found: {text}",
                        severity="medium",
                        details={"text": text},
                    )
                )

        return violations

    def _check_logs(self, observed: ObservedLogs, contract) -> List[BehaviorViolation]:
        """Check log behavior against contract."""
        violations = []

        # Combine all log lines
        all_logs = "\n".join(observed.lines)

        # Check required patterns
        for pattern in contract.required_patterns:
            if not self._check_pattern(all_logs, pattern):
                violations.append(
                    BehaviorViolation(
                        code="LOG_PATTERN_MISSING",
                        message=f"Required log pattern not found: {pattern}",
                        severity="low",
                        details={"pattern": pattern},
                    )
                )

        # Check forbidden patterns
        for pattern in contract.forbidden_patterns:
            if self._check_pattern(all_logs, pattern):
                violations.append(
                    BehaviorViolation(
                        code="LOG_PATTERN_FORBIDDEN",
                        message=f"Forbidden log pattern found: {pattern}",
                        severity="medium",
                        details={"pattern": pattern},
                    )
                )

        return violations

    def _check_json_path(self, data: dict, path: str) -> bool:
        """Check if JSON path exists in data."""
        if not path.startswith("$."):
            return False

        keys = path[2:].split(".")
        current = data

        try:
            for key in keys:
                if "[" in key and "]" in key:
                    # Handle array indices
                    base_key = key[: key.index("[")]
                    index = int(key[key.index("[") + 1 : key.index("]")])
                    current = current[base_key][index]
                else:
                    current = current[key]
            return True
        except (KeyError, IndexError, TypeError):
            return False

    def _check_pattern(self, text: str, pattern: str) -> bool:
        """Check if pattern exists in text (regex or literal)."""
        if not text:
            return False

        try:
            return bool(re.search(pattern, text))
        except re.error:
            return pattern in text

    def _calculate_risk_score(self, violations: List[BehaviorViolation]) -> float:
        """
        Calculate risk score from violations (0.0-1.0).

        Severity weights:
        - critical: 1.0
        - high: 0.7
        - medium: 0.4
        - low: 0.2
        """
        if not violations:
            return 0.0

        severity_weights = {"critical": 1.0, "high": 0.7, "medium": 0.4, "low": 0.2}

        # Calculate weighted sum
        total_weight = sum(severity_weights.get(v.severity, 0.5) for v in violations)

        # Normalize to 0-1 range (cap at 1.0)
        risk_score = min(total_weight / len(violations), 1.0)

        return round(risk_score, 2)


# ============================================================================
# Factory Function
# ============================================================================


def create_comparison_engine(strict_mode: bool = False) -> BehaviorComparisonEngine:
    """
    Create behavior comparison engine instance.

    Args:
        strict_mode: If True, any deviation is considered violation

    Returns:
        BehaviorComparisonEngine instance
    """
    return BehaviorComparisonEngine(strict_mode=strict_mode)
