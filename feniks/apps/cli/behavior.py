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

from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("cli.behavior")


def handle_behavior_record(args):
    """
    Record behavior snapshots for a scenario.

    Executes a behavior scenario and captures snapshots (HTTP responses,
    DOM state, logs) for legacy system behavior analysis.

    Args:
        args.project_id: Project identifier
        args.scenario_id: Scenario ID to execute
        args.environment: Environment (legacy/candidate/staging/production)
        args.output: Output JSONL file for snapshots
        args.count: Number of times to execute scenario (default: 1)
    """
    log.info("=== Behavior Record ===")
    log.info(f"Project: {args.project_id}")
    log.info(f"Scenario: {args.scenario_id}")
    log.info(f"Environment: {args.environment}")
    log.info(f"Output: {args.output}")
    log.info(f"Executions: {args.count}")

    # TODO: Implement actual scenario execution
    # This is a placeholder for the MVP - real implementation would:
    # 1. Load scenario from database/file
    # 2. Execute scenario (UI via Playwright, API via requests, CLI via subprocess)
    # 3. Capture observations (HTTP, DOM, logs)
    # 4. Create BehaviorSnapshot
    # 5. Save to JSONL

    log.warning("Behavior recording not yet implemented - this is a placeholder")
    log.info("To implement:")
    log.info("  1. Load BehaviorScenario from storage")
    log.info("  2. Execute scenario runner (UI/API/CLI)")
    log.info("  3. Capture observations")
    log.info("  4. Save BehaviorSnapshot to JSONL")

    # Create placeholder output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    placeholder_snapshot = {
        "id": f"snapshot-{args.scenario_id}-{datetime.now().isoformat()}",
        "scenario_id": args.scenario_id,
        "project_id": args.project_id,
        "environment": args.environment,
        "success": True,
        "created_at": datetime.now().isoformat(),
        "note": "PLACEHOLDER - implement actual scenario execution",
    }

    with output_path.open("w") as f:
        f.write(json.dumps(placeholder_snapshot) + "\n")

    log.info(f"Placeholder snapshot saved to {output_path}")
    log.info("=== Record Complete ===")


def handle_behavior_build_contracts(args):
    """
    Build behavior contracts from recorded snapshots.

    Analyzes multiple BehaviorSnapshots to derive generalized
    BehaviorContracts that define expected system behavior.

    Args:
        args.project_id: Project identifier
        args.input: Input JSONL file with snapshots
        args.output: Output JSONL file for contracts
        args.min_snapshots: Minimum snapshots required per scenario (default: 3)
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
    snapshots = []
    with input_path.open("r") as f:
        for line in f:
            snapshot_data = json.loads(line)
            # TODO: Validate and parse as BehaviorSnapshot
            snapshots.append(snapshot_data)

    log.info(f"Loaded {len(snapshots)} snapshot(s)")

    # Group by scenario_id
    scenarios_map = {}
    for snapshot in snapshots:
        scenario_id = snapshot.get("scenario_id")
        if scenario_id not in scenarios_map:
            scenarios_map[scenario_id] = []
        scenarios_map[scenario_id].append(snapshot)

    log.info(f"Found {len(scenarios_map)} unique scenario(s)")

    # Build contracts
    contracts = []
    for scenario_id, scenario_snapshots in scenarios_map.items():
        if len(scenario_snapshots) < args.min_snapshots:
            log.warning(
                f"Scenario {scenario_id}: only {len(scenario_snapshots)} snapshot(s), "
                f"minimum {args.min_snapshots} required. Skipping."
            )
            continue

        log.info(f"Building contract for scenario {scenario_id} from {len(scenario_snapshots)} snapshot(s)")

        # TODO: Implement actual contract generation logic
        # This would analyze snapshots to find:
        # - Common HTTP status codes
        # - Required DOM elements
        # - Forbidden log patterns
        # - Performance thresholds (p95, p99)

        contract = {
            "id": f"contract-{scenario_id}-{datetime.now().isoformat()}",
            "scenario_id": scenario_id,
            "project_id": args.project_id,
            "version": "1.0.0",
            "derived_from_snapshot_ids": [s["id"] for s in scenario_snapshots],
            "created_at": datetime.now().isoformat(),
            "note": "PLACEHOLDER - implement actual contract generation",
        }
        contracts.append(contract)

    # Save contracts
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        for contract in contracts:
            f.write(json.dumps(contract) + "\n")

    log.info(f"Saved {len(contracts)} contract(s) to {output_path}")
    log.info("=== Build Contracts Complete ===")


def handle_behavior_check(args):
    """
    Check new system behavior against contracts.

    Compares BehaviorSnapshots from candidate system against
    BehaviorContracts to detect regressions.

    Args:
        args.project_id: Project identifier
        args.contracts: Input JSONL file with contracts
        args.snapshots: Input JSONL file with candidate snapshots
        args.output: Output JSONL file for check results
        args.fail_on_violations: Exit with error code if violations found
    """
    log.info("=== Behavior Check ===")
    log.info(f"Project: {args.project_id}")
    log.info(f"Contracts: {args.contracts}")
    log.info(f"Snapshots: {args.snapshots}")
    log.info(f"Output: {args.output}")

    # Load contracts
    contracts_path = Path(args.contracts)
    if not contracts_path.exists():
        raise FeniksError(f"Contracts file not found: {contracts_path}")

    contracts = []
    with contracts_path.open("r") as f:
        for line in f:
            contract_data = json.loads(line)
            contracts.append(contract_data)

    log.info(f"Loaded {len(contracts)} contract(s)")

    # Load snapshots
    snapshots_path = Path(args.snapshots)
    if not snapshots_path.exists():
        raise FeniksError(f"Snapshots file not found: {snapshots_path}")

    snapshots = []
    with snapshots_path.open("r") as f:
        for line in f:
            snapshot_data = json.loads(line)
            snapshots.append(snapshot_data)

    log.info(f"Loaded {len(snapshots)} snapshot(s)")

    # Build scenario_id -> contract mapping
    contracts_map = {c["scenario_id"]: c for c in contracts}

    # Check each snapshot
    check_results = []
    total_passed = 0
    total_failed = 0
    max_risk = 0.0

    for snapshot in snapshots:
        scenario_id = snapshot.get("scenario_id")
        contract = contracts_map.get(scenario_id)

        if not contract:
            log.warning(f"No contract found for scenario {scenario_id}, skipping")
            continue

        # TODO: Implement actual comparison logic
        # This would:
        # 1. Compare HTTP status codes
        # 2. Check DOM elements presence/absence
        # 3. Match log patterns
        # 4. Calculate risk score based on violations

        # Placeholder check (always passes)
        passed = snapshot.get("success", True)
        risk_score = 0.0 if passed else 0.5

        check_result = {
            "snapshot_id": snapshot["id"],
            "contract_id": contract["id"],
            "project_id": args.project_id,
            "passed": passed,
            "violations": [],
            "risk_score": risk_score,
            "checked_at": datetime.now().isoformat(),
            "note": "PLACEHOLDER - implement actual behavior comparison",
        }

        check_results.append(check_result)

        if passed:
            total_passed += 1
        else:
            total_failed += 1

        max_risk = max(max_risk, risk_score)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        for result in check_results:
            f.write(json.dumps(result) + "\n")

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

    # Fail if violations and flag set
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
