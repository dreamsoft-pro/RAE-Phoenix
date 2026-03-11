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
Directive to Component Recipe - Migrates AngularJS directives to React components/hooks.

Handles:
- Element directives → React components
- Attribute directives → Custom hooks
- Isolated scope → Component props
- Transclusion → children prop
- Link function → useEffect + refs
- Compile function → Special handling with warnings
"""
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.angularjs.directive_to_component")


class DirectiveType(Enum):
    """Types of directives."""

    ELEMENT = "E"  # <my-directive>
    ATTRIBUTE = "A"  # <div my-directive>
    CLASS = "C"  # <div class="my-directive">
    COMMENT = "M"  # <!-- directive: my-directive -->


class DirectiveStrategy(Enum):
    """Migration strategies for directives."""

    COMPONENT = "component"  # Element/structural directive → Component
    HOOK = "hook"  # Behavior directive → Custom hook
    UTILITY = "utility"  # Simple logic → Utility function


@dataclass
class ScopeBinding:
    """Represents a scope binding in a directive."""

    name: str
    binding_type: str  # '=' (two-way), '@' (string), '&' (function), '<' (one-way)
    alias: Optional[str] = None


@dataclass
class DirectiveMetadata:
    """Metadata extracted from an AngularJS directive."""

    name: str
    restrict: str  # 'E', 'A', 'EA', etc.
    scope: Dict[str, Any]  # Scope definition
    scope_bindings: List[ScopeBinding]
    isolated_scope: bool
    template: Optional[str]
    template_url: Optional[str]
    transclude: bool
    has_controller: bool
    controller_as: Optional[str]
    has_link: bool
    has_compile: bool
    require: List[str]
    priority: int
    migration_strategy: DirectiveStrategy


class DirectiveToComponentRecipe(RefactorRecipe):
    """
    Recipe for migrating AngularJS directives to React components or hooks.

    Mapping strategy:
    - Element directive (restrict: 'E') → React component
    - Attribute directive with template → React component
    - Attribute directive (behavior only) → Custom hook
    - scope: { ... } → Props interface
    - '=' binding → Prop with onChange callback
    - '@' binding → String prop
    - '&' binding → Function prop
    - transclude → children prop
    - link function → useEffect with refs
    - compile → Warning (complex, manual review needed)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the recipe.

        Args:
            config: Optional configuration
        """
        super().__init__()
        self.config = config or {}
        self.target_dir_components = self.config.get("target_dir_components", "components/legacy")
        self.target_dir_hooks = self.config.get("target_dir_hooks", "hooks/legacy")

    @property
    def name(self) -> str:
        return "angularjs.directive-to-component-hook"

    @property
    def description(self) -> str:
        return "Migrate AngularJS directives to React components or custom hooks"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        """
        Analyze the system to find AngularJS directives.

        Args:
            system_model: The system model
            target: Optional dict with 'directive_name'

        Returns:
            RefactorPlan or None
        """
        log.info(f"Analyzing for AngularJS directives: {system_model.project_id}")

        # Find directives
        directives = self._find_directives(system_model, target)

        if not directives:
            log.info("No AngularJS directives found")
            return None

        # Extract metadata
        directive_metadata = []
        target_files = []

        for directive_chunk in directives:
            metadata = self._extract_directive_metadata(directive_chunk)
            if metadata:
                directive_metadata.append(metadata)
                target_files.append(directive_chunk.file_path)

        if not directive_metadata:
            log.info("No valid directive metadata extracted")
            return None

        # Assess risks
        risks = self._assess_risks(directive_metadata)
        risk_level = self._calculate_risk_level(directive_metadata)

        # Create refactoring plan
        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[m.name for m in directive_metadata],
            target_files=list(set(target_files)),
            rationale=f"Migrate {len(directive_metadata)} AngularJS directives to React components/hooks",
            risks=risks,
            risk_level=risk_level,
            estimated_changes=len(directive_metadata),
            validation_steps=[
                "Verify TypeScript compilation",
                "Check component/hook exports",
                "Validate props interfaces",
                "Test directive behavior",
                "Review migration strategy for each directive",
            ],
            metadata={
                "directives": [
                    {
                        "name": m.name,
                        "strategy": m.migration_strategy.value,
                        "restrict": m.restrict,
                        "has_template": m.template is not None or m.template_url is not None,
                        "transclude": m.transclude,
                    }
                    for m in directive_metadata
                ]
            },
        )

        log.info(f"Created refactoring plan for {len(directive_metadata)} directives")
        return plan

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        """
        Execute the directive migration.

        Args:
            plan: The refactoring plan
            chunks: Code chunks containing directives
            dry_run: If True, don't write files

        Returns:
            RefactorResult with generated components/hooks
        """
        log.info(f"Executing directive migration (dry_run={dry_run})")

        result = RefactorResult(plan=plan, success=True)

        try:
            for directive_data in plan.metadata["directives"]:
                # Find the corresponding chunk
                directive_chunk = self._find_chunk_by_name(chunks, directive_data["name"])
                if not directive_chunk:
                    result.warnings.append(f"Could not find chunk for directive: {directive_data['name']}")
                    continue

                # Extract full metadata
                metadata = self._extract_directive_metadata(directive_chunk)
                if not metadata:
                    result.warnings.append(f"Could not extract metadata for: {directive_data['name']}")
                    continue

                # Generate code based on strategy
                if metadata.migration_strategy == DirectiveStrategy.COMPONENT:
                    code = self._generate_component(metadata)
                    file_path = self._get_component_path(metadata)
                elif metadata.migration_strategy == DirectiveStrategy.HOOK:
                    code = self._generate_hook(metadata)
                    file_path = self._get_hook_path(metadata)
                else:
                    code = self._generate_utility(metadata)
                    file_path = self._get_utility_path(metadata)

                # Create file change
                file_change = FileChange(
                    file_path=file_path, original_content="", modified_content=code, change_type="create"
                )
                result.file_changes.append(file_change)

                log.info(f"Generated {metadata.migration_strategy.value}: {file_path}")

        except Exception as e:
            log.error(f"Error during execution: {e}", exc_info=True)
            result.success = False
            result.errors.append(str(e))

        return result

    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the migration result.

        Args:
            result: The refactoring result

        Returns:
            bool: True if validation passed
        """
        log.info("Validating directive migration")

        validation_results = {}

        # Check all files were generated
        validation_results["all_files_generated"] = len(result.file_changes) == len(result.plan.metadata["directives"])

        # Check TypeScript syntax
        for file_change in result.file_changes:
            syntax_valid = self._validate_syntax(file_change.modified_content)
            validation_results[f"syntax_{Path(file_change.file_path).name}"] = syntax_valid

        result.validation_results = validation_results

        return all(validation_results.values())

    # Helper methods

    def _find_directives(self, system_model: SystemModel, target: Optional[Dict[str, Any]]) -> List[Chunk]:
        """Find AngularJS directive definitions."""
        directives = []

        for module_name, module in system_model.modules.items():
            for chunk in module.chunks:
                if self._is_directive_chunk(chunk):
                    if target and "directive_name" in target:
                        if target["directive_name"] not in chunk.content:
                            continue
                    directives.append(chunk)

        return directives

    def _is_directive_chunk(self, chunk: Chunk) -> bool:
        """Check if chunk contains a directive definition."""
        patterns = [r'\.directive\s*\(\s*["\'](\w+)["\']', r"angular\.module\([^)]+\)\.directive"]

        for pattern in patterns:
            if re.search(pattern, chunk.content):
                return True

        return False

    def _extract_directive_metadata(self, chunk: Chunk) -> Optional[DirectiveMetadata]:
        """Extract metadata from a directive chunk."""
        try:
            # Extract directive name
            name_match = re.search(r'\.directive\s*\(\s*["\'](\w+)["\']', chunk.content)
            if not name_match:
                return None

            directive_name = name_match.group(1)

            # Extract restrict
            restrict_match = re.search(r'restrict\s*:\s*["\']([EACM]+)["\']', chunk.content)
            restrict = restrict_match.group(1) if restrict_match else "EA"

            # Extract scope
            scope_isolated = bool(re.search(r"scope\s*:\s*\{", chunk.content))
            scope_bindings = self._extract_scope_bindings(chunk.content) if scope_isolated else []

            # Extract template
            template_match = re.search(r'template\s*:\s*["\']([^"\']+)["\']', chunk.content)
            template = template_match.group(1) if template_match else None

            template_url_match = re.search(r'templateUrl\s*:\s*["\']([^"\']+)["\']', chunk.content)
            template_url = template_url_match.group(1) if template_url_match else None

            # Check transclude
            transclude = bool(re.search(r"transclude\s*:\s*true", chunk.content))

            # Check controller
            has_controller = bool(re.search(r"controller\s*:", chunk.content))
            controller_as_match = re.search(r'controllerAs\s*:\s*["\'](\w+)["\']', chunk.content)
            controller_as = controller_as_match.group(1) if controller_as_match else None

            # Check link and compile
            has_link = bool(re.search(r"link\s*:\s*function", chunk.content))
            has_compile = bool(re.search(r"compile\s*:\s*function", chunk.content))

            # Extract require
            require = self._extract_require(chunk.content)

            # Extract priority
            priority_match = re.search(r"priority\s*:\s*(\d+)", chunk.content)
            priority = int(priority_match.group(1)) if priority_match else 0

            # Determine migration strategy
            migration_strategy = self._determine_migration_strategy(
                restrict, template, template_url, has_link, has_compile
            )

            return DirectiveMetadata(
                name=directive_name,
                restrict=restrict,
                scope={},
                scope_bindings=scope_bindings,
                isolated_scope=scope_isolated,
                template=template,
                template_url=template_url,
                transclude=transclude,
                has_controller=has_controller,
                controller_as=controller_as,
                has_link=has_link,
                has_compile=has_compile,
                require=require,
                priority=priority,
                migration_strategy=migration_strategy,
            )

        except Exception as e:
            log.error(f"Error extracting directive metadata: {e}", exc_info=True)
            return None

    def _extract_scope_bindings(self, content: str) -> List[ScopeBinding]:
        """Extract scope bindings from directive."""
        bindings = []

        # Pattern: scope: { propName: '=', otherProp: '@alias' }
        scope_match = re.search(r"scope\s*:\s*\{([^}]+)\}", content)
        if not scope_match:
            return bindings

        scope_content = scope_match.group(1)

        # Extract individual bindings
        binding_pattern = r'(\w+)\s*:\s*["\']([=@&<]+)(\w*)["\']'
        for match in re.finditer(binding_pattern, scope_content):
            prop_name = match.group(1)
            binding_type = match.group(2)
            alias = match.group(3) if match.group(3) else None

            bindings.append(ScopeBinding(name=prop_name, binding_type=binding_type, alias=alias))

        return bindings

    def _extract_require(self, content: str) -> List[str]:
        """Extract required controllers."""
        require_match = re.search(r"require\s*:\s*\[([^\]]+)\]", content)
        if require_match:
            requires = [r.strip().strip("\"'") for r in require_match.group(1).split(",")]
            return requires

        require_match = re.search(r'require\s*:\s*["\']([^"\']+)["\']', content)
        if require_match:
            return [require_match.group(1)]

        return []

    def _determine_migration_strategy(
        self, restrict: str, template: Optional[str], template_url: Optional[str], has_link: bool, has_compile: bool
    ) -> DirectiveStrategy:
        """Determine the best migration strategy."""
        # If has template, it's a component
        if template or template_url:
            return DirectiveStrategy.COMPONENT

        # If element directive, likely a component
        if "E" in restrict:
            return DirectiveStrategy.COMPONENT

        # If only link (behavior), it's a hook
        if has_link and not (template or template_url):
            return DirectiveStrategy.HOOK

        # If compile, mark as high risk (needs manual review)
        if has_compile:
            return DirectiveStrategy.UTILITY

        # Default to component
        return DirectiveStrategy.COMPONENT

    def _assess_risks(self, directives: List[DirectiveMetadata]) -> List[str]:
        """Assess risks for the migration."""
        risks = []

        for directive in directives:
            if directive.has_compile:
                risks.append(f"Directive {directive.name} uses compile function (high risk)")

            if directive.require:
                risks.append(f"Directive {directive.name} requires: {', '.join(directive.require)}")

            if directive.priority > 0:
                risks.append(f"Directive {directive.name} has priority {directive.priority}")

            if "C" in directive.restrict or "M" in directive.restrict:
                risks.append(f"Directive {directive.name} uses class/comment restriction")

        risks.extend(
            [
                "Link functions need careful review for DOM manipulation",
                "Two-way bindings need state management strategy",
                "Transclusion maps to children but may need adjustments",
            ]
        )

        return risks

    def _calculate_risk_level(self, directives: List[DirectiveMetadata]) -> RefactorRisk:
        """Calculate overall risk level."""
        high_risk_count = sum(1 for d in directives if d.has_compile or len(d.require) > 1)

        if high_risk_count > len(directives) / 2:
            return RefactorRisk.HIGH
        elif high_risk_count > 0:
            return RefactorRisk.MEDIUM
        else:
            return RefactorRisk.LOW

    def _find_chunk_by_name(self, chunks: List[Chunk], name: str) -> Optional[Chunk]:
        """Find a chunk by directive name."""
        for chunk in chunks:
            if f"'{name}'" in chunk.content or f'"{name}"' in chunk.content:
                return chunk
        return None

    def _generate_component(self, metadata: DirectiveMetadata) -> str:
        """Generate React component from directive."""
        component_name = self._to_component_name(metadata.name)

        # Generate props interface
        props_interface = self._generate_props_from_scope(metadata, component_name)

        # Generate component body
        body = self._generate_component_body(metadata)

        # Generate JSX
        jsx = self._generate_jsx_from_directive(metadata)

        component = f"""// Generated by Feniks - AngularJS Directive to React Component
// Source directive: {metadata.name}
// Restrict: {metadata.restrict}
//
// TODO: Review and adjust the generated code
// TODO: Test directive behavior

import React, {{ useEffect, useRef }} from 'react';

{props_interface}

export function {component_name}(props: {component_name}Props) {{
{body}

  return (
{jsx}
  );
}}
"""

        return component

    def _generate_hook(self, metadata: DirectiveMetadata) -> str:
        """Generate custom hook from directive."""
        hook_name = self._to_hook_name(metadata.name)

        hook = f"""// Generated by Feniks - AngularJS Directive to Custom Hook
// Source directive: {metadata.name}
// Restrict: {metadata.restrict}
//
// TODO: Review and adjust the generated code

import {{ useEffect, useRef }} from 'react';

interface {hook_name.capitalize()}Options {{
  // TODO: Add options based on directive attributes
}}

export function {hook_name}(
  ref: React.RefObject<HTMLElement>,
  options: {hook_name.capitalize()}Options = {{}}
) {{
  useEffect(() => {{
    if (!ref.current) return;

    const element = ref.current;

    // TODO: Implement directive behavior from link function
    // Original directive: {metadata.name}

    return () => {{
      // Cleanup
    }};
  }}, [ref, options]);
}}
"""

        return hook

    def _generate_utility(self, metadata: DirectiveMetadata) -> str:
        """Generate utility function from directive."""
        function_name = self._to_function_name(metadata.name)

        utility = f"""// Generated by Feniks - AngularJS Directive to Utility
// Source directive: {metadata.name}
//
// WARNING: This directive requires manual review
// Reason: Complex compile function or unusual pattern

export function {function_name}() {{
  // TODO: Implement directive logic
  // Original directive: {metadata.name}
  console.warn('Utility function {function_name} not yet implemented');
}}
"""

        return utility

    def _to_component_name(self, directive_name: str) -> str:
        """Convert directive name to component name (PascalCase)."""
        # Convert camelCase or kebab-case to PascalCase
        parts = re.split(r"[-_]", directive_name)
        return "".join(word.capitalize() for word in parts)

    def _to_hook_name(self, directive_name: str) -> str:
        """Convert directive name to hook name (useCamelCase)."""
        component_name = self._to_component_name(directive_name)
        return f"use{component_name}"

    def _to_function_name(self, directive_name: str) -> str:
        """Convert directive name to function name (camelCase)."""
        component_name = self._to_component_name(directive_name)
        return component_name[0].lower() + component_name[1:]

    def _generate_props_from_scope(self, metadata: DirectiveMetadata, component_name: str) -> str:
        """Generate props interface from scope bindings."""
        props = []

        # Add children if transclude
        if metadata.transclude:
            props.append("  children?: React.ReactNode;")

        # Add props from scope bindings
        for binding in metadata.scope_bindings:
            type_annotation = self._binding_type_to_ts(binding.binding_type)
            props.append(f"  {binding.name}: {type_annotation};")

        if not props:
            props.append("  // TODO: Add props")

        props_str = "\n".join(props)

        return f"""interface {component_name}Props {{
{props_str}
}}"""

    def _binding_type_to_ts(self, binding_type: str) -> str:
        """Convert AngularJS binding type to TypeScript type."""
        if binding_type == "=":
            return "any  // Two-way binding - consider using value + onChange"
        elif binding_type == "@":
            return "string"
        elif binding_type == "&":
            return "() => void"
        elif binding_type == "<":
            return "any  // One-way binding"
        else:
            return "any"

    def _generate_component_body(self, metadata: DirectiveMetadata) -> str:
        """Generate component body with hooks."""
        body_parts = []

        # Add ref if has link function
        if metadata.has_link:
            body_parts.append("  const elementRef = useRef<HTMLDivElement>(null);")

        # Add effect for link logic
        if metadata.has_link:
            body_parts.append(
                """
  useEffect(() => {
    // TODO: Implement link function logic
    // Original directive had link function
  }, []);"""
            )

        if not body_parts:
            body_parts.append("  // No special logic needed")

        return "\n".join(body_parts)

    def _generate_jsx_from_directive(self, metadata: DirectiveMetadata) -> str:
        """Generate JSX placeholder."""
        if metadata.template:
            return f"""    <div>
      {{/* TODO: Convert template to JSX */}}
      {{/* Original template: {metadata.template[:50]}... */}}
    </div>"""
        elif metadata.transclude:
            return "    <div>{props.children}</div>"
        else:
            return """    <div>
      {/* TODO: Add JSX based on directive behavior */}
    </div>"""

    def _get_component_path(self, metadata: DirectiveMetadata) -> str:
        """Get target path for component."""
        component_name = self._to_component_name(metadata.name)
        return f"{self.target_dir_components}/{component_name}.tsx"

    def _get_hook_path(self, metadata: DirectiveMetadata) -> str:
        """Get target path for hook."""
        hook_name = self._to_hook_name(metadata.name)
        return f"{self.target_dir_hooks}/{hook_name}.ts"

    def _get_utility_path(self, metadata: DirectiveMetadata) -> str:
        """Get target path for utility."""
        function_name = self._to_function_name(metadata.name)
        return f"utils/legacy/{function_name}.ts"

    def _validate_syntax(self, content: str) -> bool:
        """Basic syntax validation."""
        if content.count("{") != content.count("}"):
            return False
        if content.count("(") != content.count(")"):
            return False

        # Check for export
        if "export" not in content:
            return False

        return True
