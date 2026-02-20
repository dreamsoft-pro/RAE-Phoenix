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

from feniks.infra.logging import log
from feniks.config.settings import settings
from feniks.core.models.types import Chunk, GitInfo, MigrationSuggestion, ApiEndpoint
from feniks.adapters.llm.embedding import get_embedding_model, create_dense_embeddings, build_tfidf
from feniks.adapters.storage.qdrant import ensure_collection, upsert_points
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

def load_ir_chunks(path: Path) -> List[Chunk]:
    """Loads chunks from the Feniks IR JSONL file."""
    chunks = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Map nested objects
                git_info_data = data.get("git_last_commit")
                git_info = GitInfo(**git_info_data) if git_info_data else None
                
                api_endpoints_data = data.get("api_endpoints", [])
                api_endpoints = [ApiEndpoint(**ep) for ep in api_endpoints_data]

                chunks.append(Chunk(
                    id=data["id"],
                    file_path=data["file_path"],
                    start_line=data["start_line"],
                    end_line=data["end_line"],
                    text=data["text"],
                    chunk_name=data["chunk_name"],
                    module=data.get("module"),
                    kind=data.get("kind"),
                    ast_node_type=data.get("ast_node_type"),
                    dependencies_di=data.get("dependencies_di", []),
                    calls_functions=data.get("calls_functions", []),
                    api_endpoints=api_endpoints,
                    ui_routes=data.get("ui_routes", []),
                    cyclomatic_complexity=data.get("cyclomatic_complexity", 0),
                    business_tags=data.get("business_tags", []),
                    git_last_commit=git_info,
                    evidence=data.get("evidence", []),
                    confidence=data.get("confidence", 1.0),
                    criticality_score=data.get("criticality_score", 0.0),
                    migration_target=data.get("migration_target"),
                    invariants=data.get("invariants", []),
                    io_contract=data.get("io_contract", {}),
                    api_contract_ref=data.get("api_contract_ref")
                ))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                log.error(f"Could not parse IR chunk line: {e} -> {line}")
    return chunks

def run_build_process(reset_collection: bool = False, collection_name: str = settings.qdrant_collection):
    log.info("--- Starting Feniks Knowledge Base Build (Advanced) ---")
    try:
        # --- 0. Setup output directories ---
        log.info("Step 0: Setting up output directories...")
        run_dir = settings.project_root / "runs" / "latest"
        run_dir.mkdir(parents=True, exist_ok=True)
        raw_chunks_path = run_dir / "chunks.mjs.jsonl"
        enriched_chunks_path = run_dir / "chunks.enriched.jsonl"
        ir_chunks_path = run_dir / "chunks.ir.jsonl"
        log.info("Step 0: Finished setting up output directories.")

        # --- 1. Run Node.js Indexer ---
        log.info("Step 1: Running advanced Node.js indexer...")
        frontend_path = settings.project_root / "frontend-master"
        indexer_cmd = ["node", str(settings.node_indexer_path), "--root", str(frontend_path), "--out", str(raw_chunks_path)]
        run_external_script(indexer_cmd, cwd=settings.project_root)
        log.info("Step 1: Finished running advanced Node.js indexer.")

        # --- 2. Run Python Git Blame Enricher ---
        log.info("Step 2: Enriching chunks with git blame information...")
        enricher_path = settings.project_root / "scripts" / "enrich_git_blame.py"
        enricher_cmd = [sys.executable, str(enricher_path), "--repo", str(frontend_path), "--in", str(raw_chunks_path), "--out", str(enriched_chunks_path)]
        run_external_script(enricher_cmd, cwd=settings.project_root)
        log.info("Step 2: Finished enriching chunks with git blame information.")

        # --- 2.5. Convert to IR ---
        log.info("Step 2.5: Converting to Feniks Intermediate Representation (IR)...")
        converter_path = settings.project_root / "scripts" / "convert_to_ir.py"
        converter_cmd = [sys.executable, str(converter_path), "--in", str(enriched_chunks_path), "--out", str(ir_chunks_path)]
        run_external_script(converter_cmd, cwd=settings.project_root)
        log.info("Step 2.5: Finished converting to Feniks IR.")

        # --- 2.6. Validate IR ---
        log.info("Step 2.6: Validating Feniks IR against schema...")
        validator_path = settings.project_root / "scripts" / "validate_ir.py"
        schema_path = settings.project_root / "schemas" / "ir.schema.json"
        validator_cmd = [sys.executable, str(validator_path), "--schema", str(schema_path), "--in", str(ir_chunks_path)]
        run_external_script(validator_cmd, cwd=settings.project_root)
        log.info("Step 2.6: Finished validating Feniks IR.")

        # --- 3. Load IR Chunks ---
        log.info("Step 3: Loading IR chunks into Python...")
        chunks = load_ir_chunks(ir_chunks_path)
        if not chunks:
            raise RuntimeError("No chunks were loaded from IR file. Aborting.")
        log.info(f"Loaded {len(chunks)} IR chunks.")
        log.info("Step 3: Finished loading IR chunks.")

        # --- 4. Embeddings ---
        log.info("Step 4: Creating dense and sparse embeddings...")
        model = get_embedding_model(settings.embedding_model)
        dense_embs = create_dense_embeddings(model, chunks)
        tfidf_vec, tfidf_matrix = build_tfidf(chunks)
        log.info(f"Created {dense_embs.shape[0]} dense embeddings.")
        log.info("Step 4: Finished creating embeddings.")

        # --- 5. Qdrant Ingestion ---
        log.info("Step 5: Connecting to Qdrant and upserting points...")
        qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        ensure_collection(client=qdrant_client, name=collection_name, dim=dense_embs.shape[1], reset=reset_collection)
        upsert_points(client=qdrant_client, collection=collection_name, chunks=chunks, dense=dense_embs, X_tfidf=tfidf_matrix, vocab=tfidf_vec.vocabulary_)
        log.info(f"Upserted {len(chunks)} points to Qdrant collection '{collection_name}'.")
        log.info("Step 5: Finished Qdrant ingestion.")

        log.info("--- Feniks Knowledge Base Build Finished Successfully ---")

    except (RuntimeError, Exception) as e:
        log.error(f"A critical error occurred during the build process: {e}", exc_info=True)
        sys.exit(1)

def run_refactor_agent(query: str, recipe: Path, dry_run: bool, filter_: str | None, score_threshold: float, limit: int | None):
    """Wrapper to call the refactor_agent.py script."""
    script_path = settings.project_root / "scripts" / "refactor_agent.py"
    cmd = [
        sys.executable, str(script_path),
        "--query", query,
        "--recipe", str(recipe),
        f"--score-threshold", str(score_threshold),
    ]
    if dry_run:
        cmd.append("--dry-run")
    if filter_:
        cmd.extend(["--filter", filter_])
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    # Use run_external_script but be mindful of streaming output if needed later
    run_external_script(cmd, cwd=settings.project_root)

def run_generate_openapi(input_path: Path, output_path: Path):
    """Wrapper to call the generate_openapi.py script."""
    script_path = settings.project_root / "scripts" / "generate_openapi.py"
    cmd = [
        sys.executable, str(script_path),
        "--in", str(input_path),
        "--out", str(output_path),
    ]
    run_external_script(cmd, cwd=settings.project_root)

def main():
    parser = argparse.ArgumentParser(description="Feniks Knowledge Base Builder and Refactoring CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Run the full knowledge base build process.")
    build_parser.add_argument("--reset", action="store_true", help="Reset the Qdrant collection.")
    build_parser.set_defaults(func=lambda args: run_build_process(reset_collection=args.reset))

    # Refactor Agent command
    refactor_parser = subparsers.add_parser("refactor", help="Run the refactoring agent.")
    refactor_parser.add_argument("--query", type=str, required=True, help="Natural language query to find refactoring targets.")
    refactor_parser.add_argument("--recipe", type=Path, required=True, help="Path to the recipe YAML file to apply.")
    refactor_parser.add_argument("--filter", type=str, default=None, help="Optional metadata filter, e.g., 'kind:js_function'")
    refactor_parser.add_argument("--score-threshold", type=float, default=0.5, help="Minimum score for a search result to be considered a match.")
    refactor_parser.add_argument("--limit", type=int, default=None, help="Limit the number of files to process.")
    refactor_parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files.")
    refactor_parser.set_defaults(func=lambda args: run_refactor_agent(
        args.query, args.recipe, args.dry_run, args.filter, args.score_threshold, args.limit
    ))

    # OpenAPI Generator command
    openapi_parser = subparsers.add_parser("generate-openapi", help="Generate an OpenAPI spec from the IR.")
    openapi_parser.add_argument("--in", dest="input_path", type=Path, required=True, help="Path to the Feniks IR JSONL file (e.g., runs/latest/chunks.ir.jsonl).")
    openapi_parser.add_argument("--out", dest="output_path", type=Path, required=True, help="Path to write the OpenAPI JSON file.")
    openapi_parser.set_defaults(func=lambda args: run_generate_openapi(args.input_path, args.output_path))

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
