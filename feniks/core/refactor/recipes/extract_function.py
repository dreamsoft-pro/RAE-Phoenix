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
Extract Function Recipe - Extracts reusable logic into separate functions.
"""
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.extract_function")


class ExtractFunctionRecipe(RefactorRecipe):
    """
    Recipe for extracting duplicated or complex logic into separate functions.

    Targets:
    - Duplicated code patterns
    - Long functions (>50 lines)
    - Functions with multiple responsibilities
    """

    @property
    def name(self) -> str:
        return "extract_function"

    @property
    def description(self) -> str:
        return "Extract duplicated or complex logic into separate functions"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        """
        Analyze system model to find extraction opportunities.

        Args:
            system_model: The system model
            target: Optional dict with 'module_name' or 'min_lines'

        Returns:
            RefactorPlan or None
        """
        log.info(f"Analyzing for function extraction: {system_model.project_id}")

        # Determine line threshold
        min_lines = target.get("min_lines", 50) if target else 50

        # Find candidates for extraction
        candidate_modules = []
        target_files = []

        for module_name, module in system_model.modules.items():
            # Check if module has high complexity or many chunks
            if module.avg_complexity > 10 or module.chunk_count > 5:
                # Check if specific module was targeted
                if target and "module_name" in target:
                    if module_name != target["module_name"]:
                        continue

                candidate_modules.append(module_name)
                target_files.extend(module.file_paths)

        if not candidate_modules:
            log.info("No extraction candidates found")
            return None

        # Create refactoring plan
        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=candidate_modules,
            target_files=list(set(target_files)),
            rationale=f"Extract functions from {len(candidate_modules)} modules to improve modularity",
            risks=[
                "May break existing function calls if signature changes",
                "Extracted functions need proper naming and documentation",
                "May affect module coupling if not done carefully",
            ],
            risk_level=self.risk_level,
            estimated_changes=len(candidate_modules) * 3,  # ~3 extractions per module
            validation_steps=[
                "Verify all function calls are updated",
                "Check that extracted functions have proper parameters",
                "Ensure no side effects were lost",
                "Validate tests still pass",
            ],
            metadata={"min_lines": min_lines, "candidate_count": len(candidate_modules)},
        )

        log.info(f"Created extraction plan for {len(candidate_modules)} modules")
        return plan

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        """
        Execute function extraction refactoring.

        Args:
            plan: The refactoring plan
            chunks: Code chunks to refactor
            dry_run: If True, generate suggestions without modifying files

        Returns:
            RefactorResult with suggested extractions
        """
        log.info(f"Executing function extraction (dry_run={dry_run})")

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

        log.info(f"Extraction completed: {len(result.file_changes)} files changed")
        return result

    def _process_file(self, file_path: str, chunks: List[Chunk], dry_run: bool) -> Optional[FileChange]:
        """
        Process a single file for function extraction.

        Args:
            file_path: Path to the file
            chunks: Chunks from this file
            dry_run: Whether this is a dry run

        Returns:
            FileChange or None if no changes needed
        """
        # Find chunks that are good extraction candidates
        # - High complexity
        # - Many lines
        # - Multiple dependencies (might be doing too much)

        extraction_candidates = [
            chunk
            for chunk in chunks
            if (
                chunk.cyclomatic_complexity > 10
                or (chunk.end_line - chunk.start_line) > 50
                or len(chunk.dependencies) > 5
            )
        ]

        if not extraction_candidates:
            return None

        # Generate extraction suggestions
        suggestions = []
        for chunk in extraction_candidates:
            reason = []
            if chunk.cyclomatic_complexity > 10:
                reason.append(f"high complexity ({chunk.cyclomatic_complexity})")
            if (chunk.end_line - chunk.start_line) > 50:
                reason.append(f"long function ({chunk.end_line - chunk.start_line} lines)")
            if len(chunk.dependencies) > 5:
                reason.append(f"many dependencies ({len(chunk.dependencies)})")

            suggestions.append(
                f"// TODO: Consider extracting from {chunk.chunk_name}\n"
                f"// Reason: {', '.join(reason)}\n"
                f"// Suggested extractions:\n"
                f"//   - Extract helper functions for complex logic\n"
                f"//   - Separate data transformation from business logic\n"
                f"//   - Move reusable code to utility functions\n"
            )

        # Create file change with suggestions
        file_change = FileChange(
            file_path=file_path, original_content="", modified_content="", change_type="modify", line_changes=[]
        )

        # Store suggestions
        file_change.line_changes = [
            (chunk.start_line, chunk.end_line, suggestion)
            for chunk, suggestion in zip(extraction_candidates, suggestions)
        ]

        return file_change

    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the extraction result.

        Args:
            result: The refactoring result

        Returns:
            bool: True if validation passed
        """
        log.info("Validating function extraction")

        validations = {
            "has_extractions": len(result.file_changes) > 0,
            "no_errors": len(result.errors) == 0,
            "reasonable_scope": len(result.file_changes) <= result.plan.estimated_changes * 2,
        }

        result.validation_results = validations
        all_passed = all(validations.values())

        log.info(f"Validation {'passed' if all_passed else 'failed'}: {validations}")
        return all_passed
