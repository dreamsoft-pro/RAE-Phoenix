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
Refactor Engine - Orchestrates refactoring workflows.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.patch_generator import PatchGenerator
from feniks.core.refactor.recipe import RefactorPlan, RefactorRecipe, RefactorResult
from feniks.core.refactor.recipes import ExtractFunctionRecipe, ReduceComplexityRecipe
from feniks.core.refactor.recipes.javascript import AngularMigrationRecipe
from feniks.core.refactor.recipes.php import PhpEnterpriseRecipe
from feniks.core.refactor.recipes.python import PythonPipelineRecipe
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("refactor.engine")


class RefactorEngine:
    """
    Engine for executing refactoring workflows.

    Orchestrates:
    - Recipe selection
    - Analysis and planning
    - Execution (dry-run or actual)
    - Patch generation
    - Validation
    - Audit trail generation
    """

    def __init__(self):
        """Initialize the refactor engine."""
        self.recipes: Dict[str, RefactorRecipe] = {}
        self.patch_generator = PatchGenerator()
        self._register_builtin_recipes()
        log.info("RefactorEngine initialized")

    def _register_builtin_recipes(self):
        """Register built-in refactoring recipes."""
        builtin_recipes = [
            ReduceComplexityRecipe(),
            ExtractFunctionRecipe(),
            PythonPipelineRecipe(),
            PhpEnterpriseRecipe(),
            AngularMigrationRecipe(),
        ]

        for recipe in builtin_recipes:
            self.register_recipe(recipe)

    def register_recipe(self, recipe: RefactorRecipe):
        """
        Register a refactoring recipe.

        Args:
            recipe: The recipe to register
        """
        self.recipes[recipe.name] = recipe
        log.info(f"Registered recipe: {recipe.name}")

    def list_recipes(self) -> List[Dict[str, str]]:
        """
        List all available recipes.

        Returns:
            List of recipe information dicts
        """
        return [
            {"name": recipe.name, "description": recipe.description, "risk_level": recipe.risk_level.value}
            for recipe in self.recipes.values()
        ]

    def analyze(
        self, recipe_name: str, system_model: SystemModel, target: Optional[Dict[str, Any]] = None
    ) -> Optional[RefactorPlan]:
        """
        Analyze system and create refactoring plan.

        Args:
            recipe_name: Name of the recipe to use
            system_model: The system model
            target: Optional targeting information

        Returns:
            RefactorPlan or None if no refactoring needed

        Raises:
            FeniksError: If recipe not found
        """
        if recipe_name not in self.recipes:
            raise FeniksError(f"Recipe not found: {recipe_name}. Available: {list(self.recipes.keys())}")

        recipe = self.recipes[recipe_name]
        log.info(f"Analyzing with recipe: {recipe_name}")

        plan = recipe.analyze(system_model, target)

        if plan:
            log.info(f"Created plan: {plan.rationale}")
            log.info(f"  Target modules: {len(plan.target_modules)}")
            log.info(f"  Target files: {len(plan.target_files)}")
            log.info(f"  Risk level: {plan.risk_level.value}")
        else:
            log.info("No refactoring plan created (no candidates found)")

        return plan

    def execute(
        self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True, output_dir: Optional[Path] = None
    ) -> RefactorResult:
        """
        Execute refactoring based on plan.

        Args:
            plan: The refactoring plan
            chunks: Code chunks to refactor
            dry_run: If True, don't modify files, just generate patches
            output_dir: Directory for output artifacts (patches, reports)

        Returns:
            RefactorResult with changes and validation

        Raises:
            FeniksError: If recipe not found or execution fails
        """
        if plan.recipe_name not in self.recipes:
            raise FeniksError(f"Recipe not found: {plan.recipe_name}")

        recipe = self.recipes[plan.recipe_name]
        log.info(f"Executing refactoring: {plan.recipe_name} (dry_run={dry_run})")

        # Execute recipe
        result = recipe.execute(plan, chunks, dry_run=dry_run)

        # Generate patch if there are changes
        if result.file_changes and output_dir:
            try:
                patch_path = self.patch_generator.generate_patch(result, output_dir=output_dir)
                result.patch_path = patch_path
                log.info(f"Generated patch: {patch_path}")
            except Exception as e:
                error_msg = f"Failed to generate patch: {e}"
                log.error(error_msg)
                result.errors.append(error_msg)

        # Validate
        validation_passed = recipe.validate(result)
        log.info(f"Validation: {'passed' if validation_passed else 'failed'}")

        # Generate meta-reflection
        meta_reflection = recipe.generate_meta_reflection(result)
        result.metadata["meta_reflection"] = meta_reflection

        return result

    def run_workflow(
        self,
        recipe_name: str,
        system_model: SystemModel,
        chunks: List[Chunk],
        target: Optional[Dict[str, Any]] = None,
        dry_run: bool = True,
        output_dir: Optional[Path] = None,
    ) -> Optional[RefactorResult]:
        """
        Run complete refactoring workflow: analyze → execute → validate.

        Args:
            recipe_name: Name of the recipe to use
            system_model: The system model
            chunks: Code chunks
            target: Optional targeting information
            dry_run: If True, don't modify files
            output_dir: Directory for output artifacts

        Returns:
            RefactorResult or None if no refactoring needed

        Raises:
            FeniksError: If workflow fails
        """
        log.info(f"Running refactoring workflow: {recipe_name}")

        # Step 1: Analyze
        plan = self.analyze(recipe_name, system_model, target)
        if not plan:
            log.info("No refactoring needed")
            return None

        # Step 2: Execute
        result = self.execute(plan, chunks, dry_run=dry_run, output_dir=output_dir)

        # Step 3: Generate report
        if output_dir:
            self._generate_report(result, output_dir)

        log.info(f"Workflow completed: {result.total_changes} changes")
        return result

    def _generate_report(self, result: RefactorResult, output_dir: Path):
        """
        Generate refactoring report.

        Args:
            result: The refactoring result
            output_dir: Directory for output
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"refactor_report_{result.plan.recipe_name}.md"

        lines = []
        lines.append(f"# Refactoring Report: {result.plan.recipe_name}")
        lines.append("")
        lines.append(f"**Project:** {result.plan.project_id}")
        lines.append(f"**Status:** {'✓ Success' if result.success else '✗ Failed'}")
        lines.append(f"**Risk Level:** {result.plan.risk_level.value.upper()}")
        lines.append("")

        lines.append("## Rationale")
        lines.append(result.plan.rationale)
        lines.append("")

        lines.append("## Target Scope")
        lines.append(f"- **Modules:** {', '.join(result.plan.target_modules)}")
        lines.append(f"- **Files:** {len(result.plan.target_files)}")
        lines.append("")

        lines.append("## Changes")
        lines.append(f"- **Total changes:** {result.total_changes}")
        lines.append(f"- **Estimated:** {result.plan.estimated_changes}")
        lines.append("- **Changed files:**")
        for file_path in result.changed_files:
            lines.append(f"  - {file_path}")
        lines.append("")

        if result.patch_path:
            lines.append("## Patch")
            lines.append(f"Patch file: `{result.patch_path.name}`")
            lines.append("")

        lines.append("## Risks")
        for risk in result.plan.risks:
            lines.append(f"- ⚠️  {risk}")
        lines.append("")

        lines.append("## Validation Steps")
        for step in result.plan.validation_steps:
            lines.append(f"- [ ] {step}")
        lines.append("")

        if result.validation_results:
            lines.append("## Validation Results")
            for key, value in result.validation_results.items():
                status = "✓" if value else "✗"
                lines.append(f"- {status} {key}: {value}")
            lines.append("")

        if result.errors:
            lines.append("## Errors")
            for error in result.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")

        if result.warnings:
            lines.append("## Warnings")
            for warning in result.warnings:
                lines.append(f"- ⚠️  {warning}")
            lines.append("")

        # Write report
        with report_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        log.info(f"Generated report: {report_path}")
