from pathlib import Path
from typing import Any, Dict, List

from feniks.core.refactor.javascript.tools import JSCodeshiftWrapper, NgMigrationAssistantWrapper
from feniks.infra.logging import get_logger

log = get_logger("refactor.js.engine")


class JSRefactorEngine:
    """
    Orchestrator for JavaScript/TypeScript refactoring (AngularJS -> React).
    """

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)
        self.jscodeshift = JSCodeshiftWrapper(work_dir)
        self.ngma = NgMigrationAssistantWrapper(work_dir)

    def scan_angular_project(self, root_dir: str) -> Dict[str, Any]:
        """Run ngMigration Assistant scan."""
        log.info(f"Scanning AngularJS project at: {root_dir}")
        return self.ngma.scan(root_dir)

    def apply_codemod(self, codemod_name: str, target_files: List[str], dry_run: bool = True) -> Dict[str, Any]:
        """
        Apply a specific codemod (jscodeshift transform).
        """
        # Map common names to transform paths
        transforms = {
            "ng-to-react-component": "transforms/ng-controller-to-component.js",
            "scope-to-hooks": "transforms/scope-to-hooks.js",
        }

        transform_path = transforms.get(codemod_name, codemod_name)
        log.info(f"Applying codemod: {codemod_name} -> {transform_path}")

        return self.jscodeshift.run_transform(transform_path, target_files, dry_run)
