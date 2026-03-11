import subprocess
from pathlib import Path
from typing import Any, Dict, List

from feniks.infra.logging import get_logger

log = get_logger("refactor.js.tools")


class JsToolRunner:
    """Base runner for JS/TS CLI tools."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)

    def run_tool(self, command: List[str]) -> Dict[str, Any]:
        log.debug(f"Executing JS tool: {' '.join(command)}")
        try:
            result = subprocess.run(command, cwd=self.work_dir, capture_output=True, text=True)
            return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
        except FileNotFoundError:
            return {"success": False, "error": "Tool not found"}


class JSCodeshiftWrapper(JsToolRunner):
    """Wrapper for jscodeshift."""

    def run_transform(self, transform_path: str, target_files: List[str], dry_run: bool = True) -> Dict[str, Any]:
        cmd = ["npx", "jscodeshift", "-t", transform_path]
        if dry_run:
            cmd.append("-d")
        cmd.extend(target_files)

        return self.run_tool(cmd)


class NgMigrationAssistantWrapper(JsToolRunner):
    """Wrapper for angular-migration-assistant."""

    def scan(self, root_dir: str = ".") -> Dict[str, Any]:
        # Assumes installed via npm install -g angular-migration-assistant or similar
        cmd = ["npx", "ngma", "scan", root_dir]
        return self.run_tool(cmd)
