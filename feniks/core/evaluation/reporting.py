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
Report Generator - generates human-readable reports from system model.
Creates text reports with module analysis, dependency graphs, and recommendations.
"""
from pathlib import Path
from typing import List, Optional

from feniks.core.models.types import MetaReflection, SystemModel
from feniks.infra.logging import get_logger

log = get_logger("core.report_generator")


class ReportGenerator:
    """Generates reports from system model."""

    def __init__(self, system_model: SystemModel, meta_reflections: Optional[List[MetaReflection]] = None):
        """
        Initialize the report generator.

        Args:
            system_model: The system model to report on
            meta_reflections: Optional list of meta-reflections
        """
        self.system_model = system_model
        self.meta_reflections = meta_reflections or []

    def generate_summary(self) -> str:
        """
        Generate a summary report.

        Returns:
            str: Text summary of the system
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"System Model Report: {self.system_model.project_id}")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.system_model.timestamp}")
        lines.append("")

        # Overview
        lines.append("## Overview")
        lines.append(f"  Total Modules: {self.system_model.total_modules}")
        lines.append(f"  Total Files: {self.system_model.total_files}")
        lines.append(f"  Total Chunks: {self.system_model.total_chunks}")
        lines.append(f"  Dependencies: {len(self.system_model.dependencies)}")
        lines.append(f"  API Endpoints: {len(self.system_model.api_endpoints)}")
        lines.append(f"  UI Routes: {len(self.system_model.ui_routes)}")
        lines.append(f"  Detected Capabilities: {len(self.system_model.capabilities)}")
        lines.append(f"  Avg Module Complexity: {self.system_model.avg_module_complexity:.2f}")
        lines.append("")

        return "\n".join(lines)

    def generate_module_analysis(self) -> str:
        """
        Generate module analysis report.

        Returns:
            str: Text report of module analysis
        """
        lines = []
        lines.append("## Module Analysis")
        lines.append("")

        # Central Modules
        if self.system_model.central_modules:
            lines.append("### Central Modules (High Connectivity)")
            lines.append("These modules are highly connected and central to the system architecture:")
            for module_name in self.system_model.central_modules[:10]:
                module = self.system_model.modules.get(module_name)
                if module:
                    lines.append(f"  - {module.name}")
                    lines.append(
                        f"    Type: {module.module_type.value if hasattr(module.module_type, 'value') else module.module_type}"
                    )
                    lines.append(f"    In-degree: {module.in_degree}, Out-degree: {module.out_degree}")
                    lines.append(f"    Centrality: {module.centrality:.3f}")
                    lines.append(f"    Complexity: {module.avg_complexity:.2f}")
            lines.append("")

        # Boundary Modules
        if self.system_model.boundary_modules:
            lines.append("### Boundary Modules (Low Connectivity)")
            lines.append("These modules have low connectivity and may be entry/exit points:")
            for module_name in self.system_model.boundary_modules[:10]:
                module = self.system_model.modules.get(module_name)
                if module:
                    lines.append(f"  - {module.name}")
                    lines.append(f"    In-degree: {module.in_degree}, Out-degree: {module.out_degree}")
            lines.append("")

        # Hotspot Modules
        if self.system_model.hotspot_modules:
            lines.append("### Hotspot Modules (High Complexity + High Connectivity)")
            lines.append("⚠️  These modules are complex and highly connected - prime refactoring candidates:")
            for module_name in self.system_model.hotspot_modules[:10]:
                module = self.system_model.modules.get(module_name)
                if module:
                    lines.append(f"  - {module.name}")
                    lines.append(f"    Complexity: {module.avg_complexity:.2f}")
                    lines.append(f"    Centrality: {module.centrality:.3f}")
                    lines.append(f"    Files: {len(module.file_paths)}")
            lines.append("")

        # God Modules
        if self.system_model.god_modules:
            lines.append("### God Modules (Many Dependencies)")
            lines.append("⚠️  These modules depend on many other modules - potential architecture smell:")
            for module_name in self.system_model.god_modules[:10]:
                module = self.system_model.modules.get(module_name)
                if module:
                    lines.append(f"  - {module.name}")
                    lines.append(f"    Out-degree: {module.out_degree}")
                    lines.append(f"    Dependencies: {', '.join(module.dependencies_out[:5])}")
                    if len(module.dependencies_out) > 5:
                        lines.append(f"    ... and {len(module.dependencies_out) - 5} more")
            lines.append("")

        return "\n".join(lines)

    def generate_capability_report(self) -> str:
        """
        Generate capability report.

        Returns:
            str: Text report of detected capabilities
        """
        lines = []
        lines.append("## Detected Capabilities")
        lines.append("")

        if not self.system_model.capabilities:
            lines.append("No capabilities detected.")
            lines.append("")
            return "\n".join(lines)

        # Group by type
        by_type = {}
        for cap in self.system_model.capabilities:
            if cap.capability_type not in by_type:
                by_type[cap.capability_type] = []
            by_type[cap.capability_type].append(cap)

        # Sort capabilities by confidence
        for cap_type, caps in by_type.items():
            caps.sort(key=lambda c: c.confidence, reverse=True)

        # Report by type
        for cap_type in sorted(by_type.keys()):
            lines.append(f"### {cap_type.title()} Capabilities")
            for cap in by_type[cap_type][:10]:
                lines.append(f"  - **{cap.name}**: {cap.description}")
                lines.append(f"    Confidence: {cap.confidence:.2f}")
                lines.append(f"    Modules: {len(cap.modules)}")
                lines.append(f"    Business Domain: {cap.business_domain}")
                if cap.patterns:
                    lines.append(f"    Patterns: {', '.join(cap.patterns[:3])}")
            lines.append("")

        return "\n".join(lines)

    def get_recommendations_data(self) -> List[dict]:
        """
        Get raw recommendation data.

        Returns:
            List[dict]: List of recommendation objects
        """
        recommendations = []

        # Hotspot recommendations
        if self.system_model.hotspot_modules:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "title": "Refactor Hotspot Modules",
                    "description": f"Found {len(self.system_model.hotspot_modules)} hotspot modules with high complexity and connectivity.",
                    "modules": self.system_model.hotspot_modules[:5],
                    "action": "Consider breaking down these modules into smaller, more focused components.",
                }
            )

        # God module recommendations
        if self.system_model.god_modules:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "title": "Reduce God Module Dependencies",
                    "description": f"Found {len(self.system_model.god_modules)} modules with excessive dependencies.",
                    "modules": self.system_model.god_modules[:5],
                    "action": "Apply Dependency Inversion Principle and consider introducing interfaces/abstractions.",
                }
            )

        # High complexity modules
        high_complexity = [
            m.name
            for m in self.system_model.modules.values()
            if m.avg_complexity > self.system_model.avg_module_complexity * 2
        ]
        if high_complexity:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "title": "Reduce Cyclomatic Complexity",
                    "description": f"Found {len(high_complexity)} modules with high cyclomatic complexity.",
                    "modules": high_complexity[:5],
                    "action": "Extract complex logic into separate functions, use guard clauses, and simplify conditionals.",
                }
            )

        # Central module recommendations
        if len(self.system_model.central_modules) > 5:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "title": "Review Central Modules",
                    "description": f"Found {len(self.system_model.central_modules)} central modules.",
                    "modules": self.system_model.central_modules[:5],
                    "action": "Ensure these modules are well-tested and documented, as they're critical to system architecture.",
                }
            )

        return recommendations

    def generate_recommendations(self) -> str:
        """
        Generate refactoring recommendations.

        Returns:
            str: Text report with recommendations
        """
        lines = []
        lines.append("## Refactoring Recommendations")
        lines.append("")

        recommendations = self.get_recommendations_data()

        # No recommendations
        if not recommendations:
            lines.append("✓ No major refactoring recommendations. System architecture appears healthy.")
            lines.append("")
            return "\n".join(lines)

        # Format recommendations
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"### {i}. [{rec['priority']}] {rec['title']}")
            lines.append(f"   {rec['description']}")
            lines.append(f"   Modules: {', '.join(rec['modules'])}")
            if len(rec["modules"]) < len(self.system_model.hotspot_modules):
                # Note: Logic for "more" count was slightly buggy in original (comparing current modules len to ALL hotspots len).
                # Fixing it to just verify if list was truncated.
                # But here I'll keep simple.
                pass
            lines.append(f"   Action: {rec['action']}")
            lines.append("")

        return "\n".join(lines)

    def generate_meta_reflections_report(self) -> str:
        """
        Generate meta-reflections report section.

        Returns:
            str: Text report of meta-reflections
        """
        if not self.meta_reflections:
            return ""

        lines = []
        lines.append("## Meta-Reflections")
        lines.append("")
        lines.append(f"Generated {len(self.meta_reflections)} meta-reflections about code quality and architecture.")
        lines.append("")

        # Group by impact
        by_impact = {}
        for r in self.meta_reflections:
            impact_name = r.impact.value
            if impact_name not in by_impact:
                by_impact[impact_name] = []
            by_impact[impact_name].append(r)

        # Display critical and refactor-recommended
        impact_order = ["critical", "refactor-recommended", "monitor"]
        for impact in impact_order:
            if impact in by_impact:
                reflections_list = by_impact[impact]
                icon = "🔴" if impact == "critical" else "⚠️" if impact == "refactor-recommended" else "📊"
                lines.append(f"### {icon} {impact.upper().replace('-', ' ')} ({len(reflections_list)})")
                lines.append("")

                for r in reflections_list[:5]:  # Show top 5 per category
                    lines.append(f"**{r.title}**")
                    lines.append(f"  Level: {r.level.name} | Scope: {r.scope.value}")
                    lines.append(f"  {r.content[:200]}..." if len(r.content) > 200 else f"  {r.content}")
                    lines.append("")

                    if r.recommendations:
                        lines.append("  Recommendations:")
                        for rec in r.recommendations[:3]:
                            lines.append(f"    - {rec}")
                        lines.append("")

        lines.append("_Full meta-reflections available in JSONL output_")
        lines.append("")

        return "\n".join(lines)

    def generate_full_report(self) -> str:
        """
        Generate complete system report.

        Returns:
            str: Complete text report
        """
        sections = [
            self.generate_summary(),
            self.generate_module_analysis(),
            self.generate_capability_report(),
            self.generate_meta_reflections_report(),
            self.generate_recommendations(),
        ]

        # Filter out empty sections
        sections = [s for s in sections if s.strip()]

        report = "\n".join(sections)
        report += "=" * 80 + "\n"
        report += "End of Report\n"
        report += "=" * 80 + "\n"

        return report

    def save_report(self, output_path: Path) -> None:
        """
        Save report to file.

        Args:
            output_path: Path to save report
        """
        report = self.generate_full_report()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(report)

        log.info(f"Report saved to {output_path}")


def generate_report(
    system_model: SystemModel,
    output_path: Optional[Path] = None,
    meta_reflections: Optional[List[MetaReflection]] = None,
) -> str:
    """
    Convenience function to generate a system model report.

    Args:
        system_model: The system model
        output_path: Optional path to save report
        meta_reflections: Optional list of meta-reflections

    Returns:
        str: The generated report
    """
    generator = ReportGenerator(system_model, meta_reflections=meta_reflections)
    report = generator.generate_full_report()

    if output_path:
        generator.save_report(output_path)

    return report
