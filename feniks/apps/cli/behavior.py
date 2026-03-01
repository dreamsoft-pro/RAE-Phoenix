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
Behavior CLI Commands - Legacy Behavior Guard

Commands for recording, building contracts, and checking behavior
of legacy systems without traditional tests.
"""
import json
from datetime import datetime
from pathlib import Path
import yaml
import uuid

from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger
from feniks.core.models.behavior import BehaviorScenario, BehaviorInput, CLICommand, BehaviorSuccessCriteria, CLISuccessCriteria
from feniks.core.models.types import OperationalState, OperationalMode, TargetLanguage, ComplianceLevel

# Import runners
from feniks.adapters.runners.cli_runner import CLIRunner
from feniks.adapters.runners.python_runner import PythonRunner
from feniks.adapters.runners.php_runner import PHPRunner

log = get_logger("cli.behavior")


def handle_behavior_record(args):
    """
    Record behavior snapshots for a scenario.
    Executes a behavior scenario and captures snapshots.
    """
    log.info("=== Behavior Record ===")
    log.info(f"Project: {args.project_id}")
    log.info(f"Scenario: {args.scenario_id}")
    log.info(f"Environment: {args.environment}")
    log.info(f"Output: {args.output}")
    log.info(f"Language: {args.language}")
    
    # 1. Setup Operational State
    state = OperationalState(
        mode=OperationalMode.AUDIT,
        language=TargetLanguage(args.language),
        trace_id=f"trace-{uuid.uuid4().hex[:8]}",
        agent_id="cli-user",
        compliance=ComplianceLevel.ADVISORY
    )

    # 2. Select Runner
    if state.language == TargetLanguage.PYTHON:
        runner = PythonRunner(state)
    elif state.language == TargetLanguage.PHP:
        runner = PHPRunner(state)
    else:
        # Fallback to generic CLI runner
        runner = CLIRunner()

    # 3. Load or Mock Scenario
    # In a full DB implementation, we would fetch by args.scenario_id.
    # For now, we construct a generic scenario from CLI args if it's missing.
    scenario = BehaviorScenario(
        id=args.scenario_id,
        project_id=args.project_id,
        category="cli",
        name=f"Auto-generated for {args.scenario_id}",
        description="CLI execution test",
        environment=args.environment,
        input=BehaviorInput(
            cli_command=CLICommand(command=args.command_to_run if hasattr(args, 'command_to_run') and args.command_to_run else "echo", args=["test"])
        ),
        success_criteria=BehaviorSuccessCriteria(
            cli=CLISuccessCriteria(expected_exit_codes=[0])
        ),
        created_at=datetime.now()
    )

    # 4. Execute
    snapshots = []
    for i in range(args.count):
        log.info(f"Execution {i+1}/{args.count}")
        snap = runner.execute_scenario(scenario, environment=args.environment)
        snapshots.append(snap.model_dump())

    # 5. Save Output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        for snap_dict in snapshots:
            # handle datetime serialization
            snap_dict['created_at'] = snap_dict['created_at'].isoformat()
            f.write(json.dumps(snap_dict) + "\n")

    log.info(f"Saved {len(snapshots)} snapshot(s) to {output_path}")
    log.info("=== Record Complete ===")


from feniks.core.behavior.contract_generator import ContractGenerator
from feniks.core.models.behavior import BehaviorSnapshot

def handle_behavior_build_contracts(args):
    """
    Build behavior contracts from recorded snapshots.
    Analyzes multiple BehaviorSnapshots to derive generalized
    BehaviorContracts that define expected system behavior.
    """
    log.info("=== Build Behavior Contracts ===")
    log.info(f"Project: {args.project_id}")
    log.info(f"Input: {args.input}")
    log.info(f"Output: {args.output}")
    log.info(f"Min snapshots: {args.min_snapshots}")

    input_path = Path(args.input)
    if not input_path.exists():
        raise FeniksError(f"Input file not found: {input_path}")

    # Load snapshots
    snapshots_data = []
    with input_path.open("r") as f:
        for line in f:
            snapshots_data.append(json.loads(line))

    log.info(f"Loaded {len(snapshots_data)} snapshot(s)")

    # Group by scenario_id
    scenarios_map = {}
    for data in snapshots_data:
        scenario_id = data.get("scenario_id")
        if scenario_id not in scenarios_map:
            scenarios_map[scenario_id] = []
        # Re-construct snapshot object
        # Note: simplistic parsing for now
        scenarios_map[scenario_id].append(BehaviorSnapshot(**data))

    log.info(f"Found {len(scenarios_map)} unique scenario(s)")

    # Build contracts
    generator = ContractGenerator()
    contracts = []
    for scenario_id, scenario_snapshots in scenarios_map.items():
        if len(scenario_snapshots) < args.min_snapshots:
            log.warning(
                f"Scenario {scenario_id}: only {len(scenario_snapshots)} snapshot(s), "
                f"minimum {args.min_snapshots} required. Skipping."
            )
            continue

        log.info(f"Building contract for scenario {scenario_id} from {len(scenario_snapshots)} snapshot(s)")
        
        contract = generator.generate_from_snapshots(
            project_id=args.project_id,
            scenario_id=scenario_id,
            snapshots=scenario_snapshots
        )
        contracts.append(contract.model_dump())

    # Save contracts
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        for contract_dict in contracts:
            # Handle datetime
            contract_dict['created_at'] = contract_dict['created_at'].isoformat()
            f.write(json.dumps(contract_dict) + "\n")

    log.info(f"Saved {len(contracts)} contract(s) to {output_path}")
    log.info("=== Build Contracts Complete ===")


from feniks.core.behavior.contract_engine import ContractEngine
from feniks.core.models.behavior import BehaviorContract

async def handle_behavior_check(args):
    """
    Check new system behavior against contracts.
    Compares BehaviorSnapshots from candidate system against
    BehaviorContracts to detect regressions.
    """
    log.info("=== Behavior Check ===")
    log.info(f"Project: {args.project_id}")
    log.info(f"Contracts: {args.contracts}")
    log.info(f"Snapshots: {args.snapshots}")
    log.info(f"Output: {args.output}")

    # 1. Setup Engine
    state = OperationalState(
        mode=OperationalMode.REFACTOR,
        language=TargetLanguage.GENERIC,
        trace_id=f"trace-{uuid.uuid4().hex[:8]}",
        agent_id="cli-user",
        compliance=ComplianceLevel.STRICT
    )
    engine = ContractEngine(state)

    # 2. Load contracts
    contracts_path = Path(args.contracts)
    if not contracts_path.exists():
        raise FeniksError(f"Contracts file not found: {contracts_path}")

    contracts_list = []
    with contracts_path.open("r") as f:
        for line in f:
            contracts_list.append(BehaviorContract(**json.loads(line)))

    log.info(f"Loaded {len(contracts_list)} contract(s)")
    contracts_map = {c.scenario_id: c for c in contracts_list}

    # 3. Load snapshots
    snapshots_path = Path(args.snapshots)
    if not snapshots_path.exists():
        raise FeniksError(f"Snapshots file not found: {snapshots_path}")

    snapshots_list = []
    with snapshots_path.open("r") as f:
        for line in f:
            snapshots_list.append(BehaviorSnapshot(**json.loads(line)))

    log.info(f"Loaded {len(snapshots_list)} snapshot(s)")

    # 4. Check
    check_results = []
    total_passed = 0
    total_failed = 0
    max_risk = 0.0

    for snap in snapshots_list:
        contract = contracts_map.get(snap.scenario_id)
        if not contract:
            log.warning(f"No contract found for scenario {snap.scenario_id}, skipping")
            continue

        result = await engine.validate_candidate(contract, snap)
        check_results.append(result.model_dump())

        if result.passed:
            total_passed += 1
        else:
            total_failed += 1
        
        max_risk = max(max_risk, result.risk_score)

    # 5. Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        for res_dict in check_results:
            res_dict['checked_at'] = res_dict['checked_at'].isoformat()
            f.write(json.dumps(res_dict) + "\n")

    log.info(f"Saved {len(check_results)} check result(s) to {output_path}")

    # Print summary
    log.info("=== Check Summary ===")
    log.info(f"Total checks: {len(check_results)}")
    log.info(f"Passed: {total_passed}")
    log.info(f"Failed: {total_failed}")
    log.info(f"Max risk score: {max_risk:.2f}")

    if max_risk >= 0.7:
        log.warning("HIGH RISK: Behavior regressions detected!")
    elif max_risk >= 0.3:
        log.warning("MEDIUM RISK: Review behavior changes")
    else:
        log.info("LOW RISK: Behavior within acceptable limits")

    if args.fail_on_violations and total_failed > 0:
        raise FeniksError(f"{total_failed} behavior check(s) failed")

    log.info("=== Behavior Check Complete ===")


def handle_behavior_define_scenario(args):
    """
    Define a new behavior scenario from YAML file.

    Loads scenario definition and stores it for later execution.

    Args:
        args.from_file: Path to scenario YAML file
        args.project_id: Project identifier
    """
    log.info("=== Define Behavior Scenario ===")
    log.info(f"Project: {args.project_id}")
    log.info(f"From file: {args.from_file}")

    file_path = Path(args.from_file)
    if not file_path.exists():
        raise FeniksError(f"Scenario file not found: {file_path}")

    # Load YAML
    with file_path.open("r") as f:
        scenario_data = yaml.safe_load(f)

    # TODO: Validate against BehaviorScenario model
    # TODO: Store in database/file system

    log.info(f"Scenario: {scenario_data.get('name', 'unnamed')}")
    log.info(f"Category: {scenario_data.get('category', 'unknown')}")
    log.info(f"Environment: {scenario_data.get('environment', 'unknown')}")

    log.warning("Scenario storage not yet implemented - this is a placeholder")
    log.info("To implement:")
    log.info("  1. Validate scenario_data against BehaviorScenario model")
    log.info("  2. Store in database (Postgres) or file system")
    log.info("  3. Return scenario ID")

    log.info("=== Define Scenario Complete ===")


def register_behavior_commands(subparsers):
    """
    Register 'behavior' command group with sub-commands.

    Args:
        subparsers: argparse subparsers object
    """
    # Main behavior command
    behavior_parser = subparsers.add_parser(
        "behavior", help="Legacy Behavior Guard commands (record, build-contracts, check)"
    )
    behavior_subparsers = behavior_parser.add_subparsers(dest="behavior_command")

    # behavior define-scenario
    define_parser = behavior_subparsers.add_parser(
        "define-scenario", help="Define a new behavior scenario from YAML file"
    )
    define_parser.add_argument("--project-id", type=str, required=True, help="Project identifier")
    define_parser.add_argument("--from-file", type=str, required=True, help="Path to scenario YAML file")
    define_parser.set_defaults(func=handle_behavior_define_scenario)

    # behavior record
    record_parser = behavior_subparsers.add_parser("record", help="Record behavior snapshots by executing scenarios")
    record_parser.add_argument("--project-id", type=str, required=True, help="Project identifier")
    record_parser.add_argument("--scenario-id", type=str, required=True, help="Scenario ID to execute")
    record_parser.add_argument(
        "--environment",
        type=str,
        choices=["legacy", "candidate", "staging", "production", "test"],
        default="legacy",
        help="Environment to execute in (default: legacy)",
    )
    record_parser.add_argument("--output", type=str, required=True, help="Output JSONL file for snapshots")
    record_parser.add_argument("--count", type=int, default=1, help="Number of times to execute scenario (default: 1)")
    record_parser.add_argument(
        "--language", 
        type=str, 
        choices=["python", "php", "typescript", "javascript", "generic"], 
        default="generic", 
        help="Target language for the runner"
    )
    record_parser.add_argument("--command-to-run", type=str, help="Explicit command to execute (e.g. 'pytest -v')")
    record_parser.set_defaults(func=handle_behavior_record)

    # behavior build-contracts
    build_parser = behavior_subparsers.add_parser(
        "build-contracts", help="Build behavior contracts from recorded snapshots"
    )
    build_parser.add_argument("--project-id", type=str, required=True, help="Project identifier")
    build_parser.add_argument("--input", type=str, required=True, help="Input JSONL file with snapshots")
    build_parser.add_argument("--output", type=str, required=True, help="Output JSONL file for contracts")
    build_parser.add_argument(
        "--min-snapshots", type=int, default=3, help="Minimum snapshots required per scenario (default: 3)"
    )
    build_parser.set_defaults(func=handle_behavior_build_contracts)

    # behavior check
    check_parser = behavior_subparsers.add_parser("check", help="Check candidate system behavior against contracts")
    check_parser.add_argument("--project-id", type=str, required=True, help="Project identifier")
    check_parser.add_argument("--contracts", type=str, required=True, help="Input JSONL file with behavior contracts")
    check_parser.add_argument("--snapshots", type=str, required=True, help="Input JSONL file with candidate snapshots")
    check_parser.add_argument("--output", type=str, required=True, help="Output JSONL file for check results")
    check_parser.add_argument(
        "--fail-on-violations", action="store_true", help="Exit with error code if violations found"
    )
    check_parser.set_defaults(func=handle_behavior_check)
