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
Reduce Complexity Recipe - Reduces cyclomatic complexity in modules.
"""
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.reduce_complexity")


class ReduceComplexityRecipe(RefactorRecipe):
    """
    Recipe for reducing cyclomatic complexity in modules.

    Targets modules with high complexity and suggests:
    - Extracting complex functions into smaller ones
    - Simplifying conditional logic
    - Removing nested structures
    """

    @property
    def name(self) -> str:
        return "reduce_complexity"

    @property
    def description(self) -> str:
        return "Reduce cyclomatic complexity in high-complexity modules"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        """
        Analyze system model to find high-complexity modules.

        Args:
            system_model: The system model
            target: Optional dict with 'module_name' or 'complexity_threshold'

        Returns:
            RefactorPlan or None
        """
        log.info(f"Analyzing complexity for project: {system_model.project_id}")

        # Determine complexity threshold
        if target and "complexity_threshold" in target:
            threshold = target["complexity_threshold"]
        else:
            # Use 1.5x average complexity as threshold
            threshold = system_model.avg_module_complexity * 1.5

        # Find high-complexity modules
        high_complexity_modules = []
        target_files = []

        for module_name, module in system_model.modules.items():
            if module.avg_complexity > threshold:
                # Check if specific module was targeted
                if target and "module_name" in target:
                    if module_name != target["module_name"]:
                        continue

                high_complexity_modules.append(module_name)
                target_files.extend(module.file_paths)

        if not high_complexity_modules:
            log.info("No high-complexity modules found")
            return None

        # Create refactoring plan
        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=high_complexity_modules,
            target_files=list(set(target_files)),
            rationale=f"Reduce complexity in {len(high_complexity_modules)} modules with complexity > {threshold:.1f}",
            risks=[
                "May introduce bugs if logic is incorrectly extracted",
                "Extracted functions may need additional testing",
                "Changes may affect module interfaces",
            ],
            risk_level=self.risk_level,
            estimated_changes=len(high_complexity_modules) * 5,  # ~5 changes per module
            validation_steps=[
                "Verify all tests pass after refactoring",
                "Check that complexity metrics improved",
                "Review extracted functions for correctness",
                "Ensure no functionality was lost",
            ],
            metadata={"complexity_threshold": threshold, "avg_system_complexity": system_model.avg_module_complexity},
        )

        log.info(f"Created refactoring plan for {len(high_complexity_modules)} modules")
        return plan

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        """
        Execute complexity reduction refactoring.

        Args:
            plan: The refactoring plan
            chunks: Code chunks to refactor
            dry_run: If True, generate suggestions without modifying files

        Returns:
            RefactorResult with suggested changes
        """
        log.info(f"Executing complexity reduction (dry_run={dry_run})")

        result = RefactorResult(plan=plan, success=True, file_changes=[], validation_results={}, errors=[], warnings=[])

        # Group chunks by file
        chunks_by_file = {}
        for chunk in chunks:
            # Only process chunks from target modules
            if chunk.module not in plan.target_modules:
                continue

            if chunk.file_path not in chunks_by_file:
                chunks_by_file[chunk.file_path] = []
            chunks_by_file[chunk.file_path].append(chunk)

        # Process each file
        for file_path, file_chunks in chunks_by_file.items():
            try:
                file_change = self._process_file(file_path, file_chunks, dry_run)
                if file_change:
                    result.file_changes.append(file_change)
            except Exception as e:
                error_msg = f"Failed to process {file_path}: {e}"
                log.error(error_msg)
                result.errors.append(error_msg)
                result.success = False

        # Add warnings for high-risk changes
        if len(result.file_changes) > plan.estimated_changes * 1.5:
            result.warnings.append(
                f"Number of changes ({len(result.file_changes)}) significantly exceeds estimate ({plan.estimated_changes})"
            )

        log.info(f"Refactoring completed: {len(result.file_changes)} files changed")
        return result

    def _process_file(self, file_path: str, chunks: List[Chunk], dry_run: bool) -> Optional[FileChange]:
        """
        Process a single file for complexity reduction.

        Args:
            file_path: Path to the file
            chunks: Chunks from this file
            dry_run: Whether this is a dry run

        Returns:
            FileChange or None if no changes needed
        """
        # Find high-complexity chunks
        high_complexity_chunks = [c for c in chunks if c.cyclomatic_complexity > 15]  # Threshold for single function

        if not high_complexity_chunks:
            return None

        # Generate suggestions (in a real implementation, this would use AST analysis)
        suggestions = []
        for chunk in high_complexity_chunks:
            suggestions.append(
                f"// TODO: Refactor {chunk.chunk_name} (complexity: {chunk.cyclomatic_complexity})\n"
                f"// Consider extracting complex logic into separate functions\n"
                f"// Simplify conditional structures\n"
            )

        # Create file change with suggestions
        file_change = FileChange(
            file_path=file_path,
            original_content="",  # Would be loaded from file in real implementation
            modified_content="",  # Would contain actual refactored code
            change_type="modify",
            line_changes=[],
        )

        # Store suggestions in metadata
        file_change.line_changes = [
            (chunk.start_line, chunk.end_line, suggestion)
            for chunk, suggestion in zip(high_complexity_chunks, suggestions)
        ]

        return file_change

    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the refactoring result.

        Args:
            result: The refactoring result

        Returns:
            bool: True if validation passed
        """
        log.info("Validating complexity reduction")

        # Basic validations
        validations = {
            "has_changes": len(result.file_changes) > 0,
            "no_critical_errors": len(result.errors) == 0,
            "within_expected_scope": len(result.file_changes) <= result.plan.estimated_changes * 2,
        }

        result.validation_results = validations
        all_passed = all(validations.values())

        log.info(f"Validation {'passed' if all_passed else 'failed'}: {validations}")
        return all_passed
