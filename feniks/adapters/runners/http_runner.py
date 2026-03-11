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
HTTP Scenario Runner - Executes API behavior scenarios and captures snapshots.

Supports REST APIs with full HTTP method coverage and response validation.
"""
import time
import uuid
from datetime import datetime
from typing import Optional

import requests

from feniks.core.models.behavior import (
    BehaviorScenario,
    BehaviorSnapshot,
    BehaviorViolation,
    ObservedHTTP,
    ObservedLogs,
)
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("adapters.runners.http")


class HTTPRunner:
    """
    Executes API behavior scenarios via HTTP requests.

    Features:
    - Full HTTP method support (GET, POST, PUT, PATCH, DELETE)
    - Request/response capture
    - Success criteria validation (status codes, JSON paths, patterns)
    - Timeout and retry handling
    - Detailed logging
    """

    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        """
        Initialize HTTP runner.

        Args:
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        log.info(f"HTTPRunner initialized (timeout={timeout}s, verify_ssl={verify_ssl})")

    def execute_scenario(self, scenario: BehaviorScenario, environment: str = "candidate") -> BehaviorSnapshot:
        """
        Execute an API scenario and capture snapshot.

        Args:
            scenario: The behavior scenario to execute
            environment: Environment identifier (legacy/candidate/staging/production)

        Returns:
            BehaviorSnapshot with captured HTTP response and validation results
        """
        if scenario.category not in ["api", "mixed"]:
            raise FeniksError(f"HTTPRunner only supports 'api' or 'mixed' scenarios, got: {scenario.category}")

        if not scenario.input.api_request:
            raise FeniksError("Scenario has no api_request defined")

        log.info(f"Executing API scenario: {scenario.name} (id={scenario.id}, env={environment})")

        api_request = scenario.input.api_request
        start_time = time.time()

        try:
            # Build URL
            base_url = scenario.input.context.get("base_url", "")
            url = f"{base_url}{api_request.url}" if base_url else api_request.url

            # Prepare request
            method = api_request.method.upper()
            headers = api_request.headers or {}
            body = api_request.body

            # Execute request
            log.debug(f"HTTP {method} {url}")

            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if isinstance(body, str) else None,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Capture HTTP response
            observed_http = ObservedHTTP(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=self._parse_response_body(response),
            )

            # Validate against success criteria
            violations = []
            success = True

            if scenario.success_criteria.http:
                http_violations = self._validate_http_criteria(observed_http, scenario.success_criteria.http)
                violations.extend(http_violations)
                if http_violations:
                    success = False

            # Create snapshot
            snapshot = BehaviorSnapshot(
                id=f"snap-{scenario.id}-{uuid.uuid4().hex[:8]}",
                scenario_id=scenario.id,
                project_id=scenario.project_id,
                environment=environment,
                observed_http=observed_http,
                observed_logs=ObservedLogs(lines=[f"HTTP {method} {url} -> {response.status_code}"]),
                duration_ms=duration_ms,
                success=success,
                violations=violations,
                created_at=datetime.now(),
                recorded_by="http_runner",
            )

            log.info(
                f"Scenario executed: {scenario.id} (success={success}, status={response.status_code}, duration={duration_ms}ms)"
            )
            return snapshot

        except requests.exceptions.Timeout:
            log.error(f"Request timeout after {self.timeout}s: {api_request.method} {url}")
            return self._create_error_snapshot(
                scenario=scenario,
                environment=environment,
                error_message=f"Request timeout after {self.timeout}s",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except requests.exceptions.ConnectionError as e:
            log.error(f"Connection error: {e}")
            return self._create_error_snapshot(
                scenario=scenario,
                environment=environment,
                error_message=f"Connection error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            log.error(f"Unexpected error executing scenario: {e}", exc_info=True)
            return self._create_error_snapshot(
                scenario=scenario,
                environment=environment,
                error_message=f"Unexpected error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _parse_response_body(self, response: requests.Response) -> Optional[dict | str]:
        """Parse response body as JSON or text."""
        try:
            return response.json()
        except Exception:
            return response.text if response.text else None

    def _validate_http_criteria(self, observed: ObservedHTTP, criteria) -> list[BehaviorViolation]:
        """Validate observed HTTP against criteria."""
        violations = []

        # Check status codes
        if criteria.expected_status_codes and observed.status_code not in criteria.expected_status_codes:
            violations.append(
                BehaviorViolation(
                    code="HTTP_STATUS_UNEXPECTED",
                    message=f"Status {observed.status_code} not in expected: {criteria.expected_status_codes}",
                    severity="high",
                    details={"expected": criteria.expected_status_codes, "actual": observed.status_code},
                )
            )

        if criteria.forbidden_status_codes and observed.status_code in criteria.forbidden_status_codes:
            violations.append(
                BehaviorViolation(
                    code="HTTP_STATUS_FORBIDDEN",
                    message=f"Status {observed.status_code} is forbidden",
                    severity="critical",
                    details={"forbidden": criteria.forbidden_status_codes, "actual": observed.status_code},
                )
            )

        # Check JSON paths (basic implementation)
        if isinstance(observed.body, dict):
            for json_path in criteria.must_contain_json_paths:
                if not self._check_json_path(observed.body, json_path):
                    violations.append(
                        BehaviorViolation(
                            code="JSON_PATH_MISSING",
                            message=f"Required JSON path not found: {json_path}",
                            severity="high",
                            details={"path": json_path},
                        )
                    )

            for json_path in criteria.must_not_contain_json_paths:
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

    def _check_json_path(self, data: dict, path: str) -> bool:
        """
        Simple JSONPath checker (supports $.key.subkey notation).
        For production, consider using jsonpath-ng library.
        """
        if not path.startswith("$."):
            return False

        keys = path[2:].split(".")
        current = data

        try:
            for key in keys:
                # Handle array indices like [0]
                if "[" in key and "]" in key:
                    base_key = key[: key.index("[")]
                    index = int(key[key.index("[") + 1 : key.index("]")])
                    current = current[base_key][index]
                else:
                    current = current[key]
            return True
        except (KeyError, IndexError, TypeError):
            return False

    def _create_error_snapshot(
        self, scenario: BehaviorScenario, environment: str, error_message: str, duration_ms: int
    ) -> BehaviorSnapshot:
        """Create snapshot for error scenarios."""
        return BehaviorSnapshot(
            id=f"snap-{scenario.id}-error-{uuid.uuid4().hex[:8]}",
            scenario_id=scenario.id,
            project_id=scenario.project_id,
            environment=environment,
            observed_logs=ObservedLogs(lines=[error_message]),
            duration_ms=duration_ms,
            success=False,
            violations=[
                BehaviorViolation(code="EXECUTION_ERROR", message=error_message, severity="critical", details={})
            ],
            error_count=1,
            created_at=datetime.now(),
            recorded_by="http_runner",
        )


# ============================================================================
# Factory Function
# ============================================================================


def create_http_runner(timeout: int = 30, verify_ssl: bool = True) -> HTTPRunner:
    """
    Create HTTP runner instance.

    Args:
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        HTTPRunner instance
    """
    return HTTPRunner(timeout=timeout, verify_ssl=verify_ssl)
