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
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator
from langdetect import detect as ld_detect
import re

# --- Utility functions from search_demo.py ---

def detect_lang(s: str) -> str:
    try:
        return ld_detect(s)
    except Exception:
        if re.search(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", s):
            return "pl"
        return "en"

def translate_pl_to_en(q: str) -> str:
    lang = detect_lang(q)
    if lang.startswith("en"):
        return q
    try:
        return GoogleTranslator(source="auto", target="en").translate(q)
    except Exception:
        log.warning("Translation failed, using simple replacement.")
        repl = {
            "refaktoryzuj":"refactor","serwis":"service","autentykacji":"authentication",
            "autentykacja":"authentication","logowanie":"login","wylogowanie":"logout",
            "użytkownika":"user","hasło":"password","token":"token","sesja":"session",
            "uprawnienia":"permissions","rola":"role","rejestracja":"registration"
        }
        t = q.lower()
        for k,v in repl.items():
            t = re.sub(rf"\b{re.escape(k)}\b", v, t)
        return t + " auth authentication login user service refactor token session password"

def parse_filter(filter_str: str | None) -> models.Filter | None:
    """Parses a simple 'key:value' string into a Qdrant filter."""
    if not filter_str or ':' not in filter_str:
        return None
    
    key, value = filter_str.split(':', 1)
    
    log.info(f"Applying metadata filter: {key}={value}")
    return models.Filter(
        must=[
            models.FieldCondition(
                key=key.strip(),
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
    parser.add_argument("--query", type=str, required=True, help="Natural language query to find refactoring targets.")
    parser.add_argument("--filter", type=str, default=None, help="Optional metadata filter, e.g., 'kind:js_function'")
    parser.add_argument("--score-threshold", type=float, default=0.5, help="Minimum score for a search result to be considered a match.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files.")
    parser.add_argument("--limit", type=int, default=50, help="Limit the number of files to process.")
    args = parser.parse_args()

    log.info("--- Starting Feniks Refactoring Agent ---")

    # 1. Connect to DB and embedding model
    try:
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        log.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        log.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
    except Exception as e:
        log.error(f"Failed to initialize Qdrant client or embedding model: {e}")
        sys.exit(1)

    # 2. Find refactoring targets via semantic search
    log.info(f"Searching for targets in collection '{settings.QDRANT_COLLECTION}'...")
    try:
        query_en = translate_pl_to_en(args.query)
        log.info(f"Original query: '{args.query}' -> Translated: '{query_en}'")
        
        query_vector = model.encode(query_en, normalize_embeddings=True)
        
        qdrant_filter = parse_filter(args.filter)

        search_response = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            score_threshold=args.score_threshold,
            limit=args.limit or 50, # Ensure limit is not None
            with_payload=True,
        )
        
        # Get unique file paths from scored points
        target_files = sorted(list(set(hit.payload['file_path'] for hit in search_response)))
        
        if args.limit:
            target_files = target_files[:args.limit]

        log.info(f"Found {len(target_files)} unique files to process with score >= {args.score_threshold}.")
        if not target_files:
            log.warning("No files matched the query and threshold. Exiting.")
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
        if args.dry_run:
            cmd.append("--dry-run")
        
        run_sub_process(cmd)

    log.info("--- Feniks Refactoring Agent Finished ---")

if __name__ == "__main__":
    main()
