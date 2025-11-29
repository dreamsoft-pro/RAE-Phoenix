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
System Model Builder - constructs system model from code chunks.
Builds module graph, dependency graph, and computes metrics.
"""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple

from feniks.core.models.types import ApiEndpoint, Chunk, Module, ModuleDependency, ModuleType, SystemModel
from feniks.infra.logging import get_logger

log = get_logger("core.system_model_builder")


class SystemModelBuilder:
    """Builds a SystemModel from a list of chunks."""

    def __init__(self, project_id: str):
        """
        Initialize the builder.

        Args:
            project_id: Unique identifier for the project
        """
        self.project_id = project_id
        self.chunks: List[Chunk] = []
        self.modules: Dict[str, Module] = {}
        self.dependency_map: Dict[Tuple[str, str, str], ModuleDependency] = {}

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Add chunks to be analyzed."""
        self.chunks.extend(chunks)
        log.info(f"Added {len(chunks)} chunks to system model builder")

    def _infer_module_type(self, module_name: str, file_paths: List[str]) -> ModuleType:
        """Infer module type from name and file paths."""
        name_lower = module_name.lower()
        paths_str = " ".join(file_paths).lower()

        # Check file paths and module name for patterns
        if "backend" in paths_str or "server" in paths_str or "api" in paths_str:
            return ModuleType.BACKEND
        elif "frontend" in paths_str or "client" in paths_str or "ui" in paths_str or "app" in name_lower:
            return ModuleType.FRONTEND
        elif "core" in paths_str or "core" in name_lower:
            return ModuleType.CORE
        elif "lib" in paths_str or "library" in name_lower:
            return ModuleType.LIBRARY
        elif "util" in paths_str or "helper" in paths_str:
            return ModuleType.UTILITY
        else:
            return ModuleType.UNKNOWN

    def _build_modules(self) -> None:
        """Build module objects from chunks."""
        log.info("Building modules from chunks...")

        # Group chunks by module
        module_chunks: Dict[str, List[Chunk]] = defaultdict(list)
        for chunk in self.chunks:
            module_name = chunk.module or "unknown"
            module_chunks[module_name].append(chunk)

        # Create Module objects
        for module_name, chunks in module_chunks.items():
            # Collect file paths
            file_paths = list(set(c.file_path for c in chunks))

            # Infer module type
            module_type = self._infer_module_type(module_name, file_paths)

            # Calculate metrics
            total_lines = sum((c.end_line - c.start_line + 1) for c in chunks)
            total_complexity = sum(c.cyclomatic_complexity for c in chunks)
            avg_complexity = total_complexity / len(chunks) if chunks else 0.0

            # Collect business tags
            business_tags = set()
            for chunk in chunks:
                business_tags.update(chunk.business_tags)

            # Create module
            module = Module(
                name=module_name,
                module_type=module_type,
                file_paths=file_paths,
                chunks=[c.id for c in chunks],
                total_lines=total_lines,
                total_complexity=total_complexity,
                avg_complexity=avg_complexity,
                chunk_count=len(chunks),
                business_tags=business_tags,
            )

            self.modules[module_name] = module

        log.info(f"Built {len(self.modules)} modules")

    def _build_dependencies(self) -> None:
        """Build dependency graph from chunk dependencies."""
        log.info("Building dependency graph...")

        for chunk in self.chunks:
            source_module = chunk.module or "unknown"

            # Process dependencies
            for dep in chunk.dependencies:
                target_module = dep.value

                # Skip self-dependencies
                if source_module == target_module:
                    continue

                # Create or update dependency
                key = (source_module, target_module, dep.type)
                if key in self.dependency_map:
                    self.dependency_map[key].count += 1
                    self.dependency_map[key].chunks.append(chunk.id)
                else:
                    self.dependency_map[key] = ModuleDependency(
                        source=source_module, target=target_module, dependency_type=dep.type, count=1, chunks=[chunk.id]
                    )

        # Update module dependency lists
        for dep in self.dependency_map.values():
            if dep.source in self.modules:
                self.modules[dep.source].dependencies_out.append(dep.target)

            if dep.target in self.modules:
                self.modules[dep.target].dependencies_in.append(dep.source)

        log.info(f"Built {len(self.dependency_map)} dependencies")

    def _compute_graph_metrics(self) -> None:
        """Compute graph metrics for modules."""
        log.info("Computing graph metrics...")

        for module in self.modules.values():
            # In/out degree
            module.in_degree = len(set(module.dependencies_in))
            module.out_degree = len(set(module.dependencies_out))

            # Centrality (simple degree centrality)
            total_degree = module.in_degree + module.out_degree
            max_possible_degree = len(self.modules) - 1
            if max_possible_degree > 0:
                module.centrality = total_degree / max_possible_degree
            else:
                module.centrality = 0.0

        # Identify special modules
        self._identify_special_modules()

    def _identify_special_modules(self) -> None:
        """Identify central, boundary, and hotspot modules."""
        if not self.modules:
            return

        # Calculate thresholds
        centralities = [m.centrality for m in self.modules.values()]
        complexities = [m.avg_complexity for m in self.modules.values()]

        avg_centrality = sum(centralities) / len(centralities) if centralities else 0
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0

        centrality_threshold = avg_centrality * 1.5
        complexity_threshold = avg_complexity * 1.5

        for module in self.modules.values():
            # Central modules: high centrality
            if module.centrality >= centrality_threshold:
                module.is_central = True

            # Boundary modules: low in-degree or low out-degree
            if module.in_degree <= 1 or module.out_degree <= 1:
                module.is_boundary = True

            # Hotspot modules: high complexity + high centrality
            if module.avg_complexity >= complexity_threshold and module.centrality >= centrality_threshold:
                module.is_hotspot = True

        log.info(f"Identified central modules: {sum(1 for m in self.modules.values() if m.is_central)}")
        log.info(f"Identified boundary modules: {sum(1 for m in self.modules.values() if m.is_boundary)}")
        log.info(f"Identified hotspot modules: {sum(1 for m in self.modules.values() if m.is_hotspot)}")

    def _collect_api_endpoints(self) -> List[ApiEndpoint]:
        """Collect all API endpoints from chunks."""
        endpoints: List[ApiEndpoint] = []
        seen = set()

        for chunk in self.chunks:
            for endpoint in chunk.api_endpoints:
                key = (endpoint.url, endpoint.method)
                if key not in seen:
                    endpoints.append(endpoint)
                    seen.add(key)

        return endpoints

    def _collect_ui_routes(self) -> List[str]:
        """Collect all UI routes from chunks."""
        routes: Set[str] = set()

        for chunk in self.chunks:
            routes.update(chunk.ui_routes)

        return sorted(routes)

    def build(self) -> SystemModel:
        """
        Build the complete system model.

        Returns:
            SystemModel: The constructed system model
        """
        log.info(f"Building system model for project: {self.project_id}")

        # Step 1: Build modules
        self._build_modules()

        # Step 2: Build dependencies
        self._build_dependencies()

        # Step 3: Compute graph metrics
        self._compute_graph_metrics()

        # Step 4: Collect API endpoints and routes
        api_endpoints = self._collect_api_endpoints()
        ui_routes = self._collect_ui_routes()

        # Step 5: Compute statistics
        total_files = len(set(c.file_path for c in self.chunks))
        avg_module_complexity = (
            sum(m.avg_complexity for m in self.modules.values()) / len(self.modules) if self.modules else 0.0
        )

        # Identify special module lists
        central_modules = [m.name for m in self.modules.values() if m.is_central]
        boundary_modules = [m.name for m in self.modules.values() if m.is_boundary]
        hotspot_modules = [m.name for m in self.modules.values() if m.is_hotspot]

        # God modules: high out-degree (depend on many modules)
        god_threshold = len(self.modules) * 0.3 if self.modules else 0
        god_modules = [m.name for m in self.modules.values() if m.out_degree >= god_threshold]

        # Create SystemModel
        system_model = SystemModel(
            project_id=self.project_id,
            timestamp=datetime.utcnow().isoformat(),
            modules=self.modules,
            dependencies=list(self.dependency_map.values()),
            api_endpoints=api_endpoints,
            ui_routes=ui_routes,
            total_chunks=len(self.chunks),
            total_modules=len(self.modules),
            total_files=total_files,
            avg_module_complexity=avg_module_complexity,
            central_modules=central_modules,
            boundary_modules=boundary_modules,
            hotspot_modules=hotspot_modules,
            god_modules=god_modules,
        )

        log.info("System model built successfully")
        log.info(f"  Modules: {system_model.total_modules}")
        log.info(f"  Dependencies: {len(system_model.dependencies)}")
        log.info(f"  API Endpoints: {len(system_model.api_endpoints)}")
        log.info(f"  UI Routes: {len(system_model.ui_routes)}")

        return system_model


def build_system_model(chunks: List[Chunk], project_id: str) -> SystemModel:
    """
    Convenience function to build a system model from chunks.

    Args:
        chunks: List of code chunks
        project_id: Project identifier

    Returns:
        SystemModel: The constructed system model
    """
    builder = SystemModelBuilder(project_id)
    builder.add_chunks(chunks)
    return builder.build()
