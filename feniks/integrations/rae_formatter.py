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
RAE Formatter - Converts Feniks data structures to RAE memory format.
Handles formatting of meta-reflections, system models, and capabilities for RAE storage.
"""
from typing import Any, Dict, List

from feniks.core.models.types import MetaReflection, SystemModel
from feniks.infra.logging import get_logger

log = get_logger("integrations.rae_formatter")


class RAEFormatter:
    """
    Formatter for converting Feniks data to RAE memory format.

    RAE Memory Types:
    - meta_reflection: Reflective/meta-reflective memory about code quality
    - semantic: Semantic memory about system structure and capabilities
    """

    @staticmethod
    def format_meta_reflection(reflection: MetaReflection) -> Dict[str, Any]:
        """
        Format a MetaReflection for RAE storage.

        Args:
            reflection: MetaReflection instance

        Returns:
            Dict formatted for RAE /memory/meta-reflection endpoint
        """
        # Map reflection scope to RAE domain
        domain_mapping = {
            "codebase": "codebase",
            "module": "module",
            "system": "architecture",
            "pattern": "architecture",
            "technical_debt": "technical_debt",
        }

        domain = domain_mapping.get(reflection.scope.value, "codebase")

        payload = {
            "memory_type": "meta_reflection",
            "domain": domain,
            "project_id": reflection.project_id,
            "timestamp": reflection.timestamp,
            "id": reflection.id,
            "level": reflection.level.value,
            "level_name": reflection.level.name,
            "scope": reflection.scope.value,
            "impact": reflection.impact.value,
            "title": reflection.title,
            "content": reflection.content,
            "evidence": [
                {"type": e.type, "source": e.source, "value": e.value, "context": e.context}
                for e in reflection.evidence
            ],
            "related_modules": reflection.related_modules,
            "related_files": reflection.related_files,
            "recommendations": reflection.recommendations,
            "tags": reflection.tags,
            "confidence": reflection.confidence,
            "origin": reflection.origin,
            "metadata": reflection.metadata,
        }

        return payload

    @staticmethod
    def format_meta_reflections_batch(reflections: List[MetaReflection]) -> Dict[str, Any]:
        """
        Format multiple meta-reflections for batch storage.

        Args:
            reflections: List of MetaReflection instances

        Returns:
            Dict formatted for RAE batch endpoint
        """
        return {
            "memory_type": "meta_reflection",
            "batch": True,
            "count": len(reflections),
            "reflections": [RAEFormatter.format_meta_reflection(r) for r in reflections],
        }

    @staticmethod
    def format_system_capabilities(system_model: SystemModel) -> Dict[str, Any]:
        """
        Format system capabilities as semantic memory for RAE.

        Args:
            system_model: SystemModel instance

        Returns:
            Dict formatted for RAE /memory/semantic endpoint
        """
        # Build semantic statements about capabilities
        semantic_statements = []

        for capability in system_model.capabilities:
            statement = {
                "type": "capability",
                "name": capability.name,
                "description": capability.description,
                "capability_type": capability.capability_type,
                "confidence": capability.confidence,
                "modules": capability.modules,
                "business_domain": capability.business_domain,
                "complexity_score": capability.complexity_score,
                "patterns": capability.patterns,
            }
            semantic_statements.append(statement)

        payload = {
            "memory_type": "semantic",
            "domain": "system_capabilities",
            "project_id": system_model.project_id,
            "timestamp": system_model.timestamp,
            "capabilities": semantic_statements,
            "metadata": {
                "total_capabilities": len(system_model.capabilities),
                "capability_types": list(set(c.capability_type for c in system_model.capabilities)),
            },
        }

        return payload

    @staticmethod
    def format_system_model(system_model: SystemModel) -> Dict[str, Any]:
        """
        Format complete system model as semantic memory for RAE.

        Args:
            system_model: SystemModel instance

        Returns:
            Dict formatted for RAE /memory/semantic/system-model endpoint
        """
        # Convert modules to semantic format
        modules_data = []
        for module_name, module in system_model.modules.items():
            module_data = {
                "name": module.name,
                "type": module.module_type.value,
                "file_paths": module.file_paths,
                "total_lines": module.total_lines,
                "avg_complexity": module.avg_complexity,
                "chunk_count": module.chunk_count,
                "dependencies_in": module.dependencies_in,
                "dependencies_out": module.dependencies_out,
                "in_degree": module.in_degree,
                "out_degree": module.out_degree,
                "centrality": module.centrality,
                "is_central": module.is_central,
                "is_boundary": module.is_boundary,
                "is_hotspot": module.is_hotspot,
                "business_tags": list(module.business_tags),
                "capabilities": list(module.capabilities),
            }
            modules_data.append(module_data)

        # Convert dependencies to semantic format
        dependencies_data = []
        for dep in system_model.dependencies:
            dep_data = {"source": dep.source, "target": dep.target, "type": dep.dependency_type, "count": dep.count}
            dependencies_data.append(dep_data)

        # Build payload
        payload = {
            "memory_type": "semantic",
            "domain": "system_model",
            "project_id": system_model.project_id,
            "timestamp": system_model.timestamp,
            "system_model": {
                "modules": modules_data,
                "dependencies": dependencies_data,
                "api_endpoints": [
                    {"url": ep.url, "method": ep.method, "dataKeys": ep.dataKeys, "paramKeys": ep.paramKeys}
                    for ep in system_model.api_endpoints
                ],
                "ui_routes": system_model.ui_routes,
                "statistics": {
                    "total_modules": system_model.total_modules,
                    "total_files": system_model.total_files,
                    "total_chunks": system_model.total_chunks,
                    "avg_module_complexity": system_model.avg_module_complexity,
                    "total_dependencies": len(system_model.dependencies),
                    "total_api_endpoints": len(system_model.api_endpoints),
                    "total_ui_routes": len(system_model.ui_routes),
                },
                "analysis": {
                    "central_modules": system_model.central_modules,
                    "boundary_modules": system_model.boundary_modules,
                    "hotspot_modules": system_model.hotspot_modules,
                    "god_modules": system_model.god_modules,
                },
            },
            "metadata": system_model.metadata,
        }

        return payload

    @staticmethod
    def format_self_model_summary(system_model: SystemModel) -> Dict[str, Any]:
        """
        Format a high-level self-model summary for RAE /system/describe_self endpoint.

        Args:
            system_model: SystemModel instance

        Returns:
            Dict formatted for self-model description
        """
        # Build capability summary
        capability_summary = []
        for cap in system_model.capabilities[:10]:  # Top 10 capabilities
            capability_summary.append(
                {
                    "name": cap.name,
                    "description": cap.description,
                    "type": cap.capability_type,
                    "confidence": cap.confidence,
                }
            )

        # Build architecture summary
        architecture_summary = {
            "modularity": {
                "total_modules": system_model.total_modules,
                "central_modules": len(system_model.central_modules),
                "boundary_modules": len(system_model.boundary_modules),
                "hotspot_modules": len(system_model.hotspot_modules),
            },
            "complexity": {
                "avg_complexity": system_model.avg_module_complexity,
                "high_complexity_modules": [
                    m.name
                    for m in system_model.modules.values()
                    if m.avg_complexity > system_model.avg_module_complexity * 1.5
                ][:5],
            },
            "connectivity": {
                "total_dependencies": len(system_model.dependencies),
                "god_modules": system_model.god_modules,
                "highly_connected": [m.name for m in system_model.modules.values() if m.out_degree > 10][:5],
            },
        }

        # Build technology summary
        technology_summary = {
            "api_endpoints": len(system_model.api_endpoints),
            "ui_routes": len(system_model.ui_routes),
            "files": system_model.total_files,
        }

        payload = {
            "project_id": system_model.project_id,
            "timestamp": system_model.timestamp,
            "self_model": {
                "capabilities": capability_summary,
                "architecture": architecture_summary,
                "technology": technology_summary,
                "summary": RAEFormatter._generate_text_summary(system_model),
            },
        }

        return payload

    @staticmethod
    def _generate_text_summary(system_model: SystemModel) -> str:
        """
        Generate a natural language summary of the system.

        Args:
            system_model: SystemModel instance

        Returns:
            str: Natural language summary
        """
        parts = []

        # Capabilities
        if system_model.capabilities:
            cap_names = [c.name for c in system_model.capabilities[:3]]
            parts.append(
                f"The system implements {len(system_model.capabilities)} capabilities including {', '.join(cap_names)}."
            )

        # Architecture
        parts.append(
            f"The architecture consists of {system_model.total_modules} modules with {len(system_model.dependencies)} dependencies."
        )

        # Complexity
        if system_model.hotspot_modules:
            parts.append(f"There are {len(system_model.hotspot_modules)} hotspot modules requiring attention.")

        # God modules
        if system_model.god_modules:
            parts.append(f"The system has {len(system_model.god_modules)} god modules with high dependency counts.")

        # API
        if system_model.api_endpoints:
            parts.append(f"It exposes {len(system_model.api_endpoints)} API endpoints.")

        return " ".join(parts)
