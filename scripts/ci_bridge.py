#!/usr/bin/env python3
"""
Feniks CI Bridge - Fetches GitHub Actions logs and artifacts for local analysis.
Usage: python scripts/ci_bridge.py [--download] [--limit 5]
"""
import json
import subprocess
import sys
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

def run_gh_command(args: list[str]) -> str:
    """Run a GitHub CLI command and return stdout."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running gh command: {' '.join(args)}")
        # Print stderr but don't exit immediately to allow fallback logic
        print(e.stderr)
        raise

def get_latest_failed_run(branch: str = "main") -> Optional[Dict[str, Any]]:
    """Get the latest failed workflow run on the specified branch."""
    print(f"Checking for failed runs on {branch}...")
    try:
        json_output = run_gh_command([
            "run", "list",
            "--branch", branch,
            "--status", "failure",
            "--limit", "1",
            "--json", "databaseId,status,conclusion,headSha,url,workflowName"
        ])
        runs = json.loads(json_output)
        if not runs:
            print("No failed runs found.")
            return None
        return runs[0]
    except Exception as e:
        print(f"Failed to list runs: {e}")
        return None

def download_test_artifacts(run_id: int, output_dir: Path) -> bool:
    """Try to download artifacts using 'gh run download'."""
    print(f"Attempting to download artifacts for run {run_id}...")
    try:
        # Try downloading specific known artifacts first or all
        # Note: listing artifacts via 'run view --json artifacts' failed previously.
        # We will try 'gh run download <id>' which downloads all artifacts.
        run_gh_command([
            "run", "download", str(run_id),
            "-D", str(output_dir)
        ])
        return True
    except Exception:
        print("Artifact download failed or no artifacts found. Falling back to logs.")
        return False

def analyze_logs(run_id: int):
    """View failure logs directly using gh run view."""
    print(f"\n=== Failure Logs (Run {run_id}) ===\n")
    try:
        log_output = run_gh_command(["run", "view", str(run_id), "--log-failed"])
        print(log_output)
    except Exception as e:
        print(f"Failed to fetch logs: {e}")

def main():
    # Create a temp directory for analysis
    temp_dir = Path("logs_ci_latest")
    if not temp_dir.exists():
        temp_dir.mkdir()
    
    run = get_latest_failed_run()
    if not run:
        print("Everything looks green! 🟢 (Or check permissions)")
        return

    print(f"Found failed run: {run['databaseId']} ({run['workflowName']})")
    print(f"URL: {run['url']}")
    
    # Try to download all artifacts
    has_artifacts = download_test_artifacts(run['databaseId'], temp_dir)
    
    if has_artifacts and any(temp_dir.iterdir()):
        print(f"\nArtifacts downloaded to: {temp_dir}")
        for item in temp_dir.rglob("*"):
            if item.is_file():
                print(f" - {item.relative_to(temp_dir)}")
    
    # Always analyze logs to see what failed
    analyze_logs(run['databaseId'])

if __name__ == "__main__":
    main()