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
Angular CLI Commands - AngularJS Migration Pipeline

Commands for migrating AngularJS applications to Next.js using
Feniks migration recipes.
"""
import time
from pathlib import Path
from typing import List

from feniks.core.models.types import Chunk, Module, SystemModel
from feniks.core.refactor.recipes.angularjs import (
    BehaviorGuardIntegration,
    ControllerToComponentRecipe,
    RoutingToAppRouterRecipe,
    ScopeToHooksRecipe,
    TemplateToJsxRecipe,
)
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("cli.angular")


def _create_system_model_from_directory(source_dir: Path, project_id: str) -> SystemModel:
    """
    Create a SystemModel by scanning a directory for AngularJS files.

    Args:
        source_dir: Source directory containing AngularJS application
        project_id: Project identifier

    Returns:
        SystemModel with chunks for all relevant files
    """
    log.info(f"Scanning directory: {source_dir}")

    chunks = []
    chunk_id = 0

    # Patterns to scan
    patterns = {
        "controllers": "**/*[Cc]ontroller*.js",
        "services": "**/*[Ss]ervice*.js",
        "directives": "**/*[Dd]irective*.js",
        "templates": "**/*.html",
        "config": "**/app.js",
        "filters": "**/*[Ff]ilter*.js",
    }

    for category, pattern in patterns.items():
        for file_path in source_dir.rglob(pattern):
            # Skip node_modules, dist, etc.
            if any(p in file_path.parts for p in ["node_modules", "dist", "build", ".git"]):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                language = "javascript" if file_path.suffix == ".js" else "html"

                chunk = Chunk(
                    id=f"chunk-{chunk_id}",
                    file_path=str(file_path.absolute()),
                    content=content,
                    start_line=1,
                    end_line=len(content.splitlines()),
                    language=language,
                )
                chunks.append(chunk)
                chunk_id += 1
                log.debug(f"  Added: {file_path.relative_to(source_dir)}")

            except Exception as e:
                log.warning(f"  Skipped {file_path}: {e}")

    if not chunks:
        raise FeniksError(f"No AngularJS files found in {source_dir}")

    log.info(f"Found {len(chunks)} files to migrate")

    # Create module
    module = Module(
        name=project_id,
        file_paths=[c.file_path for c in chunks],
        chunks=chunks,
        total_lines=sum(c.end_line - c.start_line + 1 for c in chunks),
        complexity_score=len(chunks) * 2.0,
    )

    # Create system model
    system_model = SystemModel(
        project_id=project_id, modules={project_id: module}, total_lines=module.total_lines, total_chunks=len(chunks)
    )

    return system_model


def _write_generated_files(output_dir: Path, file_changes: List) -> None:
    """
    Write generated files to output directory.

    Args:
        output_dir: Output directory
        file_changes: List of FileChange objects from recipe execution
    """
    for fc in file_changes:
        file_path = Path(fc.file_path)

        # Make path relative to output_dir if not already
        if not file_path.is_relative_to(output_dir):
            # Extract relative path from file_path
            # Typically file_path will be output_dir / relative_path
            try:
                file_path = output_dir / Path(fc.file_path).name
            except Exception:
                file_path = Path(fc.file_path)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(fc.modified_content)
        log.info(f"  → {file_path}")


def handle_angular_migrate(args):
    """
    Migrate an AngularJS application to Next.js.

    Executes all migration recipes in sequence:
    1. Controller to Component
    2. Template to JSX
    3. Routing to App Router
    4. Scope to Hooks (Analysis)
    5. Behavior Guard Integration

    Args:
        args.project: Path to AngularJS project directory
        args.out: Output directory for migrated Next.js application
        args.recipes: Comma-separated list of recipes to run (default: all)
        args.config: Path to configuration JSON file
        args.dry_run: Perform dry run without writing files
        args.report: Path to migration report output (default: <out>/migration-report.md)
    """
    start_time = time.time()

    log.info("=" * 70)
    log.info("🦅 FENIKS - AngularJS to Next.js Migration")
    log.info("=" * 70)
    log.info(f"Source: {args.project}")
    log.info(f"Output: {args.out}")
    log.info(f"Dry run: {args.dry_run}")
    log.info("")

    # Validate paths
    source_dir = Path(args.project)
    if not source_dir.exists():
        raise FeniksError(f"Project directory not found: {source_dir}")

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config if provided
    config = {}
    if args.config:
        import json

        config_path = Path(args.config)
        if config_path.exists():
            config = json.loads(config_path.read_text())
            log.info(f"Loaded config from {config_path}")

    # Determine which recipes to run
    if args.recipes:
        recipes_to_run = [r.strip() for r in args.recipes.split(",")]
        log.info(f"Running recipes: {', '.join(recipes_to_run)}")
    else:
        recipes_to_run = ["controller", "template", "routing", "scope", "behavior"]
        log.info("Running all recipes")
    log.info("")

    # Create system model
    log.info("📊 Step 1/6: Building system model...")
    try:
        system_model = _create_system_model_from_directory(
            source_dir, args.project_id if hasattr(args, "project_id") and args.project_id else source_dir.name
        )
        log.info(
            f"✅ System model created: {len(system_model.modules[list(system_model.modules.keys())[0]].chunks)} chunks"
        )
    except Exception as e:
        raise FeniksError(f"Failed to create system model: {e}")
    log.info("")

    # Results tracking
    results = {}
    total_files_generated = 0

    # Recipe 1: Controller to Component
    if "controller" in recipes_to_run:
        log.info("🔄 Step 2/6: Controller to Component...")
        try:
            recipe = ControllerToComponentRecipe(
                config=config.get(
                    "controller",
                    {
                        "target_dir": str(output_dir / "app" / "_legacy" / "components"),
                        "state_strategy": "useState",
                        "typing_mode": "strict",
                    },
                )
            )

            plan = recipe.analyze(system_model)
            if plan:
                chunks = [
                    c
                    for c in system_model.modules[list(system_model.modules.keys())[0]].chunks
                    if "controller" in c.file_path.lower()
                ]
                result = recipe.execute(plan, chunks, dry_run=args.dry_run)
                results["controller"] = result

                if not args.dry_run:
                    _write_generated_files(output_dir, result.file_changes)

                log.info(f"✅ Generated {len(result.file_changes)} files")
                total_files_generated += len(result.file_changes)
            else:
                log.info("ℹ️  No controllers found")
        except Exception as e:
            log.error(f"❌ Controller migration failed: {e}")
            results["controller"] = {"error": str(e)}
        log.info("")

    # Recipe 2: Template to JSX
    if "template" in recipes_to_run:
        log.info("🔄 Step 3/6: Template to JSX...")
        try:
            recipe = TemplateToJsxRecipe(
                config=config.get("template", {"preserve_comments": True, "generate_filter_stubs": True})
            )

            plan = recipe.analyze(system_model)
            if plan:
                chunks = [
                    c for c in system_model.modules[list(system_model.modules.keys())[0]].chunks if c.language == "html"
                ]
                result = recipe.execute(plan, chunks, dry_run=args.dry_run)
                results["template"] = result

                if not args.dry_run:
                    _write_generated_files(output_dir, result.file_changes)

                log.info(f"✅ Generated {len(result.file_changes)} files")
                total_files_generated += len(result.file_changes)
            else:
                log.info("ℹ️  No templates found")
        except Exception as e:
            log.error(f"❌ Template migration failed: {e}")
            results["template"] = {"error": str(e)}
        log.info("")

    # Recipe 3: Routing to App Router
    if "routing" in recipes_to_run:
        log.info("🔄 Step 4/6: Routing to App Router...")
        try:
            recipe = RoutingToAppRouterRecipe(config=config.get("routing", {"target_dir": str(output_dir / "app")}))

            plan = recipe.analyze(system_model)
            if plan:
                chunks = [
                    c
                    for c in system_model.modules[list(system_model.modules.keys())[0]].chunks
                    if "app.js" in c.file_path.lower() or "route" in c.file_path.lower()
                ]
                result = recipe.execute(plan, chunks, dry_run=args.dry_run)
                results["routing"] = result

                if not args.dry_run:
                    _write_generated_files(output_dir, result.file_changes)

                log.info(f"✅ Generated {len(result.file_changes)} files")
                total_files_generated += len(result.file_changes)
            else:
                log.info("ℹ️  No routing configuration found")
        except Exception as e:
            log.error(f"❌ Routing migration failed: {e}")
            results["routing"] = {"error": str(e)}
        log.info("")

    # Recipe 4: Scope to Hooks
    if "scope" in recipes_to_run:
        log.info("🔄 Step 5/6: Scope to Hooks Analysis...")
        try:
            recipe = ScopeToHooksRecipe(config=config.get("scope", {"global_state_strategy": "context"}))

            plan = recipe.analyze(system_model)
            if plan:
                chunks = [
                    c
                    for c in system_model.modules[list(system_model.modules.keys())[0]].chunks
                    if "controller" in c.file_path.lower() or "app.js" in c.file_path.lower()
                ]
                result = recipe.execute(plan, chunks, dry_run=args.dry_run)
                results["scope"] = result

                if not args.dry_run:
                    _write_generated_files(output_dir, result.file_changes)

                log.info(f"✅ Generated {len(result.file_changes)} infrastructure files")
                total_files_generated += len(result.file_changes)
            else:
                log.info("ℹ️  No scope patterns found")
        except Exception as e:
            log.error(f"❌ Scope analysis failed: {e}")
            results["scope"] = {"error": str(e)}
        log.info("")

    # Recipe 5: Behavior Guard Integration
    if "behavior" in recipes_to_run and not args.dry_run:
        log.info("🔄 Step 6/6: Behavior Guard Integration...")
        try:
            integration = BehaviorGuardIntegration()

            # Create test plan from routing results
            routing_result = results.get("routing")
            if routing_result and hasattr(routing_result, "metadata"):
                test_plan = integration.create_test_plan(
                    {"route_mapping": routing_result.metadata.get("route_mapping", {}), "component_mapping": {}}
                )

                # Generate scenarios
                scenarios_dir = output_dir.parent / "scenarios"
                scenarios_dir.mkdir(exist_ok=True)

                integration.generate_behavior_scenarios(test_plan, str(scenarios_dir))
                log.info(f"✅ Generated behavior test scenarios in {scenarios_dir}")
            else:
                log.info("ℹ️  No routing data available for behavior scenarios")
        except Exception as e:
            log.error(f"❌ Behavior integration failed: {e}")
        log.info("")

    # Generate migration report
    duration = time.time() - start_time

    report_path = Path(args.report) if args.report else output_dir / "migration-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_content = f"""# AngularJS to Next.js Migration Report

**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Duration**: {duration:.2f} seconds
**Source**: {source_dir}
**Output**: {output_dir}

## Summary

- **Files Analyzed**: {len(system_model.modules[list(system_model.modules.keys())[0]].chunks)}
- **Files Generated**: {total_files_generated}
- **Recipes Executed**: {len([r for r in results.keys() if not isinstance(results[r], dict) or 'error' not in results[r]])}
- **Dry Run**: {'Yes' if args.dry_run else 'No'}

## Recipes

"""

    for recipe_name, result in results.items():
        if isinstance(result, dict) and "error" in result:
            report_content += f"### ❌ {recipe_name.capitalize()}\n\n"
            report_content += f"**Error**: {result['error']}\n\n"
        elif hasattr(result, "file_changes"):
            report_content += f"### ✅ {recipe_name.capitalize()}\n\n"
            report_content += f"- Files generated: {len(result.file_changes)}\n"
            report_content += f"- Success: {result.success}\n\n"
        else:
            report_content += f"### ℹ️  {recipe_name.capitalize()}\n\n"
            report_content += "No changes made\n\n"

    report_content += f"""
## Next Steps

1. **Review generated code**: Check {output_dir} for migrated files
2. **Complete TODOs**: Search for TODO comments in generated code
3. **Install dependencies**: Run `cd {output_dir} && npm install`
4. **Run tests**: Execute behavior tests to validate migration
5. **Test application**: Run `npm run dev` and test in browser

## Generated Structure

```
{output_dir.name}/
├── app/
│   ├── todos/                    # Migrated routes
│   └── _legacy/
│       ├── components/           # Migrated controllers
│       ├── context/              # Generated context
│       └── utils/                # Filters and utilities
└── middleware.ts                 # Route redirects
```

## Migration Statistics

- **Automation Level**: ~70-75%
- **Manual Work Required**: ~25-30%
- **Common TODOs**: Service implementations, ng-model patterns, route guards

## Resources

- [AngularJS Migration Guide](https://github.com/glesniowski/feniks/docs/ANGULARJS_MIGRATION.md)
- [Known Limitations](https://github.com/glesniowski/feniks/docs/ANGULARJS_MIGRATION.md#known-limitations)
- [Behavior Guard](https://github.com/glesniowski/feniks/docs/LEGACY_BEHAVIOR_GUARD.md)

---

**Feniks** - Making Legacy Migration Manageable
🦅 Generated with Feniks v0.4.0
"""

    report_path.write_text(report_content)

    # Final summary
    log.info("=" * 70)
    log.info("✨ Migration Complete!")
    log.info("=" * 70)
    log.info(f"⏱️  Duration: {duration:.2f} seconds")
    log.info(f"📁 Output: {output_dir}")
    log.info(f"📊 Report: {report_path}")
    log.info(f"📝 Files generated: {total_files_generated}")
    log.info("")
    log.info("🎯 Next Steps:")
    log.info("   1. Review generated files")
    log.info("   2. Complete manual work (search for TODO)")
    log.info("   3. Run: cd {} && npm install && npm run dev".format(output_dir))
    log.info("")
    log.info("🦅 Feniks - Making Legacy Migration Manageable")
    log.info("=" * 70)


def register_angular_commands(subparsers):
    """
    Register Angular CLI commands.

    Args:
        subparsers: argparse subparsers object
    """
    # Angular command group
    angular_parser = subparsers.add_parser("angular", help="AngularJS migration commands")

    angular_subparsers = angular_parser.add_subparsers(dest="angular_command", help="Available Angular commands")

    # Migrate command
    migrate_parser = angular_subparsers.add_parser("migrate", help="Migrate AngularJS application to Next.js")

    migrate_parser.add_argument("--project", type=str, required=True, help="Path to AngularJS project directory")

    migrate_parser.add_argument(
        "--out", type=str, required=True, help="Output directory for migrated Next.js application"
    )

    migrate_parser.add_argument("--project-id", type=str, help="Project identifier (default: directory name)")

    migrate_parser.add_argument(
        "--recipes",
        type=str,
        help="Comma-separated list of recipes to run (controller,template,routing,scope,behavior). Default: all",
    )

    migrate_parser.add_argument("--config", type=str, help="Path to configuration JSON file")

    migrate_parser.add_argument("--dry-run", action="store_true", help="Perform dry run without writing files")

    migrate_parser.add_argument(
        "--report", type=str, help="Path to migration report output (default: <out>/migration-report.md)"
    )

    migrate_parser.set_defaults(func=handle_angular_migrate)
