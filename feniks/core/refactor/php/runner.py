import subprocess
from pathlib import Path
from typing import Any, Dict, List

from feniks.infra.logging import get_logger

log = get_logger("refactor.php.runner")


class PhpToolRunner:
    """Base runner for PHP CLI tools."""

    def __init__(self, work_dir: str = "."):
        self.work_dir = Path(work_dir)

    def run_tool(self, command: List[str], check: bool = False) -> Dict[str, Any]:
        """Execute a PHP tool command."""
        log.debug(f"Executing PHP tool: {' '.join(command)}")
        try:
            result = subprocess.run(command, cwd=self.work_dir, capture_output=True, text=True, check=check)
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except FileNotFoundError:
            log.error(f"Tool executable not found: {command[0]}")
            return {"success": False, "error": "Tool not found"}
        except Exception as e:
            log.error(f"PHP tool execution failed: {e}")
            return {"success": False, "error": str(e)}
