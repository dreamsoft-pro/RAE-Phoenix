#!/usr/bin/env python
"""
Feniks CLI - Main command-line interface for RAE-Feniks.
Handles code ingestion, analysis, and refactoring workflows.
"""
import argparse
import sys
from pathlib import Path

from feniks.logger import get_logger
from feniks.config import settings
from feniks.exceptions import FeniksError
from feniks.core.ingest_pipeline import run_ingest

log = get_logger("cli")


def handle_version():
    """Display version information."""
    print("Feniks v0.1.0 - RAE Code Analysis and Refactoring Engine")
    print(f"Profile: {settings.feniks_profile}")
    print(f"Project root: {settings.project_root}")


def handle_ingest(args):
    """Handle the ingest command."""
    log.info("=== Feniks Ingest Pipeline ===")
    log.info(f"JSONL path: {args.jsonl_path}")
    log.info(f"Collection: {args.collection}")
    log.info(f"Reset collection: {args.reset}")

    # Validate JSONL path
    jsonl_path = Path(args.jsonl_path)
    if not jsonl_path.exists():
        raise FeniksError(f"JSONL file not found: {jsonl_path}")

    # Parse filter patterns
    include_patterns = args.include.split(",") if args.include else None
    exclude_patterns = args.exclude.split(",") if args.exclude else None

    # Run ingestion
    stats = run_ingest(
        jsonl_path=jsonl_path,
        collection_name=args.collection,
        reset_collection=args.reset,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        skip_errors=args.skip_errors
    )

    # Print summary
    log.info("=== Ingestion Complete ===")
    log.info(f"Loaded: {stats['loaded']} chunks")
    log.info(f"Filtered out: {stats['filtered']} chunks")
    log.info(f"Ingested: {stats['ingested']} chunks")
    log.info(f"Collection: {stats['collection']}")


def handle_analyze(args):
    """Handle the analyze command (to be implemented in Iteration 4)."""
    log.info("Analyze command will be implemented in Iteration 4")
    log.info(f"Project ID: {args.project_id}")


def handle_refactor(args):
    """Handle the refactor command (to be implemented in Iteration 6)."""
    log.info("Refactor command will be implemented in Iteration 6")
    log.info(f"Query: {args.query}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="feniks",
        description="RAE-Feniks - Enterprise-grade code analysis, meta-reflection, and refactoring engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command (Iteration 2)
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest code from indexers into knowledge base"
    )
    ingest_parser.add_argument(
        "--jsonl-path",
        type=str,
        required=True,
        help="Path to the indexer JSONL output file"
    )
    ingest_parser.add_argument(
        "--collection",
        type=str,
        default="code_chunks",
        help="Qdrant collection name (default: code_chunks)"
    )
    ingest_parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the collection before ingestion"
    )
    ingest_parser.add_argument(
        "--include",
        type=str,
        help="Comma-separated include patterns (e.g., '*.js,src/**')"
    )
    ingest_parser.add_argument(
        "--exclude",
        type=str,
        help="Comma-separated exclude patterns (e.g., '*.test.js,*.spec.js')"
    )
    ingest_parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Skip invalid chunks instead of failing"
    )
    ingest_parser.set_defaults(func=handle_ingest)

    # Analyze command (Iteration 4)
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze code and generate meta-reflections"
    )
    analyze_parser.add_argument(
        "--project-id",
        type=str,
        required=True,
        help="Project identifier"
    )
    analyze_parser.add_argument(
        "--output",
        type=str,
        help="Output path for meta-reflections"
    )
    analyze_parser.set_defaults(func=handle_analyze)

    # Refactor command (Iteration 6)
    refactor_parser = subparsers.add_parser(
        "refactor",
        help="Execute refactoring workflows"
    )
    refactor_parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Natural language query for refactoring targets"
    )
    refactor_parser.add_argument(
        "--recipe",
        type=str,
        help="Path to refactoring recipe"
    )
    refactor_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry run without applying changes"
    )
    refactor_parser.set_defaults(func=handle_refactor)

    # Parse arguments
    args = parser.parse_args()

    # Handle version flag
    if args.version:
        handle_version()
        return 0

    # Handle no command
    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    try:
        args.func(args)
        return 0
    except FeniksError as e:
        log.error(f"Feniks error: {e}")
        return 1
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
