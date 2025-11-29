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
Refactor Recipe - Base classes for refactoring recipes.
Defines the structure for refactoring workflows.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipe")


class RefactorRisk(Enum):
    """Risk levels for refactoring operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FileChange:
    """Represents a change to a single file."""

    file_path: str
    original_content: str
    modified_content: str
    change_type: str  # "modify", "create", "delete"
    line_changes: List[tuple] = field(default_factory=list)  # (start_line, end_line, new_content)


@dataclass
class RefactorPlan:
    """
    Represents a refactoring plan before execution.

    Contains all information needed to execute and audit a refactoring operation.
    """

    recipe_name: str
    project_id: str
    target_modules: List[str]
    target_files: List[str]
    rationale: str  # Why this refactoring?
    risks: List[str]  # What are the risks?
    risk_level: RefactorRisk
    estimated_changes: int  # Number of expected changes
    validation_steps: List[str]  # How to validate correctness
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefactorResult:
    """
    Represents the result of a refactoring operation.

    Contains all changes, validation results, and audit information.
    """

    plan: RefactorPlan
    success: bool
    file_changes: List[FileChange] = field(default_factory=list)
    patch_path: Optional[Path] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_changes(self) -> int:
        """Total number of file changes."""
        return len(self.file_changes)

    @property
    def changed_files(self) -> List[str]:
        """List of changed file paths."""
        return [fc.file_path for fc in self.file_changes]


class RefactorRecipe(ABC):
    """
    Base class for refactoring recipes.

    A recipe defines a specific refactoring operation with:
    - Analysis: What needs to be changed
    - Planning: How to change it safely
    - Execution: Making the changes
    - Validation: Ensuring correctness
    """

    def __init__(self):
        """Initialize the recipe."""
        self.logger = get_logger(f"refactor.recipe.{self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Recipe name (e.g., 'reduce_complexity')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this recipe does."""
        pass

    @property
    @abstractmethod
    def risk_level(self) -> RefactorRisk:
        """Default risk level for this recipe."""
        pass

    @abstractmethod
    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        """
        Analyze the system and create a refactoring plan.

        Args:
            system_model: The system model to analyze
            target: Optional targeting information (modules, files, etc.)

        Returns:
            RefactorPlan if refactoring is applicable, None otherwise
        """
        pass

    @abstractmethod
    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        """
        Execute the refactoring based on the plan.

        Args:
            plan: The refactoring plan
            chunks: Code chunks to refactor
            dry_run: If True, don't modify files, just generate patches

        Returns:
            RefactorResult with changes and validation results
        """
        pass

    @abstractmethod
    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the refactoring result.

        Args:
            result: The refactoring result to validate

        Returns:
            bool: True if validation passed
        """
        pass

    def estimate_effort(self, plan: RefactorPlan) -> Dict[str, Any]:
        """
        Estimate the effort required for this refactoring.

        Args:
            plan: The refactoring plan

        Returns:
            Dict with effort estimates (time, complexity, etc.)
        """
        return {
            "estimated_files": len(plan.target_files),
            "estimated_changes": plan.estimated_changes,
            "risk_level": plan.risk_level.value,
            "complexity": "medium",  # Can be overridden by subclasses
        }

    def generate_meta_reflection(self, result: RefactorResult) -> Dict[str, Any]:
        """
        Generate a meta-reflection about the refactoring operation.

        Args:
            result: The refactoring result

        Returns:
            Dict with meta-reflection data
        """
        from datetime import datetime

        return {
            "timestamp": datetime.now().isoformat(),
            "recipe": self.name,
            "project_id": result.plan.project_id,
            "success": result.success,
            "rationale": result.plan.rationale,
            "risks": result.plan.risks,
            "risk_level": result.plan.risk_level.value,
            "changed_files": result.changed_files,
            "total_changes": result.total_changes,
            "validation_passed": all(result.validation_results.values()) if result.validation_results else False,
            "errors": result.errors,
            "warnings": result.warnings,
            "lessons_learned": self._extract_lessons(result),
        }

    def _extract_lessons(self, result: RefactorResult) -> List[str]:
        """
        Extract lessons learned from the refactoring operation.

        Args:
            result: The refactoring result

        Returns:
            List of lesson strings
        """
        lessons = []

        if result.errors:
            lessons.append(f"Encountered {len(result.errors)} errors during refactoring")

        if result.warnings:
            lessons.append(f"Generated {len(result.warnings)} warnings")

        if result.total_changes > result.plan.estimated_changes * 1.5:
            lessons.append("Actual changes exceeded estimates by >50% - improve estimation")

        if result.success and not result.errors:
            lessons.append("Refactoring completed successfully without errors")

        return lessons
