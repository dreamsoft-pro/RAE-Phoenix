#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

# Add the 'scripts' directory to the Python path to allow sibling imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from feniks.logger import log
from feniks.config import settings
from feniks.parser import run_ast_indexer, load_chunks_from_jsonl
from feniks.kb_builder import build_module_cards_from_chunks, write_module_cards
from feniks.git_utils import get_blame_for_chunk
from feniks.embed import get_embedding_model, create_dense_embeddings, build_tfidf
from feniks.qdrant import ensure_collection, upsert_points
from qdrant_client import QdrantClient

def run_build_process(reset_collection: bool = False):
    """
    The core logic for building the knowledge base.
    This function is called by the CLI command.
    """
    log.info("--- Starting Feniks Knowledge Base Build ---")
    try:
        # --- 1. Parsing and Chunking ---
        log.info("Step 1: Running AST indexer and loading chunks...")
        chunks_jsonl_path = run_ast_indexer(settings.FRONTEND_ROOT)
        if not chunks_jsonl_path.exists():
            log.error(f"AST indexer output not found at {chunks_jsonl_path}")
            sys.exit(1)
        chunks = load_chunks_from_jsonl(chunks_jsonl_path)
        if not chunks:
            log.error("No chunks were loaded. Aborting.")
            sys.exit(1)
        log.info(f"Loaded {len(chunks)} chunks from AST data.")

        # --- 2a. Enrich with Git Blame --- 
        log.info("Step 2a: Enriching chunks with git blame information...")
        for chunk in chunks:
            chunk.git_info = get_blame_for_chunk(chunk, repo_root=settings.FRONTEND_ROOT)


        # --- 2. Module Cards ---
        log.info("Step 2: Building and writing module cards...")
        module_cards = build_module_cards_from_chunks(chunks)
        write_module_cards(settings.OUTPUT_DIR, module_cards)

        # --- 3. Embeddings ---
        log.info("Step 3: Creating dense and sparse embeddings...")
        model = get_embedding_model(settings.EMBEDDING_MODEL)
        dense_embs = create_dense_embeddings(model, chunks)
        tfidf_vec, tfidf_matrix = build_tfidf(chunks)
        log.info(f"Created {dense_embs.shape[0]} dense embeddings of dimension {dense_embs.shape[1]}.")

        # --- 4. Qdrant Ingestion ---
        log.info("Step 4: Connecting to Qdrant and upserting points...")
        qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        ensure_collection(
            client=qdrant_client, 
            name=settings.QDRANT_COLLECTION, 
            dim=dense_embs.shape[1], 
            reset=reset_collection
        )
        upsert_points(
            client=qdrant_client,
            collection=settings.QDRANT_COLLECTION,
            chunks=chunks,
            dense=dense_embs,
            X_tfidf=tfidf_matrix,
            vocab=tfidf_vec.vocabulary_
        )
        log.info(f"Upserted {len(chunks)} points to Qdrant collection '{settings.QDRANT_COLLECTION}'.")

        log.info("--- Feniks Knowledge Base Build Finished Successfully ---")

    except RuntimeError as e:
        log.error(f"A critical error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

def main():
    """
    CLI entry point for the Feniks tool.
    """
    parser = argparse.ArgumentParser(description="Feniks Knowledge Base Builder CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Build Command ---
    build_parser = subparsers.add_parser("build", help="Run the full knowledge base build process.")
    build_parser.add_argument("--reset", action="store_true", help="Reset (delete and recreate) the Qdrant collection before upserting.")
    build_parser.set_defaults(func=lambda args: run_build_process(reset_collection=args.reset))

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
