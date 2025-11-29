from typing import Any, Dict

from feniks.core.refactor.php.runner import PhpToolRunner


class RectorWrapper(PhpToolRunner):
    """Wrapper for Rector (Automated Refactoring)."""

    def process(self, path: str = ".", dry_run: bool = True) -> Dict[str, Any]:
        cmd = ["vendor/bin/rector", "process", path, "--output-format=json"]
        if dry_run:
            cmd.append("--dry-run")

        return self.run_tool(cmd)


class PHPStanWrapper(PhpToolRunner):
    """Wrapper for PHPStan (Static Analysis)."""

    def analyze(self, path: str = ".", level: int = 5) -> Dict[str, Any]:
        cmd = ["vendor/bin/phpstan", "analyze", path, f"--level={level}", "--error-format=json"]
        return self.run_tool(cmd)


class DeptracWrapper(PhpToolRunner):
    """Wrapper for Deptrac (Architecture Analysis)."""

    def analyze(self, config_file: str = "deptrac.yaml") -> Dict[str, Any]:
        cmd = ["vendor/bin/deptrac", "analyze", config_file, "--formatter=json"]
        return self.run_tool(cmd)
