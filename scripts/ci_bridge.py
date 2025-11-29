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
import zipfile
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
        print(e.stderr)
        sys.exit(1)

def get_latest_failed_run(branch: str = "main") -> Optional[Dict[str, Any]]:
    """Get the latest failed workflow run on the specified branch."""
    print(f"Checking for failed runs on {branch}...")
    # Fetch runs
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

def download_test_artifacts(run_id: int, output_dir: Path):
    """Download test-results artifacts from a specific run."""
    print(f"Downloading artifacts for run {run_id}...")
    try:
        # List artifacts to find test results
        artifacts_json = run_gh_command(["run", "view", str(run_id), "--json", "artifacts"])
        data = json.loads(artifacts_json)
        
        test_artifacts = [
            a for a in data.get("artifacts", []) 
            if "test-results" in a["name"]
        ]
        
        if not test_artifacts:
            print("No 'test-results' artifacts found in this run.")
            # Fallback to viewing log
            return False

        for artifact in test_artifacts:
            print(f"Downloading {artifact['name']}...")
            run_gh_command([
                "run", "download", str(run_id),
                "-n", artifact["name"],
                "-D", str(output_dir)
            ])
        
        return True

    except Exception as e:
        print(f"Failed to download artifacts: {e}")
        return False

def analyze_logs(run_id: int):
    """View failure logs directly using gh run view."""
    print(f"\n=== Failure Logs (Run {run_id}) ===\n")
    # Fetch failed steps logs
    log_output = run_gh_command(["run", "view", str(run_id), "--log-failed"])
    print(log_output)

def main():
    # Create a temp directory for analysis
    temp_dir = Path("logs_ci_latest")
    if not temp_dir.exists():
        temp_dir.mkdir()
    
    run = get_latest_failed_run()
    if not run:
        print("Everything looks green! 🟢")
        return

    print(f"Found failed run: {run['databaseId']} ({run['workflowName']})")
    print(f"URL: {run['url']}")
    
    # Attempt to download artifacts (JUnit XML etc)
    has_artifacts = download_test_artifacts(run['databaseId'], temp_dir)
    
    if has_artifacts:
        print(f"\nArtifacts downloaded to: {temp_dir}")
        # List what we got
        for item in temp_dir.rglob("*"):
            if item.is_file():
                print(f" - {item.relative_to(temp_dir)}")
    else:
        print("Artifacts unavailable, fetching raw logs...")
        analyze_logs(run['databaseId'])

if __name__ == "__main__":
    main()
