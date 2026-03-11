#!/usr/bin/env python3
"""
Feniks Docs Automator - Automatically maintains project documentation.
Updates CHANGELOG.md, STATUS.md, TODO.md based on git history and code scanning.
"""
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set

# Configuration
PROJECT_ROOT = Path(".")
DOCS_FILES = ["CHANGELOG.md", "STATUS.md", "TODO.md", "README.md"]

def run_command(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, text=True).strip()
    except subprocess.CalledProcessError:
        return ""

def get_git_history() -> List[str]:
    """Get commit messages since the beginning or last tag."""
    # For simplicity, getting last 50 commits for this MVP
    return run_command(["git", "log", "-n", "50", "--pretty=format:%s"]).split("\n")

def parse_commits(commits: List[str]) -> Dict[str, List[str]]:
    """Parse Conventional Commits."""
    categories = {
        "feat": [], "fix": [], "docs": [], "refactor": [], "perf": [], "test": [], "chore": []
    }
    
    for msg in commits:
        match = re.match(r"^(\w+)(\(.+\))!?: (.+)", msg)
        if match:
            type_ = match.group(1)
            desc = match.group(3)
            if type_ in categories:
                categories[type_].append(desc)
    return categories

def update_changelog(categories: Dict[str, List[str]]):
    """Update CHANGELOG.md with Unreleased changes."""
    changelog_path = PROJECT_ROOT / "CHANGELOG.md"
    
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
    if changelog_path.exists():
        content = changelog_path.read_text()
        # If header missing, prepend it
        if "# Changelog" not in content:
            content = header + content
    else:
        content = header

    today = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"## [Unreleased] - {today}\n\n"
    
    has_changes = False
    
    # Map types to Changelog sections
    mapping = {
        "feat": "### Added",
        "fix": "### Fixed",
        "refactor": "### Changed",
        "perf": "### Performance",
        "docs": "### Documentation"
    }
    
    for type_, section_name in mapping.items():
        msgs = categories.get(type_, [])
        if msgs:
            has_changes = True
            new_entry += f"{section_name}\n"
            for msg in msgs:
                new_entry += f"- {msg}\n"
            new_entry += "\n"
            
    if not has_changes:
        return # No semantic changes to log

    # Logic to insert at top (after header) could be complex. 
    # For this MVP, we overwrite "Unreleased" if exists or append to top.
    # A simpler approach for Agent: Re-generate the 'Unreleased' section.
    
    # Basic append for now if file is new, or prepend after header
    if "## [Unreleased]" not in content:
        # Insert after header
        parts = content.split("\n\n", 1)
        if len(parts) > 1:
            content = parts[0] + "\n\n" + new_entry + parts[1]
        else:
            content += "\n" + new_entry
            
    changelog_path.write_text(content)
    print(f"Updated {changelog_path}")

def scan_todos():
    """Scan codebase for TODO comments."""
    todo_path = PROJECT_ROOT / "TODO.md"
    todos = []
    
    # Scan python and js files
    for ext in ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx"]:
        for file in PROJECT_ROOT.glob(ext):
            if "venv" in file.parts or "node_modules" in file.parts:
                continue
            try:
                lines = file.read_text().splitlines()
                for i, line in enumerate(lines):
                    if "TODO" in line:
                        # Clean line
                        clean_line = line.split("TODO")[-1].strip(": ").strip()
                        todos.append(f"- [ ] **{file.name}:{i+1}**: {clean_line}")
            except Exception:
                pass
                
    content = "# Project TODOs\n\n> Auto-generated from source code scanning.\n\n"
    if todos:
        content += "\n".join(todos)
    else:
        content += "No TODOs found in code."
        
    todo_path.write_text(content)
    print(f"Updated {todo_path}")

def update_status():
    """Update STATUS.md with badges."""
    status_path = PROJECT_ROOT / "STATUS.md"
    
    # Assuming main branch
    repo = "dreamsoft-pro/RAE-Feniks" # Detected from git remote in real scenario
    
    badges = [
        f"![CI Status](https://github.com/{repo}/actions/workflows/ci.yml/badge.svg)",
        f"![Last Commit](https://img.shields.io/github/last-commit/{repo})",
        "![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)",
        "![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)"
    ]
    
    content = "# Project Status\n\n"
    content += " ".join(badges) + "\n\n"
    
    content += "## Current Phase\n"
    content += "**Optimization & Stability**\n\n"
    
    content += "## Health Check\n"
    content += "- **Linting**: Strict (Ruff + Black + Isort)\n"
    content += "- **Testing**: Pytest (Coverage pending >80%)\n"
    content += "- **Documentation**: Automated via Feniks Agent\n"
    
    status_path.write_text(content)
    print(f"Updated {status_path}")

def check_readme():
    """Ensure README exists."""
    readme_path = PROJECT_ROOT / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# Feniks\n\nRAE-Feniks Code Analysis & Refactoring Engine.\n")
        print(f"Created {readme_path}")

def main():
    print("Starting Documentation Automation...")
    
    commits = get_git_history()
    parsed = parse_commits(commits)
    
    update_changelog(parsed)
    scan_todos()
    update_status()
    check_readme()
    
    print("Documentation update complete.")

if __name__ == "__main__":
    main()
