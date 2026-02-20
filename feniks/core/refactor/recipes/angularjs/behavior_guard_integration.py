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
Behavior Guard Integration for AngularJS Migration.

Provides integration between AngularJS recipe pack and Legacy Behavior Guard
to enable automated testing of migrations.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from feniks.core.refactor.recipe import RefactorPlan, RefactorResult
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.angularjs.behavior_guard_integration")


@dataclass
class MigrationTestPlan:
    """Test plan for migration validation."""

    project_id: str
    legacy_routes: List[Dict[str, str]]  # path -> component mapping
    migrated_routes: List[Dict[str, str]]  # path -> component mapping
    scenarios: List[str]  # Scenario IDs to test
    risk_threshold: float = 0.3


class BehaviorGuardIntegration:
    """
    Integrates AngularJS recipes with Legacy Behavior Guard.

    Workflow:
    1. Before migration: Record behavior contracts from AngularJS app
    2. Apply migration recipes
    3. After migration: Validate against behavior contracts
    4. Generate regression report
    """

    def __init__(self):
        """Initialize the integration."""
        self.logger = get_logger("behavior_guard_integration")

    def create_test_plan(self, refactor_result: RefactorResult) -> MigrationTestPlan:
        """
        Create a test plan from refactoring result.

        Args:
            refactor_result: The refactoring result

        Returns:
            MigrationTestPlan with test scenarios
        """
        self.logger.info("Creating behavior test plan from refactoring result")

        # Extract route mappings
        route_mapping = refactor_result.metadata.get("route_mapping", {})
        component_mapping = refactor_result.metadata.get("component_mapping", {})

        legacy_routes = []
        migrated_routes = []

        # Build route mappings
        for legacy_path, mapping in route_mapping.items():
            legacy_routes.append(
                {"path": legacy_path, "controller": mapping.get("controller"), "template": mapping.get("template")}
            )

            migrated_routes.append({"path": mapping.get("nextPath"), "component": mapping.get("file")})

        # Build component mappings
        for controller_name, mapping in component_mapping.items():
            if "controller" in mapping and "component" in mapping:
                legacy_routes.append(
                    {
                        "path": f"/component/{controller_name}",
                        "controller": mapping["controller"],
                        "template": mapping.get("template"),
                    }
                )

                migrated_routes.append({"path": f"/component/{controller_name}", "component": mapping["component"]})

        # Generate scenarios for each route
        scenarios = self._generate_scenarios(legacy_routes)

        plan = MigrationTestPlan(
            project_id=refactor_result.plan.project_id,
            legacy_routes=legacy_routes,
            migrated_routes=migrated_routes,
            scenarios=scenarios,
            risk_threshold=self._calculate_risk_threshold(refactor_result.plan),
        )

        self.logger.info(f"Created test plan with {len(scenarios)} scenarios")
        return plan

    def generate_behavior_scenarios(self, test_plan: MigrationTestPlan, output_path: str) -> str:
        """
        Generate Behavior Guard scenario YAML files.

        Args:
            test_plan: The test plan
            output_path: Directory to save scenarios

        Returns:
            Path to generated scenarios
        """
        self.logger.info(f"Generating behavior scenarios to {output_path}")

        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        scenarios_generated = []

        for i, scenario_id in enumerate(test_plan.scenarios):
            # Find corresponding route
            route_idx = i % len(test_plan.legacy_routes)
            legacy_route = test_plan.legacy_routes[route_idx]
            migrated_route = (
                test_plan.migrated_routes[route_idx] if route_idx < len(test_plan.migrated_routes) else None
            )

            # Generate scenario YAML
            scenario_yaml = self._generate_scenario_yaml(scenario_id, legacy_route, migrated_route, test_plan)

            # Write to file
            scenario_file = output_dir / f"{scenario_id}.yaml"
            scenario_file.write_text(scenario_yaml)

            scenarios_generated.append(str(scenario_file))

            self.logger.debug(f"Generated scenario: {scenario_file}")

        self.logger.info(f"Generated {len(scenarios_generated)} scenario files")
        return str(output_dir)

    def generate_test_script(self, test_plan: MigrationTestPlan, output_path: str) -> str:
        """
        Generate a test script for running behavior validation.

        Args:
            test_plan: The test plan
            output_path: Path to save the script

        Returns:
            Path to generated script
        """
        self.logger.info(f"Generating test script to {output_path}")

        script_content = f"""#!/bin/bash
# Generated by Feniks - AngularJS Migration Test Script
# Project: {test_plan.project_id}

set -e

PROJECT_ID="{test_plan.project_id}"
RISK_THRESHOLD={test_plan.risk_threshold}

echo "=== AngularJS Migration Behavior Validation ==="
echo "Project: $PROJECT_ID"
echo "Risk Threshold: $RISK_THRESHOLD"
echo ""

# Step 1: Record legacy behavior (if not already done)
if [ ! -f "legacy_snapshots.jsonl" ]; then
    echo "Recording legacy behavior..."
    feniks behavior record \\
        --project-id "$PROJECT_ID" \\
        --scenario-id all \\
        --environment legacy \\
        --output legacy_snapshots.jsonl
else
    echo "Using existing legacy snapshots"
fi

# Step 2: Build behavior contracts
echo ""
echo "Building behavior contracts..."
feniks behavior build-contracts \\
    --project-id "$PROJECT_ID" \\
    --input legacy_snapshots.jsonl \\
    --output contracts.jsonl

# Step 3: Record migrated behavior
echo ""
echo "Recording migrated behavior..."
feniks behavior record \\
    --project-id "$PROJECT_ID" \\
    --scenario-id all \\
    --environment migrated \\
    --output migrated_snapshots.jsonl

# Step 4: Check for regressions
echo ""
echo "Checking for regressions..."
feniks behavior check \\
    --project-id "$PROJECT_ID" \\
    --contracts contracts.jsonl \\
    --snapshots migrated_snapshots.jsonl \\
    --output results.jsonl \\
    --fail-on-violations \\
    --risk-threshold $RISK_THRESHOLD

# Step 5: Generate report
echo ""
echo "Generating report..."
feniks behavior report \\
    --project-id "$PROJECT_ID" \\
    --results results.jsonl \\
    --output migration_validation_report.md

echo ""
echo "=== Validation Complete ==="
echo "Report: migration_validation_report.md"
"""

        # Write script
        script_path = Path(output_path)
        script_path.write_text(script_content)
        script_path.chmod(0o755)  # Make executable

        self.logger.info(f"Generated test script: {script_path}")
        return str(script_path)

    def generate_integration_guide(self, output_path: str) -> str:
        """
        Generate integration guide for using Behavior Guard with migrations.

        Args:
            output_path: Path to save the guide

        Returns:
            Path to generated guide
        """
        guide_content = """# Behavior Guard Integration Guide

## Overview

This guide explains how to use Legacy Behavior Guard to validate AngularJS migrations.

## Workflow

### 1. Before Migration: Record Baseline

First, record the behavior of your AngularJS application:

```bash
# Start your legacy AngularJS app (e.g., on http://localhost:4200)
npm start

# In another terminal, record behavior
feniks behavior record \\
    --project-id my-app \\
    --scenario-id all \\
    --environment legacy \\
    --output legacy_snapshots.jsonl
```

### 2. Apply Migration Recipes

Run the AngularJS migration recipes:

```python
from feniks.core.refactor.recipes.angularjs import (
    ControllerToComponentRecipe,
    TemplateToJsxRecipe,
    RoutingToAppRouterRecipe
)

# Apply recipes...
```

### 3. After Migration: Validate

Build contracts and validate the migrated application:

```bash
# Build behavior contracts from baseline
feniks behavior build-contracts \\
    --project-id my-app \\
    --input legacy_snapshots.jsonl \\
    --output contracts.jsonl

# Start your migrated Next.js app (e.g., on http://localhost:3000)
npm run dev

# Record migrated behavior
feniks behavior record \\
    --project-id my-app \\
    --scenario-id all \\
    --environment migrated \\
    --output migrated_snapshots.jsonl

# Check for regressions
feniks behavior check \\
    --project-id my-app \\
    --contracts contracts.jsonl \\
    --snapshots migrated_snapshots.jsonl \\
    --output results.jsonl \\
    --fail-on-violations \\
    --risk-threshold 0.3
```

### 4. Review Results

Generate and review the validation report:

```bash
feniks behavior report \\
    --project-id my-app \\
    --results results.jsonl \\
    --output migration_report.md
```

## Scenario Configuration

Create scenarios for your critical user flows:

```yaml
# scenarios/user-login.yaml
id: user-login
name: User Login Flow
type: ui
environment: both  # Run on both legacy and migrated

steps:
  - action: navigate
    url: /login

  - action: input
    selector: "#username"
    value: "testuser"

  - action: input
    selector: "#password"
    value: "testpass"

  - action: click
    selector: "#login-button"

  - action: wait
    selector: "#dashboard"

assertions:
  - type: url_matches
    pattern: /dashboard

  - type: element_exists
    selector: "#user-menu"
```

## Risk Thresholds

Adjust risk thresholds based on migration phase:

- **0.1 (Strict)**: For critical flows (checkout, payments)
- **0.3 (Balanced)**: For general flows
- **0.5 (Lenient)**: For cosmetic changes

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/migration-test.yml
name: Migration Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Feniks
        run: pip install -e .

      - name: Run Behavior Validation
        run: ./test_migration.sh
```

## Best Practices

1. **Record baseline early**: Capture behavior before starting migration
2. **Test incrementally**: Validate each recipe separately
3. **Focus on critical paths**: Prioritize user-facing flows
4. **Review violations**: Not all differences are bugs - some are improvements
5. **Update contracts**: As you verify changes are correct, update contracts

## Troubleshooting

### High False Positive Rate

If you get many false positives:

- Increase risk threshold
- Exclude cosmetic differences
- Update selectors to be more resilient

### Missing Scenarios

If coverage is low:

- Add more scenario files
- Use behavior recorder in interactive mode
- Capture actual user sessions

### Performance Issues

If validation is slow:

- Run scenarios in parallel
- Use headless browser mode
- Reduce assertion complexity

---

For more information, see:
- [Legacy Behavior Guard Documentation](../LEGACY_BEHAVIOR_GUARD.md)
- [Recipe Pack Documentation](../Feniks–Recipe_Pack_AngularJS_1-3.md)
"""

        guide_path = Path(output_path)
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        guide_path.write_text(guide_content)

        self.logger.info(f"Generated integration guide: {guide_path}")
        return str(guide_path)

    # Helper methods

    def _generate_scenarios(self, routes: List[Dict[str, str]]) -> List[str]:
        """Generate scenario IDs for routes."""
        scenarios = []

        for i, route in enumerate(routes):
            path = route.get("path", "")
            # Create scenario ID from path
            scenario_id = path.strip("/").replace("/", "-").replace(":", "") or "home"
            scenarios.append(f"scenario-{scenario_id}-{i}")

        return scenarios

    def _calculate_risk_threshold(self, plan: RefactorPlan) -> float:
        """Calculate appropriate risk threshold based on plan."""
        # Higher risk refactorings get lower threshold (stricter)
        risk_map = {"LOW": 0.5, "MEDIUM": 0.3, "HIGH": 0.1, "CRITICAL": 0.05}

        return risk_map.get(plan.risk_level.value.upper(), 0.3)

    def _generate_scenario_yaml(
        self,
        scenario_id: str,
        legacy_route: Dict[str, str],
        migrated_route: Optional[Dict[str, str]],
        test_plan: MigrationTestPlan,
    ) -> str:
        """Generate scenario YAML content."""
        path = legacy_route.get("path", "/")

        yaml_content = f"""# Generated by Feniks - Behavior Scenario
id: {scenario_id}
name: Validate {path}
type: ui
environment: both

steps:
  - action: navigate
    url: {path}

  - action: wait
    timeout: 5000

  - action: screenshot
    name: page-loaded

assertions:
  - type: status_code
    expected: 200

  - type: no_console_errors

  - type: element_exists
    selector: "body"
    description: Page should render

metadata:
  legacy_controller: {legacy_route.get('controller', 'N/A')}
  legacy_template: {legacy_route.get('template', 'N/A')}
  migrated_component: {migrated_route.get('component', 'N/A') if migrated_route else 'N/A'}
  risk_threshold: {test_plan.risk_threshold}
"""

        return yaml_content
