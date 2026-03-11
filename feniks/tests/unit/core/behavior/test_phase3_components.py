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
Tests for Phase 3 - Enterprise Ready Components.

Tests:
- Scenario Library (publish, search, import)
- Storage abstraction and factory
- Storage backend implementations (file, mock)
"""
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from feniks.adapters.storage.base import create_storage_backend
from feniks.adapters.storage.behavior_store import BehaviorStore
from feniks.core.behavior.scenario_library import ScenarioLibrary
from feniks.core.models.behavior import (
    BehaviorContract,
    BehaviorScenario,
    BehaviorSnapshot,
    CLICommand,
    ScenarioInput,
    SuccessCriteria,
)

# ============================================================================
# Scenario Library Tests
# ============================================================================


class TestScenarioLibrary:
    """Tests for ScenarioLibrary."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = BehaviorStore(storage_dir=tmpdir)
            yield storage

    @pytest.fixture
    def library(self, temp_storage):
        """Create scenario library."""
        return ScenarioLibrary(storage=temp_storage)

    @pytest.fixture
    def sample_scenario(self):
        """Create sample scenario."""
        return BehaviorScenario(
            id="test-scenario-1",
            project_id="test-project",
            name="Test Scenario",
            category="api",
            description="Test scenario description",
            environment="legacy",
            input=ScenarioInput(api_request={"method": "GET", "url": "/api/test"}),
            success_criteria=SuccessCriteria(),
            created_at=datetime.now(),
        )

    def test_publish_scenario(self, library, sample_scenario):
        """Test publishing scenario to library."""
        library_id = library.publish_scenario(
            scenario=sample_scenario, tags=["http", "test"], description="Public test scenario", author="Test Author"
        )

        assert library_id.startswith("lib-")

        # Verify published
        published = library.storage.load_scenario(library_id)
        assert published is not None
        assert published.project_id == "shared_library"
        assert published.metadata["tags"] == ["http", "test"]
        assert published.metadata["author"] == "Test Author"
        assert published.metadata["usage_count"] == 0

    def test_list_public_scenarios(self, library, sample_scenario):
        """Test listing public scenarios."""
        # Publish multiple scenarios
        library.publish_scenario(sample_scenario, tags=["http"])

        scenario2 = BehaviorScenario(
            id="test-scenario-2",
            project_id="test-project",
            name="CLI Scenario",
            category="cli",
            description="CLI test",
            environment="legacy",
            input=ScenarioInput(cli_command=CLICommand(command="echo test")),
            success_criteria=SuccessCriteria(),
            created_at=datetime.now(),
        )
        library.publish_scenario(scenario2, tags=["cli"])

        # List all
        all_scenarios = library.list_public_scenarios()
        assert len(all_scenarios) == 2

        # Filter by category
        api_scenarios = library.list_public_scenarios(category="api")
        assert len(api_scenarios) == 1
        assert api_scenarios[0].category == "api"

        # Filter by tags
        http_scenarios = library.list_public_scenarios(tags=["http"])
        assert len(http_scenarios) == 1

    def test_import_scenario(self, library, sample_scenario):
        """Test importing scenario from library."""
        # Publish scenario
        library_id = library.publish_scenario(sample_scenario, tags=["http"])

        # Import to another project
        imported = library.import_scenario(
            library_scenario_id=library_id,
            target_project_id="target-project",
            customize={"name": "Imported Test Scenario"},
        )

        assert imported.project_id == "target-project"
        assert imported.name == "Imported Test Scenario"
        assert imported.metadata["imported_from"] == library_id

        # Verify usage count incremented
        library_scenario = library.storage.load_scenario(library_id)
        assert library_scenario.metadata["usage_count"] == 1

    def test_get_popular_scenarios(self, library, sample_scenario):
        """Test getting popular scenarios."""
        # Publish scenarios
        sample_scenario_2 = BehaviorScenario(
            id="test-scenario-2",
            project_id="test-project",
            name="Test Scenario 2",
            category="cli",
            description="Test scenario 2 description",
            environment="legacy",
            input=ScenarioInput(cli_command=CLICommand(command="echo test")),
            success_criteria=SuccessCriteria(),
            created_at=datetime.now(),
        )

        lib_id1 = library.publish_scenario(sample_scenario, tags=["http"])
        lib_id2 = library.publish_scenario(sample_scenario_2, tags=["cli"])

        # Import multiple times to increase usage
        library.import_scenario(lib_id1, "project1")
        library.import_scenario(lib_id1, "project2")
        library.import_scenario(lib_id1, "project3")
        library.import_scenario(lib_id2, "project4")

        # Get popular
        popular = library.get_popular_scenarios(limit=2)
        assert len(popular) == 2
        # First should be lib_id1 with usage_count=3
        assert popular[0].metadata["usage_count"] >= popular[1].metadata["usage_count"]

    def test_get_scenario_stats(self, library, sample_scenario):
        """Test getting scenario statistics."""
        library_id = library.publish_scenario(sample_scenario, tags=["http", "test"], author="Test Author")

        stats = library.get_scenario_stats(library_id)

        assert stats["scenario_id"] == library_id
        assert stats["category"] == "api"
        assert "http" in stats["tags"]
        assert stats["author"] == "Test Author"
        assert stats["usage_count"] == 0

    def test_export_library_to_yaml(self, library, sample_scenario):
        """Test exporting library catalog to YAML."""
        # Publish scenarios
        library.publish_scenario(sample_scenario, tags=["http"], author="Author 1")

        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "catalog.yml"
            library.export_library_to_yaml(output_path)

            assert output_path.exists()

            # Read and verify
            import yaml

            with output_path.open("r") as f:
                catalog = yaml.safe_load(f)

            assert catalog["total_scenarios"] == 1
            assert len(catalog["scenarios"]) == 1
            assert catalog["scenarios"][0]["category"] == "api"


# ============================================================================
# Storage Abstraction Tests
# ============================================================================


class TestStorageAbstraction:
    """Tests for storage abstraction and factory."""

    def test_register_and_create_backend(self):
        """Test backend registration and factory."""
        # File backend should already be registered
        backend = create_storage_backend("file", storage_dir="data/test")
        assert isinstance(backend, BehaviorStore)

    def test_create_unknown_backend(self):
        """Test creating unknown backend raises error."""
        with pytest.raises(ValueError, match="Unknown storage backend"):
            create_storage_backend("unknown_backend")

    def test_file_backend_crud_operations(self):
        """Test file backend CRUD operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = create_storage_backend("file", storage_dir=tmpdir)

            # Create scenario
            scenario = BehaviorScenario(
                id="test-1",
                project_id="test",
                name="Test",
                category="api",
                description="Test desc",
                environment="legacy",
                input=ScenarioInput(),
                success_criteria=SuccessCriteria(),
                created_at=datetime.now(),
            )

            # Save
            backend.save_scenario(scenario)

            # Load
            loaded = backend.load_scenario("test-1")
            assert loaded is not None
            assert loaded.id == "test-1"

            # List
            scenarios = backend.list_scenarios(project_id="test")
            assert len(scenarios) == 1

            # Delete
            deleted = backend.delete_scenario("test-1")
            assert deleted is True

            # Verify deleted
            assert backend.load_scenario("test-1") is None

    def test_snapshot_storage_with_limit(self):
        """Test snapshot storage with limit parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = create_storage_backend("file", storage_dir=tmpdir)

            # Create scenario
            scenario = BehaviorScenario(
                id="scenario-1",
                project_id="test",
                name="Test",
                category="api",
                description="Test desc",
                environment="legacy",
                input=ScenarioInput(),
                success_criteria=SuccessCriteria(),
                created_at=datetime.now(),
            )
            backend.save_scenario(scenario)

            # Create multiple snapshots
            for i in range(5):
                snapshot = BehaviorSnapshot(
                    id=f"snap-{i}",
                    scenario_id="scenario-1",
                    project_id="test",
                    environment="candidate",
                    success=True,
                    created_at=datetime.now(),
                )
                backend.save_snapshot(snapshot)

            # Load with limit
            snapshots = backend.load_snapshots("scenario-1", limit=3)
            assert len(snapshots) == 3

            # Load all
            all_snapshots = backend.load_snapshots("scenario-1")
            assert len(all_snapshots) == 5

    def test_contract_version_filtering(self):
        """Test contract loading with version filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = create_storage_backend("file", storage_dir=tmpdir)

            # Create scenario
            scenario = BehaviorScenario(
                id="scenario-1",
                project_id="test",
                name="Test",
                category="api",
                description="Test desc",
                environment="legacy",
                input=ScenarioInput(),
                success_criteria=SuccessCriteria(),
                created_at=datetime.now(),
            )
            backend.save_scenario(scenario)

            # Create multiple contract versions
            for version in ["1.0.0", "1.1.0", "2.0.0"]:
                contract = BehaviorContract(
                    id=f"contract-1-{version}",
                    version=version,
                    scenario_id="scenario-1",
                    project_id="test",
                    success_criteria=SuccessCriteria(),
                    created_at=datetime.now(),
                )
                backend.save_contract(contract)

            # Load all versions
            all_contracts = backend.load_contracts_for_scenario("scenario-1")
            assert len(all_contracts) == 3

            # Load specific version
            v1_contracts = backend.load_contracts_for_scenario("scenario-1", version="1.0.0")
            assert len(v1_contracts) == 1
            assert v1_contracts[0].version == "1.0.0"


# ============================================================================
# Integration Tests
# ============================================================================


class TestPhase3Integration:
    """Integration tests for Phase 3 components."""

    def test_library_with_storage_backend_switching(self):
        """Test scenario library works with different storage backends."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file backend
            file_storage = create_storage_backend("file", storage_dir=tmpdir)

            # Create library
            library = ScenarioLibrary(storage=file_storage)

            # Publish scenario
            scenario = BehaviorScenario(
                id="test-1",
                project_id="test",
                name="Test",
                category="api",
                description="Test desc",
                environment="legacy",
                input=ScenarioInput(),
                success_criteria=SuccessCriteria(),
                created_at=datetime.now(),
            )

            library.publish_scenario(scenario, tags=["test"])

            # Verify published
            published = library.list_public_scenarios()
            assert len(published) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
