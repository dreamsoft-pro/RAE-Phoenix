#!/usr/bin/env python
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

# Add the 'scripts' directory to the Python path to allow sibling imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from feniks.logger import log
from feniks.config import settings
from feniks.types import Chunk, GitInfo, MigrationSuggestion
from feniks.embed import get_embedding_model, create_dense_embeddings, build_tfidf
from feniks.qdrant import ensure_collection, upsert_points
from qdrant_client import QdrantClient

def run_external_script(cmd: List[str], cwd: Path):
    """Helper to run an external script and handle errors."""
    log.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=cwd)
        if result.stdout:
            log.info(result.stdout)
        if result.stderr:
            log.warning(result.stderr)
    except subprocess.CalledProcessError as e:
        log.error(f"Script failed with exit code {e.returncode}")
        log.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"External script failed: {' '.join(cmd)}") from e

def load_enriched_chunks(path: Path) -> List[Chunk]:
    """Loads chunks from the enriched JSONL file."""
    chunks = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                # Map git info and migration suggestion to dataclasses
                git_info_data = data.get("git_last_commit")
                git_info = GitInfo(**git_info_data) if git_info_data else None
                
                ms_data = data.get("migration_suggestion")
                migration_suggestion = MigrationSuggestion(**ms_data) if ms_data else None

                chunks.append(Chunk(
                    id=data["id"],
                    file_path=data["filePath"],
                    start_line=data["start"],
                    end_line=data["end"],
                    text=data["text"],
                    chunk_name=data["name"],
                    module=data.get("module"),
                    kind=data.get("kind"),
                    ast_node_type=data.get("ast_node_type"),
                    dependencies_di=data.get("dependencies_di", []),
                    calls_functions=data.get("calls_functions", []),
                    api_endpoints=data.get("api_endpoints", []),
                    ui_routes=data.get("ui_routes", []),
                    cyclomatic_complexity=data.get("cyclomatic_complexity", 0),
                    business_tags=data.get("business_tags", []),
                    git_last_commit=git_info,
                    migration_suggestion=migration_suggestion
                ))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                log.error(f"Could not parse enriched chunk line: {e} -> {line}")
    return chunks

def run_build_process(reset_collection: bool = False):
    log.info("--- Starting Feniks Knowledge Base Build (Advanced) ---")
    try:
        # --- 0. Setup output directories ---
        run_dir = settings.PROJECT_ROOT / "runs" / "latest"
        run_dir.mkdir(parents=True, exist_ok=True)
        raw_chunks_path = run_dir / "chunks.mjs.jsonl"
        enriched_chunks_path = run_dir / "chunks.enriched.jsonl"
        ir_chunks_path = run_dir / "chunks.ir.jsonl"

        # --- 1. Run Node.js Indexer ---
        log.info("Step 1: Running advanced Node.js indexer...")
        frontend_path = settings.PROJECT_ROOT / "frontend-master"
        indexer_cmd = ["node", str(settings.NODE_INDEXER_PATH), "--root", str(frontend_path), "--out", str(raw_chunks_path)]
        run_external_script(indexer_cmd, cwd=settings.PROJECT_ROOT)

        # --- 2. Run Python Git Blame Enricher ---
        log.info("Step 2: Enriching chunks with git blame information...")
        enricher_path = settings.PROJECT_ROOT / "scripts" / "enrich_git_blame.py"
        enricher_cmd = ["python3", str(enricher_path), "--repo", str(frontend_path), "--in", str(raw_chunks_path), "--out", str(enriched_chunks_path)]
        run_external_script(enricher_cmd, cwd=settings.PROJECT_ROOT)

        # --- 2.5. Convert to IR ---
        log.info("Step 2.5: Converting to Feniks Intermediate Representation (IR)...")
        converter_path = settings.PROJECT_ROOT / "scripts" / "convert_to_ir.py"
        converter_cmd = ["python3", str(converter_path), "--in", str(enriched_chunks_path), "--out", str(ir_chunks_path)]
        run_external_script(converter_cmd, cwd=settings.PROJECT_ROOT)

        # --- 2.6. Validate IR ---
        log.info("Step 2.6: Validating Feniks IR against schema...")
        validator_path = settings.PROJECT_ROOT / "scripts" / "validate_ir.py"
        schema_path = settings.PROJECT_ROOT / "schemas" / "ir.schema.json"
        validator_cmd = ["python3", str(validator_path), "--schema", str(schema_path), "--in", str(ir_chunks_path)]
        run_external_script(validator_cmd, cwd=settings.PROJECT_ROOT)

        # --- 3. Load Enriched Chunks ---
        log.info("Step 3: Loading enriched chunks into Python...")
        chunks = load_enriched_chunks(enriched_chunks_path)
        if not chunks:
            raise RuntimeError("No chunks were loaded after enrichment. Aborting.")
        log.info(f"Loaded {len(chunks)} enriched chunks.")

        # --- 4. Embeddings ---
        log.info("Step 4: Creating dense and sparse embeddings...")
        model = get_embedding_model(settings.EMBEDDING_MODEL)
        dense_embs = create_dense_embeddings(model, chunks)
        tfidf_vec, tfidf_matrix = build_tfidf(chunks)
        log.info(f"Created {dense_embs.shape[0]} dense embeddings.")

        # --- 5. Qdrant Ingestion ---
        log.info("Step 5: Connecting to Qdrant and upserting points...")
        qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        ensure_collection(client=qdrant_client, name=settings.QDRANT_COLLECTION, dim=dense_embs.shape[1], reset=reset_collection)
        upsert_points(client=qdrant_client, collection=settings.QDRANT_COLLECTION, chunks=chunks, dense=dense_embs, X_tfidf=tfidf_matrix, vocab=tfidf_vec.vocabulary_)
        log.info(f"Upserted {len(chunks)} points to Qdrant collection '{settings.QDRANT_COLLECTION}'.")

        log.info("--- Feniks Knowledge Base Build Finished Successfully ---")

    except (RuntimeError, Exception) as e:
        log.error(f"A critical error occurred during the build process: {e}", exc_info=True)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Feniks Knowledge Base Builder CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="Run the full knowledge base build process.")
    build_parser.add_argument("--reset", action="store_true", help="Reset the Qdrant collection.")
    build_parser.set_defaults(func=lambda args: run_build_process(reset_collection=args.reset))
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
