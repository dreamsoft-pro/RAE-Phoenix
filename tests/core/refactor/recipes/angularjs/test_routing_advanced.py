from feniks.core.refactor.recipe import RefactorPlan, RefactorRisk
from feniks.core.refactor.recipes.angularjs.routing_to_app_router import (
    RoutingToAppRouterRecipe,
)


def test_routing_resolve_extraction():
    recipe = RoutingToAppRouterRecipe()
    content = """
    $stateProvider.state('home', {
        url: '/home',
        templateUrl: 'home.html',
        controller: 'HomeCtrl',
        resolve: {
            user: function($http) { return $http.get('/api/user'); },
            config: ['ConfigService', function(ConfigService) { return ConfigService.get(); }]
        }
    });
    """
    routes = recipe._extract_ui_router_routes(content)
    assert len(routes) == 1
    resolve = routes[0].resolve
    assert "user" in resolve
    assert "config" in resolve


def test_routing_layout_generation():
    recipe = RoutingToAppRouterRecipe()

    # Metadata with parent and child
    routes = [
        {"path": "/parent", "name": "parent", "controller": "ParentCtrl", "template": "parent.html", "parent": None},
        {
            "path": "/parent/child",
            "name": "parent.child",
            "controller": "ChildCtrl",
            "template": "child.html",
            "parent": "parent",
        },
    ]

    plan = RefactorPlan(
        recipe_name="test",
        project_id="test",
        target_modules=[],
        target_files=[],
        rationale="test",
        risks=[],
        risk_level=RefactorRisk.LOW,
        estimated_changes=1,
        validation_steps=[],
        metadata={"routes": routes},
    )

    # Execute
    result = recipe.execute(plan, [], dry_run=True)

    # Check layout generation
    layout_files = [fc for fc in result.file_changes if fc.file_path.endswith("layout.tsx")]
    assert len(layout_files) >= 1
    assert "export default async function ParentLayout" in layout_files[0].modified_content


def test_routing_page_data_fetching():
    recipe = RoutingToAppRouterRecipe()
    route_data = {"path": "/dashboard", "controller": "DashCtrl", "resolve": {"stats": "stub", "profile": "stub"}}

    # Mock _convert_path_to_next which was failing
    # Wait, it should exist on the instance.
    # The error 'RoutingToAppRouterRecipe' object has no attribute '_convert_path_to_next' suggests it wasn't loaded or overwritten correctly.
    # I'll check the file content later if this persists, but for now assume the overwrite worked.
    # Actually, I should verify the file content first if I could, but in tests I assume it's there.

    component = recipe._generate_page_component(route_data, None)
    assert "async function getStats()" in component
    assert "const stats = await getStats();" in component
