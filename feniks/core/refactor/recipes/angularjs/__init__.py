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
AngularJS migration recipes for Feniks.

This package contains recipes for migrating AngularJS 1.x applications to Next.js.
"""
from feniks.core.refactor.recipes.angularjs.behavior_guard_integration import BehaviorGuardIntegration
from feniks.core.refactor.recipes.angularjs.controller_to_component import ControllerToComponentRecipe
from feniks.core.refactor.recipes.angularjs.directive_to_component import DirectiveToComponentRecipe
from feniks.core.refactor.recipes.angularjs.routing_to_app_router import RoutingToAppRouterRecipe
from feniks.core.refactor.recipes.angularjs.scope_to_hooks import ScopeToHooksRecipe
from feniks.core.refactor.recipes.angularjs.template_to_jsx import TemplateToJsxRecipe

__all__ = [
    "ControllerToComponentRecipe",
    "DirectiveToComponentRecipe",
    "TemplateToJsxRecipe",
    "RoutingToAppRouterRecipe",
    "ScopeToHooksRecipe",
    "BehaviorGuardIntegration",
]
