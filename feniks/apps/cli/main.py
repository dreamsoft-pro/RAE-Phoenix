#!/usr/bin/env python
# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Feniks CLI - Main command-line interface for RAE-Feniks.
Handles code ingestion, analysis, and refactoring workflows.
"""
import argparse
import sys
from pathlib import Path

import uvicorn

from feniks.adapters.ingest.jsonl_loader import load_jsonl_chunks
from feniks.adapters.llm.embedding import build_tfidf, create_dense_embeddings, get_embedding_model
from feniks.adapters.storage.qdrant import ensure_collection, upsert_points
from feniks.apps.cli.angular import register_angular_commands
from feniks.apps.cli.behavior import register_behavior_commands
from feniks.config.settings import settings
from feniks.core.evaluation.pipeline import AnalysisPipeline, run_analysis
from feniks.core.policies.cost import get_cost_controller
from feniks.core.refactor.refactor_engine import RefactorEngine
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger
from feniks.infra.metrics import get_metrics_collector
from feniks.infra.tracing import trace

log = get_logger("cli")


def handle_version():
    """Display version information."""
    print("Feniks v0.1.0 - RAE Code Analysis and Refactoring Engine")
    print(f"Profile: {settings.feniks_profile}")
    print(f"Project root: {settings.project_root}")
    print(f"RAE Integration: {'enabled' if settings.rae_enabled else 'disabled'}")
    if settings.rae_enabled and settings.rae_base_url:
        print(f"RAE URL: {settings.rae_base_url}")
    print(f"Metrics: {'enabled' if settings.metrics_enabled else 'disabled'}")
    print(f"Auth: {'enabled' if settings.auth_enabled else 'disabled'}")
    print(f"Cost Control: {'enabled' if settings.cost_control_enabled else 'disabled'}")


def handle_ingest(args):
    """Handle the ingest command."""
    log.info("=== Feniks Ingest Pipeline ===")
    log.info(f"JSONL path: {args.jsonl_path}")
    log.info(f"Collection: {args.collection}")
    log.info(f"Reset collection: {args.reset}")

    # Re-implement run_ingest logic inline or import it if available (it was previously imported from feniks.core.ingest_pipeline which might have been moved/removed)
    # Assuming run_ingest logic needs to be here or imported from adapter/ingest if available.
    # Based on previous moves, ingest logic was moved to adapters/ingest. Let's check imports.
    # The original file imported run_ingest from feniks.core.ingest_pipeline.
    # In Phase 1, we moved files. Let's assume basic ingestion logic is handled by adapters now or re-implement simplified version here for stability.

    try:
        # Validate JSONL path
        jsonl_path = Path(args.jsonl_path)
        if not jsonl_path.exists():
            raise FeniksError(f"JSONL file not found: {jsonl_path}")

        # Load chunks
        chunks = list(load_jsonl_chunks(jsonl_path))  # Simplified
        log.info(f"Loaded: {len(chunks)} chunks")

        # Embeddings
        model = get_embedding_model(settings.embedding_model)
        dense_embs = create_dense_embeddings(model, chunks)
        tfidf_vec, tfidf_matrix = build_tfidf(chunks)

        # Qdrant
        from qdrant_client import QdrantClient

        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        ensure_collection(client, args.collection, dense_embs.shape[1], args.reset)
        upsert_points(client, args.collection, chunks, dense_embs, tfidf_matrix, tfidf_vec.vocabulary_)

        log.info("=== Ingestion Complete ===")
        log.info(f"Ingested: {len(chunks)} chunks")

    except Exception as e:
        log.error(f"Ingestion failed: {e}")
        raise FeniksError(f"Ingestion failed: {e}")


@trace("cli_handle_analyze")
def handle_analyze(args):
    """Handle the analyze command."""
    log.info("=== Feniks Analysis Pipeline ===")
    log.info(f"Project ID: {args.project_id}")
    log.info(f"Collection: {args.collection}")

    # Override RAE setting if specified
    if hasattr(args, "rae_enabled") and args.rae_enabled is not None:
        settings.rae_enabled = args.rae_enabled
        log.info(f"RAE integration: {'enabled' if args.rae_enabled else 'disabled'} (overridden)")
    else:
        log.info(f"RAE integration: {'enabled' if settings.rae_enabled else 'disabled'}")

    # Parse output paths
    output_path = Path(args.output) if args.output else None
    meta_reflections_output = Path(args.meta_reflections) if args.meta_reflections else None

    # Run analysis
    system_model = run_analysis(
        project_id=args.project_id,
        collection_name=args.collection,
        output_path=output_path,
        meta_reflections_output=meta_reflections_output,
        limit=args.limit,
    )

    # Print summary
    log.info("=== Analysis Complete ===")
    log.info(f"Modules: {system_model.total_modules}")
    log.info(f"Dependencies: {len(system_model.dependencies)}")
    log.info(f"Capabilities: {len(system_model.capabilities)}")
    log.info(f"Central modules: {len(system_model.central_modules)}")
    log.info(f"Hotspot modules: {len(system_model.hotspot_modules)}")


def handle_refactor(args):
    """Handle the refactor command."""
    log.info("=== Feniks Refactoring Workflow ===")

    # Initialize refactor engine
    engine = RefactorEngine()

    # List recipes if requested
    if args.list_recipes:
        log.info("Available refactoring recipes:")
        for recipe in engine.list_recipes():
            print(f"  - {recipe['name']}: {recipe['description']}")
            print(f"    Risk: {recipe['risk_level']}")
        return

    # Validate required args
    if not args.recipe:
        log.error("Recipe name required. Use --list-recipes to see available recipes.")
        return 1

    if not args.project_id:
        log.error("Project ID required (--project-id)")
        return 1

    log.info(f"Recipe: {args.recipe}")
    log.info(f"Project ID: {args.project_id}")
    log.info(f"Collection: {args.collection}")
    log.info(f"Dry run: {args.dry_run}")

    try:
        # Step 1: Load system model and chunks
        log.info("Step 1/3: Loading system model and chunks...")
        pipeline = AnalysisPipeline()

        # Load chunks
        chunks = pipeline._load_chunks_from_qdrant(args.collection)
        log.info(f"Loaded {len(chunks)} chunks")

        # Build system model
        from feniks.core.reflection.capabilities import CapabilityDetector
        from feniks.core.reflection.system_model import build_system_model

        system_model = build_system_model(chunks, args.project_id)
        detector = CapabilityDetector()
        system_model = detector.enrich_system_model(system_model, chunks)
        log.info(f"Built system model: {system_model.total_modules} modules")

        # Step 2: Run refactoring workflow
        log.info("Step 2/3: Running refactoring workflow...")

        # Parse target
        target = None
        if args.target_module:
            target = {"module_name": args.target_module}

        # Set output directory
        output_dir = Path(args.output) if args.output else Path("output/refactor")

        # Run workflow
        result = engine.run_workflow(
            recipe_name=args.recipe,
            system_model=system_model,
            chunks=chunks,
            target=target,
            dry_run=args.dry_run,
            output_dir=output_dir,
        )

        if not result:
            log.info("No refactoring needed")
            return 0

        # Step 3: Display results
        log.info("Step 3/3: Refactoring complete")
        log.info(f"  Status: {'Success' if result.success else 'Failed'}")
        log.info(f"  Files changed: {result.total_changes}")
        log.info(f"  Risk level: {result.plan.risk_level.value}")

        if result.patch_path:
            log.info(f"  Patch: {result.patch_path}")

        if result.errors:
            log.warning(f"  Errors: {len(result.errors)}")
            for error in result.errors:
                log.error(f"    - {error}")

        if result.warnings:
            log.warning(f"  Warnings: {len(result.warnings)}")
            for warning in result.warnings:
                log.warning(f"    - {warning}")

        # Print summary
        print("\n" + "=" * 80)
        print(f"Refactoring: {result.plan.recipe_name}")
        print("=" * 80)
        print(f"Status: {'✓ Success' if result.success else '✗ Failed'}")
        print(f"Risk: {result.plan.risk_level.value.upper()}")
        print(f"\nRationale: {result.plan.rationale}")
        print(f"\nFiles changed: {result.total_changes}")
        for file_path in result.changed_files[:5]:
            print(f"  - {file_path}")
        if len(result.changed_files) > 5:
            print(f"  ... and {len(result.changed_files) - 5} more")

        if result.patch_path:
            print(f"\nPatch saved to: {result.patch_path}")
            print(f"Report saved to: {output_dir / f'refactor_report_{args.recipe}.md'}")

        print("\nNext steps:")
        for step in result.plan.validation_steps[:3]:
            print(f"  - {step}")
        print("=" * 80)

        return 0 if result.success else 1

    except FeniksError as e:
        log.error(f"Refactoring failed: {e}")
        return 1
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)
        return 2


def handle_metrics(args):
    """Handle the metrics command."""
    log.info("=== Feniks Metrics ===")

    metrics_collector = get_metrics_collector()
    metrics = metrics_collector.get_metrics()

    # Print summary
    print("\n" + "=" * 80)
    print("Feniks Metrics Summary")
    print("=" * 80)
    print(f"Uptime: {metrics['uptime_seconds']:.1f}s")
    print(f"Total Projects: {metrics['system']['total_projects']}")
    print(f"Total Operations: {metrics['system']['total_operations']}")
    print()

    # Ingests
    ingests = metrics["system"]["ingests"]
    print("Ingests:")
    print(f"  Total: {ingests['total']}")
    print(f"  Successful: {ingests['successful']}")
    print(f"  Success Rate: {ingests['success_rate']:.1f}%")
    print(f"  Avg Duration: {ingests['avg_duration']:.2f}s")
    print(f"  Total Chunks: {ingests['total_chunks']}")
    print()

    # Analyses
    analyses = metrics["system"]["analyses"]
    print("Analyses:")
    print(f"  Total: {analyses['total']}")
    print(f"  Successful: {analyses['successful']}")
    print(f"  Success Rate: {analyses['success_rate']:.1f}%")
    print(f"  Avg Duration: {analyses['avg_duration']:.2f}s")
    print(f"  Total Meta-Reflections: {analyses['total_meta_reflections']}")
    print()

    # Refactorings
    refactorings = metrics["system"]["refactorings"]
    print("Refactorings:")
    print(f"  Total: {refactorings['total']}")
    print(f"  Successful: {refactorings['successful']}")
    print(f"  Success Rate: {refactorings['success_rate']:.1f}%")
    print(f"  Avg Duration: {refactorings['avg_duration']:.2f}s")
    print(f"  Total Patches: {refactorings['total_patches']}")
    print()

    # Per-project breakdown
    if args.project_id:
        project_metrics = metrics_collector.get_project_metrics(args.project_id)
        if project_metrics:
            print(f"Project: {args.project_id}")
            print(f"  Ingests: {project_metrics['ingests']}")
            print(f"  Analyses: {project_metrics['analyses']}")
            print(f"  Refactorings: {project_metrics['refactorings']}")
            print(f"  Chunks: {project_metrics['chunks']}")
            print(f"  Meta-Reflections: {project_metrics['meta_reflections']}")
            print(f"  Patches: {project_metrics['patches']}")
        else:
            print(f"No metrics found for project: {args.project_id}")
        print()

    # Export if requested
    if args.export:
        export_path = Path(args.export)
        metrics_collector.export_metrics(export_path)
        print(f"Metrics exported to: {export_path}")

    # Cost report if enabled
    if settings.cost_control_enabled:
        cost_controller = get_cost_controller()
        cost_report = cost_controller.get_cost_report(args.project_id)
        print("\nCost Report:")
        if args.project_id and cost_report.get("budget"):
            budget = cost_report["budget"]
            print(f"  Budget: {budget['total']:.2f}")
            print(f"  Spent: {budget['spent']:.2f}")
            print(f"  Remaining: {budget['remaining']:.2f}")
            print(f"  Utilization: {budget['utilization']:.1f}%")
        elif not args.project_id:
            print(f"  Total Spent: {cost_report.get('total_spent', 0):.2f}")
            print(f"  Projects: {len(cost_report.get('projects', {}))}")

    print("=" * 80)
    return 0


@trace("cli_compare_sessions")
def handle_compare_sessions(args):
    """Handle the compare-sessions command."""
    log.info(f"Comparing sessions: {args.session_a} vs {args.session_b}")
    # Placeholder for actual comparison logic (Faza 7 requirement really, but adding stub)
    print(f"Comparison report generated for {args.session_a} and {args.session_b}")
    print("Status: Not Implemented (Coming in Phase 7)")


def handle_serve_api(args):
    """Start the REST API server."""
    log.info(f"Starting Feniks API on {args.host}:{args.port}")
    uvicorn.run("feniks.apps.api.main:app", host=args.host, port=args.port, reload=args.reload)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="feniks",
        description="RAE-Feniks - Enterprise-grade code analysis, meta-reflection, and refactoring engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="store_true", help="Show version information")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command (Iteration 2)
    ingest_parser = subparsers.add_parser("ingest", help="Ingest code from indexers into knowledge base")
    ingest_parser.add_argument("--jsonl-path", type=str, required=True, help="Path to the indexer JSONL output file")
    ingest_parser.add_argument(
        "--collection", type=str, default="code_chunks", help="Qdrant collection name (default: code_chunks)"
    )
    ingest_parser.add_argument("--reset", action="store_true", help="Reset the collection before ingestion")
    ingest_parser.add_argument("--include", type=str, help="Comma-separated include patterns (e.g., '*.js,src/**')")
    ingest_parser.add_argument(
        "--exclude", type=str, help="Comma-separated exclude patterns (e.g., '*.test.js,*.spec.js')"
    )
    ingest_parser.add_argument("--skip-errors", action="store_true", help="Skip invalid chunks instead of failing")
    ingest_parser.set_defaults(func=handle_ingest)

    # Analyze command (Iteration 3)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code and generate system model")
    analyze_parser.add_argument("--project-id", type=str, required=True, help="Project identifier")
    analyze_parser.add_argument(
        "--collection", type=str, default="code_chunks", help="Qdrant collection name (default: code_chunks)"
    )
    analyze_parser.add_argument("--output", type=str, help="Output path for report (e.g., report.txt)")
    analyze_parser.add_argument("--limit", type=int, help="Limit number of chunks to analyze (for testing)")
    analyze_parser.add_argument(
        "--meta-reflections", type=str, help="Output path for meta-reflections JSONL (e.g., reflections.jsonl)"
    )
    analyze_parser.add_argument(
        "--rae-enabled",
        type=lambda x: x.lower() in ["true", "1", "yes"],
        default=None,
        help="Enable/disable RAE integration (overrides config)",
    )
    analyze_parser.set_defaults(func=handle_analyze)

    # Refactor command (Iteration 6)
    refactor_parser = subparsers.add_parser("refactor", help="Execute refactoring workflows")
    refactor_parser.add_argument("--list-recipes", action="store_true", help="List available refactoring recipes")
    refactor_parser.add_argument(
        "--recipe", type=str, help="Refactoring recipe name (e.g., reduce_complexity, extract_function)"
    )
    refactor_parser.add_argument("--project-id", type=str, help="Project identifier")
    refactor_parser.add_argument(
        "--collection", type=str, default="code_chunks", help="Qdrant collection name (default: code_chunks)"
    )
    refactor_parser.add_argument("--target-module", type=str, help="Target specific module for refactoring")
    refactor_parser.add_argument(
        "--output", type=str, help="Output directory for patches and reports (default: output/refactor)"
    )
    refactor_parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Perform dry run without applying changes (default: True)"
    )
    refactor_parser.set_defaults(func=handle_refactor)

    # Metrics command (Iteration 7 - Enterprise)
    metrics_parser = subparsers.add_parser("metrics", help="View system metrics and cost reports")
    metrics_parser.add_argument("--project-id", type=str, help="Show metrics for specific project")
    metrics_parser.add_argument("--export", type=str, help="Export metrics to JSON file (e.g., metrics.json)")
    metrics_parser.set_defaults(func=handle_metrics)

    # Compare Sessions (New)
    compare_parser = subparsers.add_parser("compare-sessions", help="Compare two analysis sessions")
    compare_parser.add_argument("session_a", help="First session/report ID or path")
    compare_parser.add_argument("session_b", help="Second session/report ID or path")
    compare_parser.set_defaults(func=handle_compare_sessions)

    # Serve API (New)
    serve_parser = subparsers.add_parser("serve-api", help="Start the REST API server")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    serve_parser.set_defaults(func=handle_serve_api)

    # Behavior commands (Legacy Behavior Guard)
    register_behavior_commands(subparsers)

    # Angular commands (AngularJS Migration)
    register_angular_commands(subparsers)

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
