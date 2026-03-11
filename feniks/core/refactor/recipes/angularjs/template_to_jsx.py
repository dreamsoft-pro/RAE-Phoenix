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
Template to JSX Recipe - Converts AngularJS HTML templates to React JSX/TSX.

Handles:
- {{ interpolation }} → {expression}
- ng-repeat → map()
- ng-if/ng-show/ng-hide → conditional rendering
- ng-click/ng-submit → onClick/onSubmit
- ng-model → controlled components
- ng-class/ng-style → className/style
- ng-bind → text interpolation
- Filters → utility functions
"""
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.angularjs.template_to_jsx")


@dataclass
class TemplateMetadata:
    """Metadata extracted from an AngularJS template."""

    file_path: str
    raw_html: str
    interpolations: List[str]
    directives: Dict[str, List[str]]  # directive_name -> occurrences
    filters: List[str]
    controller_ref: Optional[str]  # vm, $ctrl, $scope
    complexity_score: int


class AngularHTMLParser(HTMLParser):
    """Custom HTML parser for AngularJS templates."""

    def __init__(self):
        super().__init__()
        self.jsx_output = []
        self.indent_level = 0
        self.directives_found = {}
        self.filters_found = []
        self.controller_ref = None

    def handle_starttag(self, tag, attrs):
        """Handle opening tag."""
        indent = "  " * self.indent_level

        # Convert tag attributes
        jsx_attrs = []
        ng_directives = {}

        for attr_name, attr_value in attrs:
            # Collect AngularJS directives
            if attr_name.startswith("ng-"):
                ng_directives[attr_name] = attr_value
                if attr_name not in self.directives_found:
                    self.directives_found[attr_name] = []
                self.directives_found[attr_name].append(attr_value)
            else:
                # Regular HTML attribute
                jsx_attr_name = self._convert_attr_name(attr_name)
                jsx_attrs.append(f'{jsx_attr_name}="{attr_value}"')

        # Process AngularJS directives
        jsx_attrs.extend(self._process_ng_directives(ng_directives))

        # Build tag
        attrs_str = " ".join(jsx_attrs)
        if attrs_str:
            self.jsx_output.append(f"{indent}<{tag} {attrs_str}>")
        else:
            self.jsx_output.append(f"{indent}<{tag}>")

        self.indent_level += 1

    def handle_endtag(self, tag):
        """Handle closing tag."""
        self.indent_level -= 1
        indent = "  " * self.indent_level
        self.jsx_output.append(f"{indent}</{tag}>")

    def handle_data(self, data):
        """Handle text content."""
        # Skip whitespace-only data
        if not data.strip():
            return

        indent = "  " * self.indent_level

        # Convert Angular interpolations {{ }} to JSX { }
        converted = self._convert_interpolation(data)

        if converted != data.strip():
            # Has interpolation
            self.jsx_output.append(f"{indent}{converted}")
        else:
            # Plain text
            self.jsx_output.append(f"{indent}{data.strip()}")

    def _convert_attr_name(self, attr_name: str) -> str:
        """Convert HTML attribute name to JSX."""
        # Common conversions
        conversions = {
            "class": "className",
            "for": "htmlFor",
            "readonly": "readOnly",
            "maxlength": "maxLength",
            "tabindex": "tabIndex",
        }
        return conversions.get(attr_name, attr_name)

    def _process_ng_directives(self, directives: Dict[str, str]) -> List[str]:
        """Process AngularJS directives to JSX."""
        jsx_attrs = []

        for directive, value in directives.items():
            if directive == "ng-click":
                # ng-click="vm.save()" → onClick={() => vm.save()}
                jsx_attrs.append(f"onClick={{() => {value}}}")

            elif directive == "ng-submit":
                # ng-submit="vm.submit()" → onSubmit={(e) => { e.preventDefault(); vm.submit(); }}
                jsx_attrs.append(f"onSubmit={{(e) => {{ e.preventDefault(); {value}; }}}}")

            elif directive == "ng-change":
                jsx_attrs.append(f"onChange={{() => {value}}}")

            elif directive == "ng-if":
                # ng-if handled at element level (conditional rendering)
                jsx_attrs.append(f'{{/* TODO: ng-if="{value}" - use conditional rendering */}}')

            elif directive == "ng-show":
                # ng-show="expr" → style={{ display: expr ? 'block' : 'none' }}
                jsx_attrs.append(f'style={{{{ display: {value} ? "block" : "none" }}}}')

            elif directive == "ng-hide":
                jsx_attrs.append(f'style={{{{ display: {value} ? "none" : "block" }}}}')

            elif directive == "ng-class":
                # ng-class="{ active: vm.isActive }" → className={vm.isActive ? 'active' : ''}
                jsx_attrs.append(f'{{/* TODO: ng-class="{value}" - convert to className logic */}}')

            elif directive == "ng-model":
                # ng-model="vm.name" → value={vm.name} onChange={(e) => handleModelChange('vm.name', e.target.value)}
                jsx_attrs.append(f"value={{{value}}}")
                jsx_attrs.append(f"onChange={{(e) => handleModelChange('{value}', e.target.value)}}")

            elif directive == "ng-disabled":
                jsx_attrs.append(f"disabled={{{value}}}")

            elif directive == "ng-checked":
                jsx_attrs.append(f"checked={{{value}}}")

            elif directive == "ng-href":
                jsx_attrs.append(f"href={{{value}}}")

            elif directive == "ng-src":
                jsx_attrs.append(f"src={{{value}}}")

            elif directive == "ng-bind":
                # ng-bind="vm.text" → {vm.text}
                jsx_attrs.append(f'{{/* TODO: ng-bind="{value}" - use interpolation */}}')

            else:
                # Unknown directive - leave as comment
                jsx_attrs.append(f'{{/* TODO: {directive}="{value}" */}}')

        return jsx_attrs

    def _convert_interpolation(self, text: str) -> str:
        """Convert {{ expression }} to {expression}."""
        # Find all {{ }} patterns
        pattern = r"\{\{\s*(.+?)\s*\}\}"

        def replace_interpolation(match):
            expr = match.group(1)

            # Check for filters: {{ value | filterName:arg }}
            if "|" in expr:
                self._extract_filters(expr)
                # Convert filter to function call
                return "{" + self._convert_filter(expr) + "}"
            else:
                return "{" + expr + "}"

        converted = re.sub(pattern, replace_interpolation, text)
        return converted

    def _extract_filters(self, expr: str):
        """Extract filter names from expression."""
        # {{ value | filterName:arg1:arg2 }}
        parts = expr.split("|")
        if len(parts) > 1:
            for filter_part in parts[1:]:
                filter_name = filter_part.split(":")[0].strip()
                if filter_name not in self.filters_found:
                    self.filters_found.append(filter_name)

    def _convert_filter(self, expr: str) -> str:
        """Convert filter expression to function call."""
        # {{ amount | currency:'PLN' }} → formatCurrency(amount, 'PLN')
        parts = expr.split("|")
        value = parts[0].strip()

        if len(parts) == 1:
            return value

        filter_expr = parts[1].strip()
        filter_parts = filter_expr.split(":")
        filter_name = filter_parts[0].strip()
        filter_args = [value] + [arg.strip() for arg in filter_parts[1:]]

        # Map common filters
        filter_mapping = {
            "currency": "formatCurrency",
            "date": "formatDate",
            "number": "formatNumber",
            "lowercase": "toLowerCase",
            "uppercase": "toUpperCase",
            "json": "JSON.stringify",
        }

        function_name = filter_mapping.get(filter_name, f"apply{filter_name.capitalize()}")
        args_str = ", ".join(filter_args)

        return f"{function_name}({args_str})"

    def get_jsx(self) -> str:
        """Get the generated JSX."""
        return "\n".join(self.jsx_output)


class TemplateToJsxRecipe(RefactorRecipe):
    """
    Recipe for converting AngularJS HTML templates to JSX/TSX.

    Mapping rules:
    - {{ expr }} → {expr}
    - ng-repeat="item in items" → {items.map(item => <li key={...}>)}
    - ng-if="condition" → {condition && <Element />}
    - ng-show/ng-hide → style display or conditional rendering
    - ng-click → onClick
    - ng-model → value + onChange
    - ng-class → className with logic
    - Filters → utility functions
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the recipe.

        Args:
            config: Optional configuration
        """
        super().__init__()
        self.config = config or {}
        self.preserve_comments = self.config.get("preserve_comments", True)
        self.generate_filter_stubs = self.config.get("generate_filter_stubs", True)

    @property
    def name(self) -> str:
        return "angularjs.template-to-jsx"

    @property
    def description(self) -> str:
        return "Convert AngularJS HTML templates to React JSX/TSX"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        """
        Analyze the system to find AngularJS templates.

        Args:
            system_model: The system model
            target: Optional dict with 'template_path'

        Returns:
            RefactorPlan or None
        """
        log.info(f"Analyzing for AngularJS templates: {system_model.project_id}")

        # Find HTML templates
        templates = self._find_templates(system_model, target)

        if not templates:
            log.info("No AngularJS templates found")
            return None

        # Extract metadata
        template_metadata = []
        target_files = []

        for template_chunk in templates:
            metadata = self._extract_template_metadata(template_chunk)
            if metadata:
                template_metadata.append(metadata)
                target_files.append(template_chunk.file_path)

        if not template_metadata:
            log.info("No valid template metadata extracted")
            return None

        # Assess risks
        risks = self._assess_risks(template_metadata)
        risk_level = self._calculate_risk_level(template_metadata)

        # Collect all filters
        all_filters = set()
        for metadata in template_metadata:
            all_filters.update(metadata.filters)

        # Create refactoring plan
        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[],
            target_files=list(set(target_files)),
            rationale=f"Convert {len(template_metadata)} AngularJS templates to JSX",
            risks=risks,
            risk_level=risk_level,
            estimated_changes=len(template_metadata),
            validation_steps=[
                "Verify JSX syntax is valid",
                "Check all directives are converted",
                "Validate filter functions exist",
                "Test component rendering",
                "Review ng-repeat conversions",
            ],
            metadata={
                "templates": [
                    {
                        "path": m.file_path,
                        "complexity": m.complexity_score,
                        "directives": list(m.directives.keys()),
                        "filters": m.filters,
                    }
                    for m in template_metadata
                ],
                "all_filters": list(all_filters),
            },
        )

        log.info(f"Created refactoring plan for {len(template_metadata)} templates")
        return plan

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        """
        Execute the template conversion.

        Args:
            plan: The refactoring plan
            chunks: Code chunks containing templates
            dry_run: If True, don't write files

        Returns:
            RefactorResult with converted JSX
        """
        log.info(f"Executing template conversion (dry_run={dry_run})")

        result = RefactorResult(plan=plan, success=True)

        try:
            # Convert each template
            for template_data in plan.metadata["templates"]:
                # Find the corresponding chunk
                template_chunk = self._find_chunk_by_path(chunks, template_data["path"])
                if not template_chunk:
                    result.warnings.append(f"Could not find chunk for template: {template_data['path']}")
                    continue

                # Convert to JSX
                jsx_code = self._convert_template_to_jsx(template_chunk.text, template_data)

                # Determine output path
                output_path = self._get_jsx_path(template_chunk.file_path)

                # Create file change
                file_change = FileChange(
                    file_path=output_path,
                    original_content=template_chunk.text,
                    modified_content=jsx_code,
                    change_type="create",
                )
                result.file_changes.append(file_change)

                log.info(f"Converted template: {output_path}")

            # Generate filter stubs if needed
            if self.generate_filter_stubs and plan.metadata["all_filters"]:
                filter_code = self._generate_filter_stubs(plan.metadata["all_filters"])
                filter_path = "legacy/filters/index.ts"

                filter_change = FileChange(
                    file_path=filter_path, original_content="", modified_content=filter_code, change_type="create"
                )
                result.file_changes.append(filter_change)

                log.info(f"Generated filter stubs: {filter_path}")

        except Exception as e:
            log.error(f"Error during execution: {e}", exc_info=True)
            result.success = False
            result.errors.append(str(e))

        return result

    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the conversion result.

        Args:
            result: The refactoring result

        Returns:
            bool: True if validation passed
        """
        log.info("Validating template conversion")

        validation_results = {}

        # Check JSX syntax
        for file_change in result.file_changes:
            if file_change.file_path.endswith(".tsx") or file_change.file_path.endswith(".jsx"):
                syntax_valid = self._validate_jsx_syntax(file_change.modified_content)
                validation_results[f"syntax_{file_change.file_path}"] = syntax_valid

        result.validation_results = validation_results

        return all(validation_results.values())

    # Helper methods

    def _find_templates(self, system_model: SystemModel, target: Optional[Dict[str, Any]]) -> List[Chunk]:
        """Find HTML template files."""
        templates = []

        for module_name, module in system_model.modules.items():
            for chunk in module.chunks:
                # Check if it's an HTML file
                if chunk.file_path.endswith(".html"):
                    if target and "template_path" in target:
                        if chunk.file_path != target["template_path"]:
                            continue
                    templates.append(chunk)

        return templates

    def _extract_template_metadata(self, chunk: Chunk) -> Optional[TemplateMetadata]:
        """Extract metadata from a template."""
        try:
            # Find interpolations
            interpolations = re.findall(r"\{\{(.+?)\}\}", chunk.text)

            # Find directives
            directives = {}
            for directive in [
                "ng-repeat",
                "ng-if",
                "ng-show",
                "ng-hide",
                "ng-click",
                "ng-model",
                "ng-class",
                "ng-style",
                "ng-bind",
            ]:
                matches = re.findall(rf'{directive}="([^"]*)"', chunk.text)
                if matches:
                    directives[directive] = matches

            # Find filters
            filters = []
            for interpolation in interpolations:
                if "|" in interpolation:
                    filter_matches = re.findall(r"\|\s*(\w+)", interpolation)
                    filters.extend(filter_matches)

            # Detect controller reference (vm, $ctrl, $scope)
            controller_ref = None
            if "vm." in chunk.text:
                controller_ref = "vm"
            elif "$ctrl." in chunk.text:
                controller_ref = "$ctrl"
            elif "$scope." in chunk.text:
                controller_ref = "$scope"

            # Calculate complexity
            complexity_score = len(interpolations) + len(directives) * 2 + len(filters) * 3

            return TemplateMetadata(
                file_path=chunk.file_path,
                raw_html=chunk.text,
                interpolations=interpolations,
                directives=directives,
                filters=list(set(filters)),
                controller_ref=controller_ref,
                complexity_score=complexity_score,
            )

        except Exception as e:
            log.error(f"Error extracting template metadata: {e}", exc_info=True)
            return None

    def _assess_risks(self, templates: List[TemplateMetadata]) -> List[str]:
        """Assess risks for the conversion."""
        risks = []

        for template in templates:
            if template.complexity_score > 50:
                risks.append(f"Template {template.file_path} is highly complex (score: {template.complexity_score})")

            if "ng-repeat" in template.directives:
                risks.append(f"Template {template.file_path} uses ng-repeat (requires key handling)")

            if len(template.filters) > 3:
                risks.append(f"Template {template.file_path} uses many filters: {', '.join(template.filters)}")

        risks.extend(
            [
                "ng-model requires manual state management setup",
                "Custom filters need implementation",
                "Complex ng-class expressions may need refactoring",
            ]
        )

        return risks

    def _calculate_risk_level(self, templates: List[TemplateMetadata]) -> RefactorRisk:
        """Calculate overall risk level."""
        avg_complexity = sum(t.complexity_score for t in templates) / len(templates)

        if avg_complexity > 50:
            return RefactorRisk.HIGH
        elif avg_complexity > 25:
            return RefactorRisk.MEDIUM
        else:
            return RefactorRisk.LOW

    def _find_chunk_by_path(self, chunks: List[Chunk], path: str) -> Optional[Chunk]:
        """Find a chunk by file path."""
        for chunk in chunks:
            if chunk.file_path == path:
                return chunk
        return None

    def _convert_template_to_jsx(self, html: str, template_data: Dict[str, Any]) -> str:
        """Convert HTML template to JSX."""
        # Pre-process ng-repeat (convert to map syntax)
        # html = self._preprocess_ng_repeat(html)

        # Pre-process ng-if (convert to conditional rendering)
        # html = self._preprocess_ng_if(html)

        # Parse and convert
        parser = AngularHTMLParser()
        try:
            parser.feed(html)
            jsx = parser.get_jsx()
        except Exception as e:
            log.warning(f"HTML parsing failed, using fallback conversion: {e}")
            jsx = self._fallback_conversion(html)

        # Wrap in fragment if needed
        if jsx.count("<") > 1:
            jsx = f"<>\n{jsx}\n</>"

        return jsx

    def _preprocess_ng_repeat(self, html: str) -> str:
        """Pre-process ng-repeat directives."""
        # Pattern: <li ng-repeat="item in items">...</li>
        # Convert to: {items.map(item => <li key={...}>...</li>)}

        def replace_repeat(match):
            full_tag = match.group(0)
            ng_repeat_value = match.group(2)

            # Parse ng-repeat: "item in items track by item.id"
            repeat_parts = ng_repeat_value.split(" in ")
            if len(repeat_parts) != 2:
                return full_tag  # Can't parse, leave as is

            item_var = repeat_parts[0].strip()
            items_expr = repeat_parts[1].split(" track by ")[0].strip()
            track_by = None

            if " track by " in repeat_parts[1]:
                track_by = repeat_parts[1].split(" track by ")[1].strip()

            # Generate key
            key_expr = track_by if track_by else "index"

            # Build map syntax
            map_start = f"{{{items_expr}.map(({item_var}, index) => ("

            # Replace the opening tag
            new_tag = full_tag.replace(f'ng-repeat="{ng_repeat_value}"', f"key={{{key_expr}}}")

            return f"{map_start}\n{new_tag}"

        # This is a simplified version - full implementation would need proper HTML parsing
        pattern = r'<(\w+)[^>]*ng-repeat="([^"]+)"[^>]*>'
        converted = re.sub(pattern, replace_repeat, html)

        return converted

    def _preprocess_ng_if(self, html: str) -> str:
        """Pre-process ng-if directives."""
        # Pattern: <div ng-if="condition">...</div>
        # Convert to: {condition && <div>...</div>}

        # This is a simplified version
        pattern = r'<(\w+)([^>]*)ng-if="([^"]+)"([^>]*)>'

        def replace_if(match):
            tag_name = match.group(1)
            before_attrs = match.group(2)
            condition = match.group(3)
            after_attrs = match.group(4)

            return f"{{{condition} && <{tag_name}{before_attrs}{after_attrs}>"

        converted = re.sub(pattern, replace_if, html)

        return converted

    def _fallback_conversion(self, html: str) -> str:
        """Fallback conversion using regex."""
        converted = html

        # Convert interpolations
        converted = re.sub(r"\{\{\s*(.+?)\s*\}\}", r"{\1}", converted)

        # Convert class to className
        converted = re.sub(r"\bclass=", "className=", converted)

        # Convert common attributes
        converted = re.sub(r"\bfor=", "htmlFor=", converted)

        return converted

    def _get_jsx_path(self, html_path: str) -> str:
        """Get the output path for JSX file."""
        # Replace .html with .tsx
        return html_path.replace(".html", ".tsx")

    def _generate_filter_stubs(self, filters: List[str]) -> str:
        """Generate stub functions for filters."""
        stubs = []

        for filter_name in sorted(filters):
            # Common filters
            if filter_name == "currency":
                stubs.append(
                    """export function formatCurrency(value: number, currency: string = 'USD'): string {
  // TODO: Implement currency formatting
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value);
}"""
                )
            elif filter_name == "date":
                stubs.append(
                    """export function formatDate(value: Date | string, format: string = 'yyyy-MM-dd'): string {
  // TODO: Implement date formatting (consider date-fns or dayjs)
  return new Date(value).toISOString().split('T')[0];
}"""
                )
            elif filter_name == "number":
                stubs.append(
                    """export function formatNumber(value: number, decimals: number = 2): string {
  return value.toFixed(decimals);
}"""
                )
            else:
                # Custom filter
                function_name = f"apply{filter_name.capitalize()}"
                stubs.append(
                    f"""export function {function_name}(value: any, ...args: any[]): any {{
  // TODO: Implement custom filter '{filter_name}'
  console.warn('Filter {filter_name} not yet implemented');
  return value;
}}"""
                )

        header = """// Generated by Feniks - AngularJS Filters
// TODO: Review and implement filter functions

"""

        return header + "\n\n".join(stubs)

    def _validate_jsx_syntax(self, content: str) -> bool:
        """Basic JSX syntax validation."""
        # Check balanced brackets
        if content.count("{") != content.count("}"):
            return False
        if content.count("<") != content.count(">"):
            return False

        return True
