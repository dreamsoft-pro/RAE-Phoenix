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
CLI Scenario Runner - Executes command-line scenarios and captures output.

Supports batch scripts, CLI tools, and command testing with exit code and output validation.
"""
import re
import subprocess
import time
import uuid
from datetime import datetime

from feniks.core.models.behavior import BehaviorScenario, BehaviorSnapshot, BehaviorViolation, ObservedCLI, ObservedLogs
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("adapters.runners.cli")


class CLIRunner:
    """
    Executes CLI behavior scenarios via subprocess.

    Features:
    - Command execution with timeout
    - Stdout/stderr capture
    - Exit code validation
    - Output pattern matching (regex)
    - Environment variable support
    - Working directory configuration
    - Detailed logging
    """

    def __init__(self, timeout: int = 60, shell: bool = False):
        """
        Initialize CLI runner.

        Args:
            timeout: Command timeout in seconds
            shell: Whether to execute command through shell
        """
        self.timeout = timeout
        self.shell = shell
        log.info(f"CLIRunner initialized (timeout={timeout}s, shell={shell})")

    def execute_scenario(self, scenario: BehaviorScenario, environment: str = "candidate") -> BehaviorSnapshot:
        """
        Execute a CLI scenario and capture snapshot.

        Args:
            scenario: The behavior scenario to execute
            environment: Environment identifier (legacy/candidate/staging/production)

        Returns:
            BehaviorSnapshot with captured CLI output and validation results
        """
        if scenario.category not in ["cli", "mixed"]:
            raise FeniksError(f"CLIRunner only supports 'cli' or 'mixed' scenarios, got: {scenario.category}")

        if not scenario.input.cli_command:
            raise FeniksError("Scenario has no cli_command defined")

        log.info(f"Executing CLI scenario: {scenario.name} (id={scenario.id}, env={environment})")

        cli_command = scenario.input.cli_command
        start_time = time.time()

        try:
            # Prepare execution environment
            working_dir = scenario.input.context.get("working_directory")
            env_vars = scenario.input.context.get("environment_variables", {})

            # Merge with current environment
            import os

            full_env = os.environ.copy()
            full_env.update(env_vars)

            # Parse command
            if self.shell:
                cmd = cli_command
            else:
                # Split command into list for subprocess
                cmd = cli_command.split()

            # Execute command
            log.debug(f"Executing: {cli_command} (cwd={working_dir})")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=self.shell,
                cwd=working_dir,
                env=full_env,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Capture CLI output
            observed_cli = ObservedCLI(
                command=cli_command, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr
            )

            # Validate against success criteria
            violations = []
            success = True

            if scenario.success_criteria.cli:
                cli_violations = self._validate_cli_criteria(observed_cli, scenario.success_criteria.cli)
                violations.extend(cli_violations)
                if cli_violations:
                    success = False

            # Create snapshot
            snapshot = BehaviorSnapshot(
                id=f"snap-{scenario.id}-{uuid.uuid4().hex[:8]}",
                scenario_id=scenario.id,
                project_id=scenario.project_id,
                environment=environment,
                observed_cli=observed_cli,
                observed_logs=ObservedLogs(
                    lines=[
                        f"Command: {cli_command}",
                        f"Exit code: {result.returncode}",
                        f"Stdout lines: {len(result.stdout.splitlines())}",
                        f"Stderr lines: {len(result.stderr.splitlines())}",
                    ]
                ),
                duration_ms=duration_ms,
                success=success,
                violations=violations,
                created_at=datetime.now(),
                recorded_by="cli_runner",
            )

            log.info(
                f"Scenario executed: {scenario.id} (success={success}, exit_code={result.returncode}, duration={duration_ms}ms)"
            )
            return snapshot

        except subprocess.TimeoutExpired:
            log.error(f"Command timeout after {self.timeout}s: {cli_command}")
            return self._create_error_snapshot(
                scenario=scenario,
                environment=environment,
                error_message=f"Command timeout after {self.timeout}s",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except FileNotFoundError as e:
            log.error(f"Command not found: {e}")
            return self._create_error_snapshot(
                scenario=scenario,
                environment=environment,
                error_message=f"Command not found: {str(e)}",
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

    def _validate_cli_criteria(self, observed: ObservedCLI, criteria) -> list[BehaviorViolation]:
        """Validate observed CLI against criteria."""
        violations = []

        # Check exit codes
        if criteria.expected_exit_codes and observed.exit_code not in criteria.expected_exit_codes:
            violations.append(
                BehaviorViolation(
                    code="CLI_EXIT_CODE_UNEXPECTED",
                    message=f"Exit code {observed.exit_code} not in expected: {criteria.expected_exit_codes}",
                    severity="high",
                    details={"expected": criteria.expected_exit_codes, "actual": observed.exit_code},
                )
            )

        if criteria.forbidden_exit_codes and observed.exit_code in criteria.forbidden_exit_codes:
            violations.append(
                BehaviorViolation(
                    code="CLI_EXIT_CODE_FORBIDDEN",
                    message=f"Exit code {observed.exit_code} is forbidden",
                    severity="critical",
                    details={"forbidden": criteria.forbidden_exit_codes, "actual": observed.exit_code},
                )
            )

        # Check stdout patterns
        for pattern in criteria.must_contain_stdout_patterns:
            if not self._check_pattern(observed.stdout, pattern):
                violations.append(
                    BehaviorViolation(
                        code="CLI_STDOUT_PATTERN_MISSING",
                        message=f"Required stdout pattern not found: {pattern}",
                        severity="high",
                        details={"pattern": pattern},
                    )
                )

        for pattern in criteria.must_not_contain_stdout_patterns:
            if self._check_pattern(observed.stdout, pattern):
                violations.append(
                    BehaviorViolation(
                        code="CLI_STDOUT_PATTERN_FORBIDDEN",
                        message=f"Forbidden stdout pattern found: {pattern}",
                        severity="medium",
                        details={"pattern": pattern},
                    )
                )

        # Check stderr patterns
        for pattern in criteria.must_contain_stderr_patterns:
            if not self._check_pattern(observed.stderr, pattern):
                violations.append(
                    BehaviorViolation(
                        code="CLI_STDERR_PATTERN_MISSING",
                        message=f"Required stderr pattern not found: {pattern}",
                        severity="high",
                        details={"pattern": pattern},
                    )
                )

        for pattern in criteria.must_not_contain_stderr_patterns:
            if self._check_pattern(observed.stderr, pattern):
                violations.append(
                    BehaviorViolation(
                        code="CLI_STDERR_PATTERN_FORBIDDEN",
                        message=f"Forbidden stderr pattern found: {pattern}",
                        severity="medium",
                        details={"pattern": pattern},
                    )
                )

        return violations

    def _check_pattern(self, text: str, pattern: str) -> bool:
        """
        Check if pattern exists in text.
        Supports both literal strings and regex patterns.
        """
        if not text:
            return False

        try:
            # Try as regex first
            return bool(re.search(pattern, text))
        except re.error:
            # Fall back to literal string search
            return pattern in text

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
            recorded_by="cli_runner",
        )


# ============================================================================
# Factory Function
# ============================================================================


def create_cli_runner(timeout: int = 60, shell: bool = False) -> CLIRunner:
    """
    Create CLI runner instance.

    Args:
        timeout: Command timeout in seconds
        shell: Whether to execute command through shell

    Returns:
        CLIRunner instance
    """
    return CLIRunner(timeout=timeout, shell=shell)
