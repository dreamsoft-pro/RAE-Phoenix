from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.javascript.engine import JSRefactorEngine
from feniks.core.refactor.recipe import RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk


class AngularMigrationRecipe(RefactorRecipe):
    """
    Recipe for migrating AngularJS to React.
    """

    def __init__(self):
        super().__init__()
        self.engine = JSRefactorEngine()

    @property
    def name(self) -> str:
        return "angular_migration"

    @property
    def description(self) -> str:
        return "Migrate AngularJS codebase to React using jscodeshift"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.CRITICAL

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        return RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[],
            target_files=["src/app"],
            rationale="Migrate legacy AngularJS to React",
            risks=["UI regression", "Broken bindings"],
            risk_level=self.risk_level,
            estimated_changes=100,
            validation_steps=["Run Playwright tests", "Manual UI check"],
        )

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        result = RefactorResult(plan=plan, success=True)

        # Scan
        scan_res = self.engine.scan_angular_project(".")
        result.metadata["ng_scan"] = scan_res

        # Apply transforms
        files = [c.file_path for c in chunks if c.file_path.endswith(".js")]
        if files:
            transform_res = self.engine.apply_codemod("ng-to-react-component", files, dry_run=dry_run)
            result.metadata["transform"] = transform_res

        return result

    def validate(self, result: RefactorResult) -> bool:
        return True
