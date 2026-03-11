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
Routing to App Router Recipe - Migrates AngularJS routing to Next.js App Router.

Handles:
- $routeProvider (ngRoute) → app/ directory structure
- ui-router ($stateProvider) → app/ directory structure
- Route parameters (:id) → [id] dynamic segments
- Nested routes → nested directories
- Route guards → middleware or component-level logic
- Redirects → redirect() calls
- Query parameters → searchParams
"""
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.angularjs.routing_to_app_router")


class RouterType(Enum):
    """Types of AngularJS routers."""

    NG_ROUTE = "ngRoute"  # $routeProvider
    UI_ROUTER = "ui-router"  # $stateProvider


@dataclass
class RouteDefinition:
    """Represents an AngularJS route definition."""

    path: str  # Original path (/orders/:id)
    name: Optional[str]  # State name (for ui-router)
    controller: Optional[str]
    controller_as: Optional[str]
    template_url: Optional[str]
    template: Optional[str]
    resolve: Dict[str, str]  # Resolve functions
    parent: Optional[str]  # Parent state (for ui-router)
    is_default: bool  # Default route
    redirect_to: Optional[str]  # Redirect target


@dataclass
class RoutingMetadata:
    """Metadata extracted from routing configuration."""

    router_type: RouterType
    routes: List[RouteDefinition]
    default_route: Optional[str]
    otherwise_route: Optional[str]


class RoutingToAppRouterRecipe(RefactorRecipe):
    """
    Recipe for migrating AngularJS routing to Next.js App Router.

    Mapping strategy:
    - /orders → app/orders/page.tsx
    - /orders/:id → app/orders/[id]/page.tsx
    - /orders/:id/:tab → app/orders/[id]/[tab]/page.tsx
    - Nested states → nested directories with layout.tsx
    - $stateParams/:params → useParams() hook
    - $location.search() → useSearchParams() hook
    - resolve → Server Components or async data fetching
    - otherwise/default → middleware redirect
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the recipe.

        Args:
            config: Optional configuration
        """
        super().__init__()
        self.config = config or {}
        self.target_dir = self.config.get("target_dir", "app")
        self.use_legacy_prefix = self.config.get("use_legacy_prefix", True)

    @property
    def name(self) -> str:
        return "angularjs.routing-to-app-router"

    @property
    def description(self) -> str:
        return "Migrate AngularJS routing ($routeProvider/ui-router) to Next.js App Router"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        """
        Analyze the system to find routing configuration.

        Args:
            system_model: The system model
            target: Optional dict with routing constraints

        Returns:
            RefactorPlan or None
        """
        log.info(f"Analyzing for AngularJS routing: {system_model.project_id}")

        # Find routing configuration
        routing_chunks = self._find_routing_config(system_model)

        if not routing_chunks:
            log.info("No AngularJS routing configuration found")
            return None

        # Extract routing metadata
        routing_metadata = self._extract_routing_metadata(routing_chunks)

        if not routing_metadata or not routing_metadata.routes:
            log.info("No valid routes extracted")
            return None

        # Assess risks
        risks = self._assess_risks(routing_metadata)
        risk_level = self._calculate_risk_level(routing_metadata)

        # Create refactoring plan
        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[],
            target_files=[chunk.file_path for chunk in routing_chunks],
            rationale=f"Migrate {len(routing_metadata.routes)} routes to Next.js App Router",
            risks=risks,
            risk_level=risk_level,
            estimated_changes=len(routing_metadata.routes),
            validation_steps=[
                "Verify all page.tsx files are created",
                "Check route parameter handling",
                "Validate nested route structure",
                "Test navigation between routes",
                "Review middleware for redirects",
            ],
            metadata={
                "router_type": routing_metadata.router_type.value,
                "routes": [
                    {
                        "path": r.path,
                        "name": r.name,
                        "controller": r.controller,
                        "template": r.template_url or r.template,
                        "parent": r.parent,
                        "redirect_to": r.redirect_to,
                    }
                    for r in routing_metadata.routes
                ],
                "default_route": routing_metadata.default_route,
                "otherwise_route": routing_metadata.otherwise_route,
            },
        )

        log.info(f"Created refactoring plan for {len(routing_metadata.routes)} routes")
        return plan

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        """
        Execute the routing migration.

        Args:
            plan: The refactoring plan
            chunks: Code chunks
            dry_run: If True, don't write files

        Returns:
            RefactorResult with generated route files
        """
        log.info(f"Executing routing migration (dry_run={dry_run})")

        result = RefactorResult(plan=plan, success=True)

        try:
            # Identify parents
            all_routes = plan.metadata["routes"]
            parent_names = {r["parent"] for r in all_routes if r.get("parent")}

            # Generate route structure
            route_mapping = {}

            for route_data in all_routes:
                # Skip redirects (handled separately)
                if route_data.get("redirect_to"):
                    continue

                # Convert path to Next.js structure
                next_path = self._convert_path_to_next(route_data["path"])

                # Determine if this is a layout (parent route)
                is_layout = route_data.get("name") in parent_names

                # Generate page.tsx (Leaf or Index)
                page_code = self._generate_page_component(route_data, plan)
                page_file_path = f"{self.target_dir}{next_path}/page.tsx"

                file_change = FileChange(
                    file_path=page_file_path, original_content="", modified_content=page_code, change_type="create"
                )
                result.file_changes.append(file_change)

                # Generate layout.tsx if parent
                if is_layout:
                    layout_code = self._generate_layout_component(route_data, plan)
                    layout_file_path = f"{self.target_dir}{next_path}/layout.tsx"

                    layout_change = FileChange(
                        file_path=layout_file_path,
                        original_content="",
                        modified_content=layout_code,
                        change_type="create",
                    )
                    result.file_changes.append(layout_change)
                    log.info(f"Generated layout: {layout_file_path}")

                route_mapping[route_data["path"]] = {
                    "nextPath": next_path,
                    "file": page_file_path,
                    "controller": route_data.get("controller"),
                    "template": route_data.get("template"),
                }

                log.info(f"Generated route: {page_file_path}")

            # Generate middleware for redirects
            if plan.metadata.get("otherwise_route"):
                middleware_code = self._generate_middleware(plan)
                middleware_path = "middleware.ts"

                middleware_change = FileChange(
                    file_path=middleware_path,
                    original_content="",
                    modified_content=middleware_code,
                    change_type="create",
                )
                result.file_changes.append(middleware_change)

                log.info("Generated middleware for redirects")

            # Generate route mapping JSON
            result.metadata["route_mapping"] = route_mapping

        except Exception as e:
            log.error(f"Error during execution: {e}", exc_info=True)
            result.success = False
            result.errors.append(str(e))

        return result

    def _generate_layout_component(self, route_data: Dict[str, Any], plan: RefactorPlan) -> str:
        """Generate layout.tsx for nested routes."""
        path = route_data["path"]
        component_name = self._path_to_component_name(path).replace("Page", "Layout")

        # Resolve generation similar to page
        data_fetching_funcs = ""
        data_fetching_calls = ""
        resolve_map = route_data.get("resolve", {})
        if resolve_map:
            for key, _ in resolve_map.items():
                func_name = f"get{key.capitalize()}"
                data_fetching_funcs += f"async function {func_name}() {{ return {{}}; }}\n"
                data_fetching_calls += f"  const {key} = await {func_name}();\n"

        return f"""// Generated by Feniks - Layout for {path}
import React from 'react';

{data_fetching_funcs}

export default async function {component_name}({{ children }}: {{ children: React.ReactNode }}) {{
{data_fetching_calls}
  return (
    <div className="layout-wrapper">
      {{/* TODO: Render parent template content here */}}
      {{children}}
    </div>
  );
}}
"""

    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the routing migration.

        Args:
            result: The refactoring result

        Returns:
            bool: True if validation passed
        """
        log.info("Validating routing migration")

        validation_results = {}

        # Check all routes have page.tsx
        expected_count = len([r for r in result.plan.metadata["routes"] if not r["redirect_to"]])
        actual_page_count = len([fc for fc in result.file_changes if fc.file_path.endswith("page.tsx")])
        validation_results["all_pages_generated"] = actual_page_count == expected_count

        # Check syntax
        for file_change in result.file_changes:
            if file_change.file_path.endswith(".tsx"):
                syntax_valid = self._validate_syntax(file_change.modified_content)
                validation_results[f"syntax_{Path(file_change.file_path).name}"] = syntax_valid

        result.validation_results = validation_results

        return all(validation_results.values())

    # Helper methods

    def _find_routing_config(self, system_model: SystemModel) -> List[Chunk]:
        """Find routing configuration chunks."""
        routing_chunks = []

        for module_name, module in system_model.modules.items():
            for chunk in module.chunks:
                if self._is_routing_chunk(chunk):
                    routing_chunks.append(chunk)

        return routing_chunks

    def _is_routing_chunk(self, chunk: Chunk) -> bool:
        """Check if chunk contains routing configuration."""
        patterns = [
            r"\$routeProvider",
            r"\$stateProvider",
            r"\.config\s*\(\s*\[.*?routeProvider",
            r"\.config\s*\(\s*\[.*?stateProvider",
        ]

        for pattern in patterns:
            if re.search(pattern, chunk.content):
                return True

        return False

    def _extract_routing_metadata(self, chunks: List[Chunk]) -> Optional[RoutingMetadata]:
        """Extract routing metadata from chunks."""
        all_routes = []
        router_type = RouterType.NG_ROUTE
        default_route = None
        otherwise_route = None

        for chunk in chunks:
            # Detect router type
            if "$stateProvider" in chunk.content:
                router_type = RouterType.UI_ROUTER
                routes = self._extract_ui_router_routes(chunk.content)
            else:
                routes = self._extract_ng_route_routes(chunk.content)

            all_routes.extend(routes)

            # Extract otherwise/default
            otherwise_match = re.search(r'otherwise\s*\(\s*["\']([^"\']+)["\']', chunk.content)
            if otherwise_match:
                otherwise_route = otherwise_match.group(1)

        if not all_routes:
            return None

        return RoutingMetadata(
            router_type=router_type, routes=all_routes, default_route=default_route, otherwise_route=otherwise_route
        )

    def _extract_ng_route_routes(self, content: str) -> List[RouteDefinition]:
        """Extract routes from $routeProvider configuration."""
        routes = []

        # Pattern: .when('/path', { controller: '...', templateUrl: '...' })
        when_pattern = r'\.when\s*\(\s*["\']([^"\']+)["\']\s*,\s*\{([^}]+)\}'

        for match in re.finditer(when_pattern, content):
            path = match.group(1)
            config = match.group(2)

            # Extract controller
            controller_match = re.search(r'controller\s*:\s*["\']([^"\']+)["\']', config)
            controller = controller_match.group(1) if controller_match else None

            # Extract controllerAs
            controller_as_match = re.search(r'controllerAs\s*:\s*["\']([^"\']+)["\']', config)
            controller_as = controller_as_match.group(1) if controller_as_match else None

            # Extract templateUrl
            template_url_match = re.search(r'templateUrl\s*:\s*["\']([^"\']+)["\']', config)
            template_url = template_url_match.group(1) if template_url_match else None

            # Extract template
            template_match = re.search(r'template\s*:\s*["\']([^"\']+)["\']', config)
            template = template_match.group(1) if template_match else None

            # Extract redirectTo
            redirect_match = re.search(r'redirectTo\s*:\s*["\']([^"\']+)["\']', config)
            redirect_to = redirect_match.group(1) if redirect_match else None

            routes.append(
                RouteDefinition(
                    path=path,
                    name=None,
                    controller=controller,
                    controller_as=controller_as,
                    template_url=template_url,
                    template=template,
                    resolve={},
                    parent=None,
                    is_default=False,
                    redirect_to=redirect_to,
                )
            )

        return routes

    def _convert_path_to_next(self, angular_path: str) -> str:
        """Convert AngularJS path to Next.js path."""
        # Remove leading slash
        path = angular_path.lstrip("/")

        # Convert :param to [param]
        path = re.sub(r":(\w+)", r"[\1]", path)

        # Handle optional parameters (ui-router)
        path = path.replace("?", "")

        # Add leading slash
        return f"/{path}" if path else ""

    def _extract_ui_router_routes(self, content: str) -> List[RouteDefinition]:
        """Extract routes from ui-router $stateProvider."""
        routes = []

        # Pattern: .state('name', { url: '/path', ... })
        # Using a simpler regex to capture the whole config block first
        state_pattern = r'\.state\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\{[\s\S]*?\})\s*\)'

        for match in re.finditer(state_pattern, content):
            state_name = match.group(1)
            config = match.group(2)

            # Extract url
            url_match = re.search(r'url\s*:\s*["\']([^"\']+)["\']', config)
            url = url_match.group(1) if url_match else f"/{state_name}"

            # Extract controller
            controller_match = re.search(r'controller\s*:\s*["\']([^"\']+)["\']', config)
            controller = controller_match.group(1) if controller_match else None

            # Extract controllerAs
            controller_as_match = re.search(r'controllerAs\s*:\s*["\']([^"\']+)["\']', config)
            controller_as = controller_as_match.group(1) if controller_as_match else None

            # Extract templateUrl
            template_url_match = re.search(r'templateUrl\s*:\s*["\']([^"\']+)["\']', config)
            template_url = template_url_match.group(1) if template_url_match else None

            # Extract parent
            parent_match = re.search(r'parent\s*:\s*["\']([^"\']+)["\']', config)
            parent = parent_match.group(1) if parent_match else None

            # Check if state name has dot (nested)
            if "." in state_name and not parent:
                parent = state_name.rsplit(".", 1)[0]

            # Extract resolve
            resolve = {}
            # Try to find resolve block. Logic: find 'resolve:', then capture inside braces.
            # This is hard with regex. Simplified assumption: resolve block doesn't contain 'resolve:' string inside.
            resolve_match = re.search(r"resolve\s*:\s*\{", config)
            if resolve_match:
                start = resolve_match.end()
                # Basic brace counting
                brace_count = 1
                end = start
                for i, char in enumerate(config[start:]):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                    if brace_count == 0:
                        end = start + i
                        break

                resolve_block = config[start:end]
                # Find keys
                for res_item in re.finditer(r"(\w+)\s*:", resolve_block):
                    resolve[res_item.group(1)] = "data_fetch_stub"

            routes.append(
                RouteDefinition(
                    path=url,
                    name=state_name,
                    controller=controller,
                    controller_as=controller_as,
                    template_url=template_url,
                    template=None,
                    resolve=resolve,
                    parent=parent,
                    is_default=False,
                    redirect_to=None,
                )
            )

        return routes

    # ... existing methods ...

    def _generate_page_component(self, route_data: Dict[str, Any], plan: RefactorPlan) -> str:
        """Generate page.tsx component for a route."""
        # Extract route name for component
        path = route_data["path"]
        component_name = self._path_to_component_name(path)

        # Check if has parameters
        has_params = "[" in self._convert_path_to_next(path)

        # Generate params interface
        params_interface = self._generate_params_interface(path) if has_params else ""

        # Generate Data Fetching from Resolve
        data_fetching_funcs = ""
        data_fetching_calls = ""

        resolve_map = route_data.get("resolve", {})
        if resolve_map:
            for key, _ in resolve_map.items():
                func_name = f"get{key.capitalize()}"
                data_fetching_funcs += f"""
async function {func_name}() {{
  // TODO: Implement data fetching for '{key}'
  // This replaces the AngularJS resolve function
  return {{}};
}}
"""
                data_fetching_calls += f"  const {key} = await {func_name}();\n"

        # Generate component
        component = f"""// Generated by Feniks - AngularJS Route to Next.js Page
// Original route: {path}
// Controller: {route_data.get('controller', 'N/A')}
// Template: {route_data.get('template', 'N/A')}

import React from 'react';

{params_interface}

{data_fetching_funcs}

export default async function {component_name}({{ params }}: {component_name}Props) {{
  // Data Fetching (migrated from resolve)
{data_fetching_calls}

  // TODO: Replace with migrated controller component
  // Original controller: {route_data.get('controller', 'N/A')}

  return (
    <div>
      <h1>{component_name}</h1>
      <p>Migrated from AngularJS route: {path}</p>
      {{/* TODO: Import and render migrated component, passing data as props */}}
    </div>
  );
}}
"""

        return component

    def _generate_params_interface(self, path: str) -> str:
        """Generate TypeScript interface for route params."""
        # Extract parameter names
        params = re.findall(r":(\w+)", path)

        if not params:
            return ""

        params_str = "\n".join([f"  {param}: string;" for param in params])

        return f"""interface PageProps {{
  params: {{
{params_str}
  }};
}}

type {self._path_to_component_name(path)}Props = PageProps;
"""

    def _path_to_component_name(self, path: str) -> str:
        """Convert path to component name."""
        # Remove leading slash and parameters
        clean_path = re.sub(r"[/:?\[\]]", " ", path).strip()
        # Convert to PascalCase
        parts = clean_path.split()
        component_name = "".join(word.capitalize() for word in parts if word)
        return component_name + "Page" if component_name else "HomePage"

    def _generate_middleware(self, plan: RefactorPlan) -> str:
        """Generate Next.js middleware for redirects."""
        otherwise_route = plan.metadata.get("otherwise_route", "/")

        middleware = f"""// Generated by Feniks - Route Middleware
// Handles redirects from AngularJS routing

import {{ NextResponse }} from 'next/server';
import type {{ NextRequest }} from 'next/server';

export function middleware(request: NextRequest) {{
  const {{ pathname }} = request.nextUrl;

  // Handle default route redirect
  if (pathname === '/') {{
    return NextResponse.redirect(new URL('{otherwise_route}', request.url));
  }}

  // TODO: Add additional route guards and redirects here

  return NextResponse.next();
}}

export const config = {{
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}};
"""

        return middleware

    def _validate_syntax(self, content: str) -> bool:
        """Basic syntax validation."""
        if content.count("{") != content.count("}"):
            return False
        if content.count("(") != content.count(")"):
            return False

        # Check for export default
        if "export default" not in content:
            return False

        return True
