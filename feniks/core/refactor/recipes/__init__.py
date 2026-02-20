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
Built-in refactoring recipes.
"""
# AngularJS migration recipes
from feniks.core.refactor.recipes.angularjs import (
    ControllerToComponentRecipe,
    DirectiveToComponentRecipe,
    RoutingToAppRouterRecipe,
    ScopeToHooksRecipe,
    TemplateToJsxRecipe,
)
from feniks.core.refactor.recipes.extract_function import ExtractFunctionRecipe
from feniks.core.refactor.recipes.reduce_complexity import ReduceComplexityRecipe

__all__ = [
    "ReduceComplexityRecipe",
    "ExtractFunctionRecipe",
    # AngularJS migration recipes
    "ControllerToComponentRecipe",
    "DirectiveToComponentRecipe",
    "TemplateToJsxRecipe",
    "RoutingToAppRouterRecipe",
    "ScopeToHooksRecipe",
]
