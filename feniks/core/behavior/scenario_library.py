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
Shared Scenario Library - Public scenario repository for reusability.

Provides centralized management of reusable behavior scenarios:
- Scenario templates
- Best practices library
- Community contributions
- Cross-project sharing
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from feniks.adapters.storage.base import BehaviorStorageBackend
from feniks.core.models.behavior import BehaviorScenario
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("core.behavior.scenario_library")


class ScenarioLibrary:
    """
    Shared scenario library manager.

    Features:
    - Publish scenarios to shared library
    - Browse and search public scenarios
    - Import scenarios into projects
    - Version tracking
    - Tagging and categorization
    - Usage statistics
    """

    def __init__(self, storage: BehaviorStorageBackend, library_project_id: str = "shared_library"):
        """
        Initialize scenario library.

        Args:
            storage: Storage backend (file/postgres/qdrant)
            library_project_id: Project ID for shared scenarios
        """
        self.storage = storage
        self.library_project_id = library_project_id
        log.info(f"ScenarioLibrary initialized (project={library_project_id})")

    def publish_scenario(
        self,
        scenario: BehaviorScenario,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
    ) -> str:
        """
        Publish scenario to shared library.

        Args:
            scenario: Scenario to publish
            tags: Optional tags for categorization
            description: Optional public description
            author: Optional author name

        Returns:
            Published scenario ID
        """
        # Create library version with metadata
        library_scenario = BehaviorScenario(
            id=f"lib-{scenario.id}",
            project_id=self.library_project_id,
            name=scenario.name,
            category=scenario.category,
            description=description or scenario.description,
            environment=scenario.environment,
            input=scenario.input,
            success_criteria=scenario.success_criteria,
            metadata={
                "original_project": scenario.project_id,
                "original_id": scenario.id,
                "tags": tags or [],
                "author": author,
                "published_at": datetime.now().isoformat(),
                "usage_count": 0,
            },
            created_at=datetime.now(),
        )

        self.storage.save_scenario(library_scenario)
        log.info(f"Published scenario to library: {library_scenario.id}")
        return library_scenario.id

    def list_public_scenarios(
        self, category: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 50
    ) -> List[BehaviorScenario]:
        """
        List public scenarios from library.

        Args:
            category: Optional category filter
            tags: Optional tag filters
            limit: Maximum number of results

        Returns:
            List of public scenarios
        """
        all_scenarios = self.storage.list_scenarios(project_id=self.library_project_id)

        # Apply filters
        filtered = []
        for scenario in all_scenarios:
            # Category filter
            if category and scenario.category != category:
                continue

            # Tag filter
            if tags:
                scenario_tags = scenario.metadata.get("tags", [])
                if not any(tag in scenario_tags for tag in tags):
                    continue

            filtered.append(scenario)

            if len(filtered) >= limit:
                break

        log.info(f"Listed {len(filtered)} public scenarios (category={category}, tags={tags})")
        return filtered

    def search_scenarios(self, query: str, limit: int = 10) -> List[BehaviorScenario]:
        """
        Search public scenarios (requires Qdrant backend).

        Args:
            query: Natural language search query
            limit: Maximum number of results

        Returns:
            List of matching scenarios
        """
        # Check if semantic search is available
        if hasattr(self.storage, "search_similar_scenarios"):
            scenarios = self.storage.search_similar_scenarios(
                query=query, limit=limit, project_id=self.library_project_id
            )
            log.info(f"Semantic search found {len(scenarios)} scenarios for: {query}")
            return scenarios
        else:
            # Fallback to simple text matching
            all_scenarios = self.list_public_scenarios(limit=limit)
            query_lower = query.lower()

            matches = []
            for scenario in all_scenarios:
                # Simple text search
                searchable = f"{scenario.name} {scenario.description} {scenario.category}".lower()
                if query_lower in searchable:
                    matches.append(scenario)

            log.info(f"Text search found {len(matches)} scenarios for: {query}")
            return matches[:limit]

    def import_scenario(
        self, library_scenario_id: str, target_project_id: str, customize: Optional[Dict] = None
    ) -> BehaviorScenario:
        """
        Import scenario from library into project.

        Args:
            library_scenario_id: ID of scenario in library
            target_project_id: Target project ID
            customize: Optional customizations (name, description, etc.)

        Returns:
            Imported scenario
        """
        # Load library scenario
        library_scenario = self.storage.load_scenario(library_scenario_id)
        if not library_scenario:
            raise FeniksError(f"Library scenario not found: {library_scenario_id}")

        # Create project scenario
        imported_scenario = BehaviorScenario(
            id=f"imported-{library_scenario.id}-{target_project_id}",
            project_id=target_project_id,
            name=customize.get("name") if customize else library_scenario.name,
            category=library_scenario.category,
            description=(customize.get("description") if customize else None) or library_scenario.description,
            environment=library_scenario.environment,
            input=library_scenario.input,
            success_criteria=library_scenario.success_criteria,
            metadata={
                "imported_from": library_scenario_id,
                "imported_at": datetime.now().isoformat(),
                "original_author": library_scenario.metadata.get("author"),
            },
            created_at=datetime.now(),
        )

        self.storage.save_scenario(imported_scenario)

        # Increment usage count
        self._increment_usage_count(library_scenario_id)

        log.info(f"Imported scenario {library_scenario_id} to project {target_project_id}")
        return imported_scenario

    def _increment_usage_count(self, scenario_id: str):
        """Increment usage count for a library scenario."""
        scenario = self.storage.load_scenario(scenario_id)
        if scenario:
            current_count = scenario.metadata.get("usage_count", 0)
            scenario.metadata["usage_count"] = current_count + 1
            self.storage.save_scenario(scenario)

    def export_library_to_yaml(self, output_path: Path) -> None:
        """
        Export library scenarios to YAML catalog.

        Args:
            output_path: Path to output YAML file
        """
        scenarios = self.list_public_scenarios(limit=1000)

        catalog = {
            "library_version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "total_scenarios": len(scenarios),
            "scenarios": [],
        }

        for scenario in scenarios:
            catalog["scenarios"].append(
                {
                    "id": scenario.id,
                    "name": scenario.name,
                    "category": scenario.category,
                    "description": scenario.description,
                    "tags": scenario.metadata.get("tags", []),
                    "author": scenario.metadata.get("author"),
                    "usage_count": scenario.metadata.get("usage_count", 0),
                    "published_at": scenario.metadata.get("published_at"),
                }
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            yaml.dump(catalog, f, default_flow_style=False, sort_keys=False)

        log.info(f"Exported library catalog to {output_path}")

    def get_popular_scenarios(self, limit: int = 10) -> List[BehaviorScenario]:
        """
        Get most popular scenarios by usage count.

        Args:
            limit: Maximum number of results

        Returns:
            List of popular scenarios
        """
        all_scenarios = self.list_public_scenarios(limit=1000)

        # Sort by usage count
        sorted_scenarios = sorted(all_scenarios, key=lambda s: s.metadata.get("usage_count", 0), reverse=True)

        popular = sorted_scenarios[:limit]
        log.info(f"Retrieved {len(popular)} popular scenarios")
        return popular

    def get_scenario_stats(self, scenario_id: str) -> Dict:
        """
        Get statistics for a library scenario.

        Args:
            scenario_id: Library scenario ID

        Returns:
            Dict with statistics
        """
        scenario = self.storage.load_scenario(scenario_id)
        if not scenario:
            raise FeniksError(f"Library scenario not found: {scenario_id}")

        stats = {
            "scenario_id": scenario.id,
            "name": scenario.name,
            "category": scenario.category,
            "tags": scenario.metadata.get("tags", []),
            "author": scenario.metadata.get("author"),
            "published_at": scenario.metadata.get("published_at"),
            "usage_count": scenario.metadata.get("usage_count", 0),
            "has_contracts": len(self.storage.load_contracts_for_scenario(scenario.id, None)) > 0,
        }

        return stats


# ============================================================================
# Default Library Templates
# ============================================================================

DEFAULT_TEMPLATES = {
    "http_health_check": {
        "name": "HTTP Health Check",
        "category": "api",
        "description": "Standard health check endpoint validation",
        "tags": ["http", "health", "monitoring"],
    },
    "login_form": {
        "name": "Login Form Validation",
        "category": "ui",
        "description": "Standard login form behavior",
        "tags": ["ui", "authentication", "form"],
    },
    "data_export": {
        "name": "Data Export Command",
        "category": "cli",
        "description": "Standard data export CLI scenario",
        "tags": ["cli", "export", "data"],
    },
}


def create_scenario_library(storage: BehaviorStorageBackend) -> ScenarioLibrary:
    """
    Create scenario library instance.

    Args:
        storage: Storage backend

    Returns:
        ScenarioLibrary instance
    """
    return ScenarioLibrary(storage=storage)
