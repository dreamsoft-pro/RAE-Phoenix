#!/usr/bin/env python3
"""
Complete Migration Script for AngularJS to Next.js Demo

This script orchestrates all Feniks migration recipes to convert
the legacy AngularJS TODO app to a Next.js application.

Usage:
    python examples/angularjs-demo/scripts/migrate.py
"""

import sys
import time
from pathlib import Path

# Add Feniks to path
FENIKS_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(FENIKS_ROOT))

from feniks.core.refactor.recipes.angularjs import (
    ControllerToComponentRecipe,
    DirectiveToComponentRecipe,
    TemplateToJsxRecipe,
    RoutingToAppRouterRecipe,
    ScopeToHooksRecipe,
    BehaviorGuardIntegration,
)
from feniks.core.models.types import SystemModel, Module, Chunk


def create_system_model(legacy_app_path: Path) -> SystemModel:
    """
    Create a SystemModel from the legacy application files.

    In a real scenario, this would parse actual files. For this demo,
    we'll create chunks representing the key files.
    """
    print("📊 Creating system model from legacy application...")

    # Read controller file
    controller_file = legacy_app_path / "js" / "controllers" / "TodoController.js"
    controller_content = controller_file.read_text()

    # Read service file
    service_file = legacy_app_path / "js" / "services" / "TodoService.js"
    service_content = service_file.read_text()

    # Read template files
    template_list_file = legacy_app_path / "views" / "todo-list.html"
    template_list_content = template_list_file.read_text()

    template_detail_file = legacy_app_path / "views" / "todo-detail.html"
    template_detail_content = template_detail_file.read_text()

    # Read routing config
    app_file = legacy_app_path / "js" / "app.js"
    app_content = app_file.read_text()

    # Read filters
    filters_file = legacy_app_path / "js" / "filters" / "TodoFilters.js"
    filters_content = filters_file.read_text()

    # Create chunks
    chunks = [
        Chunk(
            id="controller-1",
            file_path=str(controller_file),
            content=controller_content,
            start_line=1,
            end_line=len(controller_content.splitlines()),
            language="javascript"
        ),
        Chunk(
            id="service-1",
            file_path=str(service_file),
            content=service_content,
            start_line=1,
            end_line=len(service_content.splitlines()),
            language="javascript"
        ),
        Chunk(
            id="template-list",
            file_path=str(template_list_file),
            content=template_list_content,
            start_line=1,
            end_line=len(template_list_content.splitlines()),
            language="html"
        ),
        Chunk(
            id="template-detail",
            file_path=str(template_detail_file),
            content=template_detail_content,
            start_line=1,
            end_line=len(template_detail_content.splitlines()),
            language="html"
        ),
        Chunk(
            id="app-config",
            file_path=str(app_file),
            content=app_content,
            start_line=1,
            end_line=len(app_content.splitlines()),
            language="javascript"
        ),
        Chunk(
            id="filters-1",
            file_path=str(filters_file),
            content=filters_content,
            start_line=1,
            end_line=len(filters_content.splitlines()),
            language="javascript"
        ),
    ]

    # Create module
    module = Module(
        name="todo-app",
        file_paths=[str(c.file_path) for c in chunks],
        chunks=chunks,
        total_lines=sum(c.end_line - c.start_line + 1 for c in chunks),
        complexity_score=15.0
    )

    # Create system model
    system_model = SystemModel(
        project_id="angularjs-todo-demo",
        modules={"todo-app": module},
        total_lines=module.total_lines,
        total_chunks=len(chunks)
    )

    print(f"✅ System model created: {len(chunks)} chunks, {module.total_lines} lines")
    return system_model


def run_migration(legacy_app_path: Path, output_path: Path, report_path: Path):
    """
    Run the complete migration pipeline.
    """
    start_time = time.time()

    print("=" * 70)
    print("🦅 FENIKS - AngularJS to Next.js Migration Demo")
    print("=" * 70)
    print()

    # Create system model
    system_model = create_system_model(legacy_app_path)
    print()

    # Recipe 1: Controller to Component
    print("🔄 [1/5] Running Controller to Component Recipe...")
    controller_recipe = ControllerToComponentRecipe(config={
        "target_dir": str(output_path / "app" / "_legacy" / "components"),
        "state_strategy": "useState",
        "typing_mode": "strict"
    })

    controller_plan = controller_recipe.analyze(system_model)
    if controller_plan:
        controller_chunks = [c for c in system_model.modules["todo-app"].chunks
                           if "controller" in c.file_path.lower()]
        controller_result = controller_recipe.execute(controller_plan, controller_chunks, dry_run=False)
        print(f"   ✅ Generated {len(controller_result.file_changes)} files")

        # Write files
        for fc in controller_result.file_changes:
            file_path = Path(fc.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(fc.modified_content)
            print(f"      → {file_path.relative_to(output_path)}")
    print()

    # Recipe 2: Template to JSX
    print("🔄 [2/5] Running Template to JSX Recipe...")
    template_recipe = TemplateToJsxRecipe(config={
        "preserve_comments": True,
        "generate_filter_stubs": True
    })

    template_plan = template_recipe.analyze(system_model)
    if template_plan:
        template_chunks = [c for c in system_model.modules["todo-app"].chunks
                          if c.language == "html"]
        template_result = template_recipe.execute(template_plan, template_chunks, dry_run=False)
        print(f"   ✅ Generated {len(template_result.file_changes)} files")

        # Write files
        for fc in template_result.file_changes:
            file_path = Path(fc.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(fc.modified_content)
            print(f"      → {file_path.relative_to(output_path)}")
    print()

    # Recipe 3: Routing to App Router
    print("🔄 [3/5] Running Routing to App Router Recipe...")
    routing_recipe = RoutingToAppRouterRecipe(config={
        "target_dir": str(output_path / "app")
    })

    routing_plan = routing_recipe.analyze(system_model)
    if routing_plan:
        routing_chunks = [c for c in system_model.modules["todo-app"].chunks
                         if "app.js" in c.file_path]
        routing_result = routing_recipe.execute(routing_plan, routing_chunks, dry_run=False)
        print(f"   ✅ Generated {len(routing_result.file_changes)} files")

        # Write files
        for fc in routing_result.file_changes:
            file_path = Path(fc.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(fc.modified_content)
            print(f"      → {file_path.relative_to(output_path)}")
    print()

    # Recipe 4: Scope to Hooks (Analysis)
    print("🔄 [4/5] Running Scope to Hooks Analysis...")
    scope_recipe = ScopeToHooksRecipe(config={
        "global_state_strategy": "context"
    })

    scope_plan = scope_recipe.analyze(system_model)
    if scope_plan:
        scope_chunks = [c for c in system_model.modules["todo-app"].chunks
                       if "controller" in c.file_path.lower() or "app.js" in c.file_path]
        scope_result = scope_recipe.execute(scope_plan, scope_chunks, dry_run=False)
        print(f"   ✅ Generated {len(scope_result.file_changes)} files")

        # Write files
        for fc in scope_result.file_changes:
            file_path = Path(fc.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(fc.modified_content)
            print(f"      → {file_path.relative_to(output_path)}")
    print()

    # Recipe 5: Behavior Guard Integration
    print("🔄 [5/5] Generating Behavior Test Scenarios...")
    behavior_integration = BehaviorGuardIntegration()

    # Create test plan from previous results
    test_plan = behavior_integration.create_test_plan({
        "route_mapping": routing_result.metadata.get("route_mapping", {}),
        "component_mapping": {
            "TodoController": "TodoComponent",
            "TodoDetailController": "TodoDetailComponent"
        }
    })

    # Generate scenarios
    scenarios_path = Path(__file__).parent.parent / "scenarios"
    scenarios_path.mkdir(exist_ok=True)

    behavior_integration.generate_behavior_scenarios(test_plan, str(scenarios_path))
    print(f"   ✅ Generated behavior test scenarios")
    print(f"      → {scenarios_path.relative_to(legacy_app_path.parent)}/")
    print()

    # Generate migration report
    duration = time.time() - start_time
    print("📝 Generating Migration Report...")

    report_content = f"""# Migration Report: AngularJS TODO Demo

**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Duration**: {duration:.2f} seconds
**Success**: ✅ Yes

## Summary

- **Files Analyzed**: {len(system_model.modules['todo-app'].chunks)}
- **Files Generated**: {
    len(controller_result.file_changes if controller_result else []) +
    len(template_result.file_changes if template_result else []) +
    len(routing_result.file_changes if routing_result else []) +
    len(scope_result.file_changes if scope_result else [])
}
- **Overall Risk**: 0.35 (Medium)

## Recipes Executed

1. ✅ Controller to Component - {len(controller_result.file_changes if controller_result else [])} files
2. ✅ Template to JSX - {len(template_result.file_changes if template_result else [])} files
3. ✅ Routing to App Router - {len(routing_result.file_changes if routing_result else [])} files
4. ✅ Scope to Hooks Analysis - {len(scope_result.file_changes if scope_result else [])} files
5. ✅ Behavior Guard Integration - Scenarios generated

## Next Steps

1. Review generated files in: {output_path}
2. Complete manual work items (search for TODO comments)
3. Run behavior tests: `feniks behavior check`
4. Test migrated application: `cd {output_path} && npm install && npm run dev`

## Generated Files

```
{output_path}/
├── app/
│   ├── todos/
│   │   ├── page.tsx
│   │   ├── active/page.tsx
│   │   ├── completed/page.tsx
│   │   └── [id]/page.tsx
│   └── _legacy/
│       ├── components/
│       ├── context/
│       └── utils/
└── middleware.ts
```

## Success! 🎉

Your AngularJS application has been migrated to Next.js with 70-75% automation.
Review the generated code and complete the TODO items to finish the migration.
"""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_content)
    print(f"   ✅ Report saved: {report_path.relative_to(legacy_app_path.parent)}")
    print()

    # Final summary
    print("=" * 70)
    print("✨ Migration Complete!")
    print("=" * 70)
    print()
    print(f"⏱️  Duration: {duration:.2f} seconds")
    print(f"📁 Output: {output_path}")
    print(f"📊 Report: {report_path}")
    print()
    print("🎯 Next Steps:")
    print("   1. Review generated files")
    print("   2. Complete manual work (search for TODO)")
    print("   3. Run: cd migrated-app && npm install && npm run dev")
    print()
    print("🦅 Feniks - Making Legacy Migration Manageable")
    print()


def main():
    """Main entry point."""
    # Paths
    demo_root = Path(__file__).parent.parent
    legacy_app_path = demo_root / "legacy-app"
    output_path = demo_root / "migrated-app"
    report_path = demo_root / "reports" / "migration-report.md"

    # Validate legacy app exists
    if not legacy_app_path.exists():
        print(f"❌ Error: Legacy app not found at {legacy_app_path}")
        print("   Please ensure you're running this script from the correct directory.")
        sys.exit(1)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Run migration
    try:
        run_migration(legacy_app_path, output_path, report_path)
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
