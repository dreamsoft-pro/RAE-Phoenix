# Copyright 2025 Grzegorz Leśniowski
"""
Python Runner - Executes Python-specific behavior scenarios (e.g., using pytest).
Integrates tightly with the Contract Engine and OpenTelemetry.
"""
import time
import uuid
import subprocess
from datetime import datetime
from typing import Optional, Dict

from feniks.core.models.behavior import (
    BehaviorScenario,
    BehaviorSnapshot,
    ObservedCLI,
    ObservedLogs,
    BehaviorViolation,
    CLICommand
)
from feniks.core.models.types import OperationalState
from feniks.infra.logging import get_logger
from feniks.infra.tracing import span

log = get_logger("adapters.runners.python")

class PythonRunner:
    """
    Executes Python scripts or tests (e.g. pytest) as behavior scenarios.
    """
    def __init__(self, state: OperationalState, timeout: int = 60):
        self.state = state
        self.timeout = timeout

    def execute_scenario(
        self, 
        scenario: BehaviorScenario, 
        environment: str = "candidate"
    ) -> BehaviorSnapshot:
        """
        Runs the specified Python command and wraps the output in a BehaviorSnapshot.
        """
        with span("execute_python_scenario", attributes={"scenario.id": scenario.id}):
            if not scenario.input.cli_command:
                # Fallback to a default pytest command if not explicitly provided
                cmd = CLICommand(command="pytest", args=["-v"])
            else:
                cmd = scenario.input.cli_command

            log.info(f"Executing Python scenario: {scenario.name}", command=cmd.command)
            
            start_time = time.time()
            
            try:
                # Merge env vars
                import os
                env = os.environ.copy()
                env.update(cmd.env)
                
                full_cmd = [cmd.command] + cmd.args
                
                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env=env,
                    cwd=scenario.input.context.get("working_directory")
                )
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                observed_cli = ObservedCLI(
                    command=" ".join(full_cmd),
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
                
                success = result.returncode == 0
                violations = []
                
                if not success:
                    violations.append(
                        BehaviorViolation(
                            code="PYTHON_EXECUTION_FAILED",
                            message=f"Command exited with code {result.returncode}",
                            severity="high",
                            details={"stderr": result.stderr[-500:]} # last 500 chars
                        )
                    )
                
                return BehaviorSnapshot(
                    id=f"snap-{scenario.id}-{uuid.uuid4().hex[:8]}",
                    scenario_id=scenario.id,
                    project_id=scenario.project_id,
                    environment=environment,
                    observed_cli=observed_cli,
                    observed_logs=ObservedLogs(
                        lines=result.stdout.splitlines() + result.stderr.splitlines()
                    ),
                    duration_ms=duration_ms,
                    success=success,
                    violations=violations,
                    created_at=datetime.now(),
                    recorded_by=self.state.agent_id
                )
                
            except Exception as e:
                log.error("python_runner_error", error=str(e))
                return BehaviorSnapshot(
                    id=f"snap-{scenario.id}-err-{uuid.uuid4().hex[:8]}",
                    scenario_id=scenario.id,
                    project_id=scenario.project_id,
                    environment=environment,
                    success=False,
                    violations=[
                        BehaviorViolation(
                            code="RUNNER_EXCEPTION",
                            message=str(e),
                            severity="critical"
                        )
                    ],
                    duration_ms=int((time.time() - start_time) * 1000),
                    created_at=datetime.now(),
                    recorded_by=self.state.agent_id
                )
