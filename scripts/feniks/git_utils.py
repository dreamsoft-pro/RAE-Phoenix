import subprocess
from pathlib import Path
from typing import Optional, Dict

from feniks.types import Chunk
from feniks.logger import log

def get_blame_for_chunk(chunk: Chunk, repo_root: Path) -> Optional[Dict[str, str]]:
    """
    Runs `git blame` for a specific code chunk to find the last commit 
    that modified it.

    Uses --porcelain format for stable parsing.
    Returns a dictionary with commit info or None if blame fails.
    """
    if not chunk.file_path or not chunk.start_line or not chunk.end_line:
        return None

    # We need to construct the full path to the file for git
    # Assuming chunk.file_path is relative to the frontend root
    full_file_path = repo_root / chunk.file_path

    if not full_file_path.exists():
        return None

    cmd = [
        "git", "blame",
        "-L", f"{chunk.start_line},{chunk.end_line}",
        "--porcelain",
        str(full_file_path)
    ]

    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=repo_root, # Run git command in the repo root
            check=True
        )
        
        # Porcelain format is a set of key-value pairs.
        # We are interested in the first commit hash and the summary.
        lines = result.stdout.splitlines()
        if not lines:
            return None

        commit_hash = lines[0].split(" ")[0]
        summary = ""
        author = ""

        for i, line in enumerate(lines):
            if line.startswith("summary"): # First summary is the most relevant
                summary = line.split(" ", 1)[1]
            if line.startswith("author "):
                author = line.split(" ", 1)[1]
        
        if commit_hash and summary:
            return {
                "hash": commit_hash,
                "author": author,
                "summary": summary
            }

    except (subprocess.CalledProcessError, FileNotFoundError, IndexError) as e:
        log.warning(f"Could not run git blame for {chunk.file_path}: {e}")
        return None

    return None
