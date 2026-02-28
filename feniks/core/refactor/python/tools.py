import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from feniks.infra.logging import get_logger

log = get_logger("refactor.python.tools")


class PythonToolWrapper:
    """Base wrapper for Python refactoring and analysis tools."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)

    def _run_command(self, cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
        """Run a subprocess command."""
        log.debug(f"Running command: {' '.join(cmd)}")
        try:
            return subprocess.run(cmd, cwd=self.work_dir, capture_output=True, text=True, check=check)
        except subprocess.CalledProcessError as e:
            log.error(f"Command failed: {e}")
            log.error(f"Stderr: {e.stderr}")
            raise

    def is_installed(self, tool_name: str) -> bool:
        return shutil.which(tool_name) is not None


class RuffWrapper(PythonToolWrapper):
    """Wrapper for Ruff linter/formatter."""

    def check(self, target: str = ".") -> Dict[str, Any]:
        """Run ruff check --json."""
        if not self.is_installed("ruff"):
            log.warning("Ruff not found")
            return {}

        result = self._run_command(["ruff", "check", target, "--output-format=json"], check=False)
        try:
            return json.loads(result.stdout) if result.stdout else []
        except json.JSONDecodeError:
            return {"error": "Failed to parse ruff output", "raw": result.stdout}

    def fix(self, target: str = ".") -> None:
        """Run ruff check --fix."""
        if not self.is_installed("ruff"):
            return
        self._run_command(["ruff", "check", target, "--fix"], check=False)


class MyPyWrapper(PythonToolWrapper):
    """Wrapper for MyPy type checker."""

    def check(self, target: str = ".") -> str:
        if not self.is_installed("mypy"):
            log.warning("MyPy not found")
            return "MyPy not installed"

        result = self._run_command(["mypy", target], check=False)
        return result.stdout


class BowlerWrapper(PythonToolWrapper):
    """Wrapper for Bowler refactoring tool."""

    def run_query(self, query_pattern: str, target: str = ".") -> str:
        """
        Simulated Bowler execution (since Bowler is a library usually invoked via script).
        This expects a python script that uses bowler to be passed or similar.
        For this implementation, we assume a CLI adapter exists or we build one.
        """
        # Real implementation would involve importing bowler and running a query
        # For now, we assume a CLI interface or return a placeholder
        return "Bowler execution placeholder"


class LibCSTWrapper(PythonToolWrapper):
    """Wrapper for LibCST analysis."""

    def analyze_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze file structure using LibCST.
        """
        try:
            import libcst as cst

            class StructureVisitor(cst.CSTVisitor):
                def __init__(self):
                    self.functions = []
                    self.classes = []

                def visit_FunctionDef(self, node: cst.FunctionDef) -> None:  # noqa: N802
                    self.functions.append(node.name.value)

                def visit_ClassDef(self, node: cst.ClassDef) -> None:  # noqa: N802
                    self.classes.append(node.name.value)

            path = self.work_dir / file_path
            if not path.exists():
                return {"error": "File not found"}

            with open(path, "r") as f:
                source = f.read()

            module = cst.parse_module(source)
            visitor = StructureVisitor()
            module.visit(visitor)

            return {"functions": visitor.functions, "classes": visitor.classes}

        except ImportError:
            log.warning("LibCST not installed")
            return {"error": "LibCST not installed"}
        except Exception as e:
            log.error(f"LibCST analysis failed: {e}")
            return {"error": str(e)}
