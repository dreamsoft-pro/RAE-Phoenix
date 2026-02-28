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
Patch Generator - Generates unified diff patches for refactoring changes.
"""
import difflib
from datetime import datetime
from pathlib import Path
from typing import List

from feniks.core.refactor.recipe import FileChange, RefactorResult
from feniks.infra.logging import get_logger

log = get_logger("refactor.patch_generator")


class PatchGenerator:
    """
    Generates patches (diffs) for refactoring changes.

    Creates unified diff format patches that can be:
    - Reviewed manually
    - Applied with `git apply` or `patch` command
    - Stored as audit trail
    """

    def generate_patch(self, result: RefactorResult, output_dir: Path) -> Path:
        """
        Generate a unified diff patch file.

        Args:
            result: The refactoring result with file changes
            output_dir: Directory to save the patch file

        Returns:
            Path: Path to the generated patch file
        """
        if not result.file_changes:
            log.warning("No file changes to generate patch for")
            return None

        log.info(f"Generating patch for {len(result.file_changes)} files")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate patch filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        patch_filename = f"{result.plan.recipe_name}_{result.plan.project_id}_{timestamp}.patch"
        patch_path = output_dir / patch_filename

        # Generate patch content
        patch_lines = []

        # Header
        patch_lines.append(f"# Refactoring Patch: {result.plan.recipe_name}")
        patch_lines.append(f"# Project: {result.plan.project_id}")
        patch_lines.append(f"# Generated: {datetime.now().isoformat()}")
        patch_lines.append(f"# Risk Level: {result.plan.risk_level.value}")
        patch_lines.append("#")
        patch_lines.append(f"# Rationale: {result.plan.rationale}")
        patch_lines.append("#")
        patch_lines.append(f"# Files changed: {len(result.file_changes)}")
        patch_lines.append("#")
        patch_lines.append("")

        # Generate diff for each file
        for file_change in result.file_changes:
            diff = self._generate_file_diff(file_change)
            if diff:
                patch_lines.extend(diff)
                patch_lines.append("")

        # Write patch file
        with patch_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(patch_lines))

        log.info(f"Patch saved to: {patch_path}")
        return patch_path

    def _generate_file_diff(self, file_change: FileChange) -> List[str]:
        """
        Generate unified diff for a single file.

        Args:
            file_change: The file change

        Returns:
            List of diff lines
        """
        if file_change.change_type == "delete":
            return [f"--- {file_change.file_path}", "+++ /dev/null", "# File deleted"]

        if file_change.change_type == "create":
            return ["--- /dev/null", f"+++ {file_change.file_path}", "# New file created"]

        # For modifications, generate suggestions as comments
        diff_lines = []
        diff_lines.append(f"--- {file_change.file_path}")
        diff_lines.append(f"+++ {file_change.file_path}")
        diff_lines.append("")

        # Add line change suggestions
        for start_line, end_line, suggestion in file_change.line_changes:
            diff_lines.append(f"# Lines {start_line}-{end_line}:")
            for line in suggestion.split("\n"):
                diff_lines.append(f"# {line}")
            diff_lines.append("")

        return diff_lines

    def generate_unified_diff(self, original: str, modified: str, file_path: str) -> str:
        """
        Generate unified diff between two strings.

        Args:
            original: Original file content
            modified: Modified file content
            file_path: File path for diff header

        Returns:
            str: Unified diff
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines, modified_lines, fromfile=f"a/{file_path}", tofile=f"b/{file_path}", lineterm=""
        )

        return "".join(diff)
