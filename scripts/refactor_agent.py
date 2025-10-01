#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

# Add project root to allow sibling imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from feniks.logger import log
from feniks.config import settings
from qdrant_client import QdrantClient
from qdrant_client.http import models

def parse_query(query_str: str) -> models.Filter:
    """Parses a simple 'key:value' query string into a Qdrant filter."""
    if ':' not in query_str:
        raise ValueError("Invalid query format. Expected 'key:value'.")
    
    key, value = query_str.split(':', 1)
    
    return models.Filter(
        must=[
            models.FieldCondition(
                key=f"payload.{key.strip()}",
                match=models.MatchValue(value=value.strip()),
            )
        ]
    )

def run_sub_process(cmd: list[str]):
    """Helper to run an external script and stream its output."""
    log.info(f"Executing: {' '.join(cmd)}")
    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8') as proc:
            if proc.stdout:
                for line in proc.stdout:
                    log.info(line.strip())
        if proc.returncode != 0:
            log.error(f"Sub-process failed with exit code {proc.returncode}")
    except Exception as e:
        log.error(f"Sub-process execution failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Feniks Refactoring Agent")
    parser.add_argument("--recipe", type=Path, required=True, help="Path to the recipe YAML file.")
    parser.add_argument("--query", type=str, required=True, help="Simple query to find targets, e.g., 'kind:service'")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of files to process.")
    args = parser.parse_args()

    log.info("--- Starting Feniks Refactoring Agent ---")

    # 1. Parse query and connect to DB
    try:
        qdrant_filter = parse_query(args.query)
        log.info(f"Parsed query to filter: {qdrant_filter}")
    except ValueError as e:
        log.error(f"Invalid query string: {e}")
        sys.exit(1)

    try:
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        log.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    except Exception as e:
        log.error(f"Failed to connect to Qdrant: {e}")
        sys.exit(1)

    # 2. Find refactoring targets
    log.info(f"Searching for targets in collection '{settings.QDRANT_COLLECTION}'...")
    try:
        scroll_response, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=qdrant_filter,
            limit=2000, # A reasonable upper limit for a single run
            with_payload=True,
        )
        
        # Get unique file paths
        target_files = sorted(list(set(hit.payload['file_path'] for hit in scroll_response)))
        
        if args.limit:
            target_files = target_files[:args.limit]

        log.info(f"Found {len(target_files)} unique files to process.")
        if not target_files:
            log.warning("No files matched the query. Exiting.")
            return

    except Exception as e:
        log.error(f"Failed to query Qdrant: {e}")
        sys.exit(1)

    # 3. Apply recipe to each target
    apply_recipe_script = project_root / "scripts" / "apply_recipe.py"
    processed_count = 0
    for file_path in target_files:
        processed_count += 1
        log.info(f"--- Processing file {processed_count}/{len(target_files)}: {file_path} ---")
        
        # The file_path from the DB is already relative to the project root,
        # but we construct a full path for clarity and safety.
        absolute_file_path = project_root / file_path
        if not absolute_file_path.exists():
            log.warning(f"File not found: {absolute_file_path}. Skipping.")
            continue

        cmd = [
            sys.executable,
            str(apply_recipe_script),
            "--recipe", str(args.recipe),
            "--file-path", str(absolute_file_path),
        ]
        if args.dry-run:
            cmd.append("--dry-run")
        
        run_sub_process(cmd)

    log.info("--- Feniks Refactoring Agent Finished ---")

if __name__ == "__main__":
    main()
