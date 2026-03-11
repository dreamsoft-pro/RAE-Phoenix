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
Tests for ControllerToComponentRecipe.
"""
from datetime import datetime

import pytest

from feniks.core.models.types import Chunk, Module, ModuleType, SystemModel
from feniks.core.refactor.recipes.angularjs import ControllerToComponentRecipe


@pytest.fixture
def sample_controller():
    """Sample AngularJS controller code."""
    return """
angular.module('myApp')
  .controller('OrdersCtrl', ['$scope', '$http', 'OrderService', function($scope, $http, OrderService) {
    var vm = this;

    vm.orders = [];
    vm.selectedOrder = null;

    vm.loadOrders = function() {
      $http.get('/api/orders').then(function(response) {
        vm.orders = response.data;
      });
    };

    vm.selectOrder = function(order) {
      vm.selectedOrder = order;
    };

    $scope.$on('$destroy', function() {
      // Cleanup
    });

    vm.loadOrders();
  }]);
"""


@pytest.fixture
def system_model_with_controller(sample_controller):
    """Create a system model with a controller."""
    chunk = Chunk(
        id="chunk1",
        file_path="/src/controllers/orders.controller.js",
        text=sample_controller,
        chunk_name="OrdersCtrl",
        start_line=1,
        end_line=25,
        language="javascript",
    )

    module = Module(
        name="myApp",
        module_type=ModuleType.FRONTEND,
        file_paths=["/src/controllers/orders.controller.js"],
        chunks=[chunk],
        total_lines=25,
        total_complexity=5,
    )

    system_model = SystemModel(
        project_id="test-project", timestamp=datetime.now().isoformat(), modules={"myApp": module}, total_chunks=1
    )

    return system_model


def test_recipe_name():
    """Test recipe name."""
    recipe = ControllerToComponentRecipe()
    assert recipe.name == "angularjs.controller-to-next-component"


def test_recipe_description():
    """Test recipe description."""
    recipe = ControllerToComponentRecipe()
    assert "AngularJS controllers" in recipe.description
    assert "Next.js" in recipe.description


def test_analyze_finds_controller(system_model_with_controller):
    """Test that analyze finds AngularJS controllers."""
    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model_with_controller)

    assert plan is not None
    assert len(plan.metadata["controllers"]) == 1
    assert plan.metadata["controllers"][0]["name"] == "OrdersCtrl"


def test_analyze_extracts_dependencies(system_model_with_controller):
    """Test that analyze extracts DI dependencies."""
    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model_with_controller)

    controller = plan.metadata["controllers"][0]
    assert "$scope" in controller["dependencies"]
    assert "$http" in controller["dependencies"]
    assert "OrderService" in controller["dependencies"]


def test_execute_generates_component(system_model_with_controller):
    """Test that execute generates a component file."""
    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model_with_controller)

    # Get the chunk
    chunk = system_model_with_controller.modules["myApp"].chunks[0]

    result = recipe.execute(plan, [chunk], dry_run=True)

    assert result.success
    assert len(result.file_changes) == 2
    assert result.file_changes[0].file_path.endswith(".tsx")


def test_generated_component_has_react_imports(system_model_with_controller):
    """Test that generated component imports React."""
    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model_with_controller)
    chunk = system_model_with_controller.modules["myApp"].chunks[0]

    result = recipe.execute(plan, [chunk], dry_run=True)

    component_code = result.file_changes[0].modified_content
    assert "import React" in component_code
    assert "useState" in component_code or "useReducer" in component_code


def test_generated_component_has_props_interface(system_model_with_controller):
    """Test that generated component has TypeScript props interface."""
    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model_with_controller)
    chunk = system_model_with_controller.modules["myApp"].chunks[0]

    result = recipe.execute(plan, [chunk], dry_run=True)

    component_code = result.file_changes[0].modified_content
    assert "interface" in component_code
    assert "Props" in component_code


def test_generated_component_has_export(system_model_with_controller):
    """Test that generated component has default export."""
    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model_with_controller)
    chunk = system_model_with_controller.modules["myApp"].chunks[0]

    result = recipe.execute(plan, [chunk], dry_run=True)

    component_code = result.file_changes[0].modified_content
    assert "export default function" in component_code


def test_validate_checks_syntax(system_model_with_controller):
    """Test that validate checks TypeScript syntax."""
    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model_with_controller)
    chunk = system_model_with_controller.modules["myApp"].chunks[0]

    result = recipe.execute(plan, [chunk], dry_run=True)
    is_valid = recipe.validate(result)

    assert is_valid


def test_no_controllers_returns_none():
    """Test that analyze returns None when no controllers found."""
    # Empty system model
    system_model = SystemModel(
        project_id="test-project", timestamp=datetime.now().isoformat(), modules={}, total_chunks=0
    )

    recipe = ControllerToComponentRecipe()
    plan = recipe.analyze(system_model)

    assert plan is None


def test_config_target_dir():
    """Test that config can specify target directory."""
    config = {"target_dir": "app/custom"}
    recipe = ControllerToComponentRecipe(config)

    assert recipe.target_dir == "app/custom"


def test_config_state_strategy():
    """Test that config can specify state strategy."""
    config = {"state_strategy": "useReducer"}
    recipe = ControllerToComponentRecipe(config)

    assert recipe.state_strategy == "useReducer"
