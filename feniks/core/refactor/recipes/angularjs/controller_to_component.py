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
Controller to Component Recipe - Migrates AngularJS controllers to Next.js components.

Handles:
- Controller functions → Functional React components
- $scope → useState/useReducer
- DI services → Import statements
- Lifecycle hooks → useEffect
- Navigation → next/navigation hooks
"""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.angularjs.controller_to_component")


@dataclass
class ControllerMetadata:
    """Metadata extracted from an AngularJS controller."""

    name: str
    module_name: str
    dependencies: List[str]
    properties: Dict[str, Any]
    methods: Dict[str, str]
    controller_as: Optional[str]
    template_path: Optional[str]
    uses_scope: bool
    lifecycle_hooks: List[str]


class ControllerToComponentRecipe(RefactorRecipe):
    """
    Recipe for migrating AngularJS controllers to Next.js functional components.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.target_dir = self.config.get("target_dir", "app/_legacy")
        self.service_dir = self.config.get("service_dir", "services/legacy")
        self.state_strategy = self.config.get("state_strategy", "useState")
        self.typing_mode = self.config.get("typing_mode", "strict")
        self.aggressiveness = self.config.get("aggressiveness", "balanced")

    @property
    def name(self) -> str:
        return "angularjs.controller-to-next-component"

    @property
    def description(self) -> str:
        return "Migrate AngularJS controllers to Next.js functional components with TypeScript"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        log.info(f"Analyzing for AngularJS controllers: {system_model.project_id}")
        controllers = self._find_controllers(system_model, target)

        if not controllers:
            return None

        controller_metadata = []
        target_files = []

        for controller_chunk in controllers:
            metadata = self._extract_controller_metadata(controller_chunk)
            if metadata:
                controller_metadata.append(metadata)
                target_files.append(controller_chunk.file_path)

        if not controller_metadata:
            return None

        risks = self._assess_risks(controller_metadata)
        risk_level = self._calculate_risk_level(controller_metadata)

        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[m.name for m in controller_metadata],
            target_files=list(set(target_files)),
            rationale=f"Migrate {len(controller_metadata)} AngularJS controllers to Next.js components",
            risks=risks,
            risk_level=risk_level,
            estimated_changes=len(controller_metadata) * 3,  # Component + Service stubs
            validation_steps=[
                "Verify TypeScript compilation",
                "Check all imports are resolved",
                "Validate component props interfaces",
            ],
            metadata={
                "controllers": [
                    {
                        "name": m.name,
                        "module": m.module_name,
                        "dependencies": m.dependencies,
                        "template": m.template_path,
                    }
                    for m in controller_metadata
                ],
                "target_directory": self.target_dir,
                "service_directory": self.service_dir,
            },
        )
        return plan

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        log.info(f"Executing controller migration (dry_run={dry_run})")
        result = RefactorResult(plan=plan, success=True)

        try:
            generated_services = set()

            for controller_data in plan.metadata["controllers"]:
                chunk = self._find_chunk_by_name(chunks, controller_data["name"])
                if not chunk:
                    continue

                metadata = self._extract_controller_metadata(chunk)
                if not metadata:
                    continue

                # 1. Generate Component
                component_code = self._generate_component(metadata, plan)
                component_path = self._get_component_path(metadata)
                result.file_changes.append(
                    FileChange(
                        file_path=component_path,
                        original_content="",
                        modified_content=component_code,
                        change_type="create",
                    )
                )
                log.info(f"Generated component: {component_path}")

                # 2. Generate Service Stubs
                for dep in metadata.dependencies:
                    if (
                        dep
                        not in [
                            "$scope",
                            "$http",
                            "$timeout",
                            "$interval",
                            "$q",
                            "$state",
                            "$stateParams",
                            "$location",
                            "$rootScope",
                        ]
                        and dep not in generated_services
                    ):
                        service_code = self._generate_service_stub(dep)
                        service_name = dep.replace("$", "").capitalize()
                        service_path = f"{self.service_dir}/{service_name}.ts"

                        result.file_changes.append(
                            FileChange(
                                file_path=service_path,
                                original_content="",
                                modified_content=service_code,
                                change_type="create",
                            )
                        )
                        generated_services.add(dep)
                        log.info(f"Generated service stub: {service_path}")

        except Exception as e:
            log.error(f"Error during execution: {e}", exc_info=True)
            result.success = False
            result.errors.append(str(e))

        return result

    def validate(self, result: RefactorResult) -> bool:
        return True

    # Helper methods

    def _find_controllers(self, system_model: SystemModel, target: Optional[Dict[str, Any]]) -> List[Chunk]:
        controllers = []
        for module_name, module in system_model.modules.items():
            if target and "module_name" in target and module_name != target["module_name"]:
                continue
            for chunk in module.chunks:
                if self._is_controller_chunk(chunk):
                    if target and "controller_name" in target and target["controller_name"] not in chunk.content:
                        continue
                    controllers.append(chunk)
        return controllers

    def _is_controller_chunk(self, chunk: Chunk) -> bool:
        patterns = [
            r'\.controller\s*\(\s*["\'](\w+)["\']',
            r"angular\.module\([^)]+\)\.controller",
        ]
        for pattern in patterns:
            if re.search(pattern, chunk.text):
                return True
        return False

    def _extract_controller_metadata(self, chunk: Chunk) -> Optional[ControllerMetadata]:
        try:
            name_match = re.search(r'\.controller\s*\(\s*["\'](\w+)["\']', chunk.text)
            if not name_match:
                return None
            controller_name = name_match.group(1)

            module_match = re.search(r'angular\.module\s*\(\s*["\']([^"\\]+)["\\]', chunk.text)
            module_name = module_match.group(1) if module_match else "unknown"

            dependencies = self._extract_dependencies(chunk.text)
            properties, methods = self._extract_properties_and_methods(chunk.text)

            match = re.search(r'controllerAs\s*:\s*["\'](\w+)["\\]', chunk.text)
            controller_as = match.group(1) if match else None

            uses_scope = "$scope" in dependencies

            hooks = []
            if "$scope.$on('$destroy'" in chunk.text:
                hooks.append("$destroy")
            if "$scope.$on('$init'" in chunk.text:
                hooks.append("$init")

            template_path = None
            match = re.search(r'templateUrl\s*:\s*["\']([^"\\]+)["\\]', chunk.text)
            if match:
                template_path = match.group(1)

            return ControllerMetadata(
                name=controller_name,
                module_name=module_name,
                dependencies=dependencies,
                properties=properties,
                methods=methods,
                controller_as=controller_as,
                template_path=template_path,
                uses_scope=uses_scope,
                lifecycle_hooks=hooks,
            )
        except Exception:
            return None

    def _extract_dependencies(self, content: str) -> List[str]:
        array_match = re.search(r"\[([^\]]+)\s*,\s*function", content)
        if array_match:
            deps_str = array_match.group(1)
            return [d.strip().strip("\"'") for d in deps_str.split(",")]
        else:
            func_match = re.search(r"function\s*\(([^)]*)\)", content)
            if func_match:
                params = func_match.group(1)
                return [p.strip() for p in params.split(",") if p.strip()]
        return []

    def _extract_properties_and_methods(self, content: str) -> tuple:
        properties = {}
        methods = {}
        prop_pattern = r"(?:this|(?:\$scope))\.(\w+)\s*=\s*([^;]+);"
        for match in re.finditer(prop_pattern, content):
            prop_name = match.group(1)
            prop_value = match.group(2).strip()
            if prop_value.startswith("function"):
                methods[prop_name] = prop_value
            else:
                properties[prop_name] = prop_value
        return properties, methods

    def _assess_risks(self, controllers: List[ControllerMetadata]) -> List[str]:
        return []

    def _calculate_risk_level(self, controllers: List[ControllerMetadata]) -> RefactorRisk:
        return RefactorRisk.LOW

    def _find_chunk_by_name(self, chunks: List[Chunk], name: str) -> Optional[Chunk]:
        for chunk in chunks:
            if f"'{name}'" in chunk.text or f'"{name}"' in chunk.text:
                return chunk
        return None

    def _generate_component(self, metadata: ControllerMetadata, plan: RefactorPlan) -> str:
        component_name = self._to_component_name(metadata.name)
        imports = self._generate_imports(metadata)
        props = self._generate_props_interface(metadata, component_name)
        state = self._generate_state_declarations(metadata)
        methods = self._generate_methods(metadata)
        effects = self._generate_effects(metadata)
        jsx = self._generate_jsx_placeholder(metadata)

        return f"""// Generated by Feniks
{imports}

{props}

export default function {component_name}(props: {component_name}Props) {{
{state}

{methods}

{effects}

  return (
{jsx}
  );
}}
"""

    def _to_component_name(self, controller_name: str) -> str:
        name = re.sub(r"(Ctrl|Controller)$", "", controller_name)
        if not name.endswith("Page"):
            name += "Page"
        return name

    def _generate_imports(self, metadata: ControllerMetadata) -> str:
        imports = ['import React, { useState, useEffect } from "react";']
        if any(dep in ["$state", "$stateParams", "$location"] for dep in metadata.dependencies):
            imports.append('import { useRouter } from "next/navigation";')

        for dep in metadata.dependencies:
            if dep not in [
                "$scope",
                "$http",
                "$timeout",
                "$interval",
                "$q",
                "$state",
                "$stateParams",
                "$location",
                "$rootScope",
            ]:
                service_name = dep.replace("$", "").capitalize()
                imports.append(f'import {{ {service_name} }} from "@/services/legacy/{service_name}";')
        return "\n".join(imports)

    def _generate_props_interface(self, metadata: ControllerMetadata, component_name: str) -> str:
        return f"interface {component_name}Props {{ [key: string]: any; }}"

    def _generate_state_declarations(self, metadata: ControllerMetadata) -> str:
        decls = []
        for prop, val in metadata.properties.items():
            type_hint = self._infer_type(val)
            decls.append(f"  const [{prop}, set{prop.capitalize()}] = useState<{type_hint}>({val});")
        return "\n".join(decls)

    def _infer_type(self, value: str) -> str:
        if value in ["true", "false"]:
            return "boolean"
        if value.isdigit():
            return "number"
        return "any"

    def _generate_methods(self, metadata: ControllerMetadata) -> str:
        methods = []
        for name, body in metadata.methods.items():
            converted = self._convert_http_to_fetch(body)
            converted = converted.replace("$scope.", "").replace("this.", "")

            method_code = "  const " + name + " = async () => {\n"
            method_code += "    try {\n"
            method_code += "      " + converted + "\n"
            method_code += "    } catch (err) { console.error(err); }\n"
            method_code += "  };"

            methods.append(method_code)
        return "\n\n".join(methods)

    def _convert_http_to_fetch(self, body: str) -> str:
        body = re.sub(r"^function\s*\([^)]*\)\s*\{\{", "", body)
        body = re.sub(r"\}\}$", "", body)
        # Simple $http.get conversion
        body = re.sub(r"\$http\.get\s*\(([^)]+)\)", r"await fetch(\1).then(r => r.json())", body)
        return body.strip()

    def _generate_effects(self, metadata: ControllerMetadata) -> str:
        return "  useEffect(() => {}, []);"

    def _generate_jsx_placeholder(self, metadata: ControllerMetadata) -> str:
        return "    <div>{metadata.name}</div>"

    def _get_component_path(self, metadata: ControllerMetadata) -> str:
        name = self._to_component_name(metadata.name)
        return f"{self.target_dir}/{name}.tsx"

    def _generate_service_stub(self, service_name: str) -> str:
        """Generate a service stub file."""
        clean_name = service_name.replace("$", "").capitalize()
        return f"""// Generated by Feniks - Service Stub
// Original Service: {service_name}

export class {clean_name} {{
  // TODO: Implement methods found in original service
  constructor() {{}}

  async getData() {{
    return Promise.resolve({{}});
  }}
}}
"""
