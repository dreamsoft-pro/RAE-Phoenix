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
Reflection Rules - rules for generating meta-reflections.
Defines conditions and templates for different types of reflections.
"""
from dataclasses import dataclass
from typing import Callable, List

from feniks.core.models.types import (
    MetaReflection,
    ReflectionEvidence,
    ReflectionImpact,
    ReflectionLevel,
    ReflectionScope,
    SystemModel,
)


@dataclass
class ReflectionRule:
    """Rule for generating a meta-reflection."""

    id: str
    name: str
    description: str
    level: ReflectionLevel
    scope: ReflectionScope
    impact: ReflectionImpact
    condition: Callable[[SystemModel], bool]
    generate: Callable[[SystemModel], MetaReflection]
    tags: List[str]


class ReflectionRuleSet:
    """Collection of reflection rules."""

    def __init__(self):
        """Initialize the rule set."""
        self.rules: List[ReflectionRule] = []
        self._build_rules()

    def _build_rules(self):
        """Build the set of reflection rules."""
        # Rule 1: God Modules Detection
        self.rules.append(
            ReflectionRule(
                id="god_modules",
                name="God Modules Detected",
                description="Modules with excessive dependencies (god object anti-pattern)",
                level=ReflectionLevel.REFLECTION,
                scope=ReflectionScope.MODULE,
                impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                condition=lambda sm: len(sm.god_modules) > 0,
                generate=self._generate_god_modules_reflection,
                tags=["architecture", "dependencies", "anti-pattern"],
            )
        )

        # Rule 2: Hotspot Modules
        self.rules.append(
            ReflectionRule(
                id="hotspot_modules",
                name="Hotspot Modules Identified",
                description="Modules with high complexity and high connectivity",
                level=ReflectionLevel.REFLECTION,
                scope=ReflectionScope.MODULE,
                impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                condition=lambda sm: len(sm.hotspot_modules) > 0,
                generate=self._generate_hotspot_reflection,
                tags=["complexity", "maintenance", "risk"],
            )
        )

        # Rule 3: High System Complexity
        self.rules.append(
            ReflectionRule(
                id="high_complexity",
                name="High Overall Complexity",
                description="System exhibits high cyclomatic complexity",
                level=ReflectionLevel.REFLECTION,
                scope=ReflectionScope.CODEBASE,
                impact=ReflectionImpact.MONITOR,
                condition=lambda sm: sm.avg_module_complexity > 50,
                generate=self._generate_complexity_reflection,
                tags=["complexity", "quality"],
            )
        )

        # Rule 4: Centralization Risk
        self.rules.append(
            ReflectionRule(
                id="centralization_risk",
                name="Over-Centralized Architecture",
                description="Too many central modules create single points of failure",
                level=ReflectionLevel.META_REFLECTION,
                scope=ReflectionScope.SYSTEM,
                impact=ReflectionImpact.MONITOR,
                condition=lambda sm: len(sm.central_modules) > len(sm.modules) * 0.3,
                generate=self._generate_centralization_reflection,
                tags=["architecture", "risk", "resilience"],
            )
        )

        # Rule 5: Module Isolation
        self.rules.append(
            ReflectionRule(
                id="poor_isolation",
                name="Poor Module Isolation",
                description="High coupling between modules",
                level=ReflectionLevel.REFLECTION,
                scope=ReflectionScope.SYSTEM,
                impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                condition=lambda sm: self._check_high_coupling(sm),
                generate=self._generate_coupling_reflection,
                tags=["coupling", "modularity", "architecture"],
            )
        )

        # Rule 6: Large Modules
        self.rules.append(
            ReflectionRule(
                id="large_modules",
                name="Large Modules Detected",
                description="Some modules are excessively large",
                level=ReflectionLevel.OBSERVATION,
                scope=ReflectionScope.MODULE,
                impact=ReflectionImpact.MONITOR,
                condition=lambda sm: self._check_large_modules(sm),
                generate=self._generate_large_modules_reflection,
                tags=["size", "maintainability"],
            )
        )

        # Rule 7: Capability Diversity
        self.rules.append(
            ReflectionRule(
                id="capability_diversity",
                name="Rich Capability Set",
                description="System has diverse capabilities",
                level=ReflectionLevel.OBSERVATION,
                scope=ReflectionScope.SYSTEM,
                impact=ReflectionImpact.INFORMATIONAL,
                condition=lambda sm: len(sm.capabilities) >= 5,
                generate=self._generate_capability_reflection,
                tags=["capabilities", "features"],
            )
        )

        # Rule 8: Architecture Quality Assessment
        self.rules.append(
            ReflectionRule(
                id="architecture_quality",
                name="Architecture Quality Assessment",
                description="Overall architecture quality evaluation",
                level=ReflectionLevel.META_REFLECTION,
                scope=ReflectionScope.SYSTEM,
                impact=ReflectionImpact.INFORMATIONAL,
                condition=lambda sm: True,  # Always generate
                generate=self._generate_architecture_quality_reflection,
                tags=["architecture", "quality", "assessment"],
            )
        )

    def _check_high_coupling(self, sm: SystemModel) -> bool:
        """Check if system has high coupling."""
        if not sm.modules:
            return False
        avg_deps = sum(len(m.dependencies_out) for m in sm.modules.values()) / len(sm.modules)
        return avg_deps > 5

    def _check_large_modules(self, sm: SystemModel) -> bool:
        """Check if system has large modules."""
        if not sm.modules:
            return False
        max_chunks = max((m.chunk_count for m in sm.modules.values()), default=0)
        return max_chunks > 20

    def _generate_god_modules_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate reflection about god modules."""
        import hashlib
        from datetime import datetime

        god_mods = sm.god_modules[:5]
        evidence = []
        related_modules = []

        for mod_name in god_mods:
            if mod_name in sm.modules:
                mod = sm.modules[mod_name]
                evidence.append(
                    ReflectionEvidence(
                        type="metric",
                        source=f"module:{mod_name}",
                        value={"out_degree": mod.out_degree, "dependencies": len(mod.dependencies_out)},
                        context=f"Module depends on {mod.out_degree} other modules",
                    )
                )
                related_modules.append(mod_name)

        content = (
            f"Detected {len(sm.god_modules)} god module(s) with excessive dependencies. "
            f"God modules: {', '.join(god_mods)}. "
            f"These modules violate the Single Responsibility Principle and create tight coupling. "
            f"Consider applying Dependency Inversion Principle and breaking down responsibilities."
        )

        recommendations = [
            "Apply Dependency Inversion Principle - depend on abstractions, not concretions",
            "Break down large modules into smaller, focused components",
            "Extract shared functionality into utility modules",
            "Consider introducing interfaces/facades to reduce direct dependencies",
            "Review and eliminate unnecessary cross-module dependencies",
        ]

        reflection_id = hashlib.sha256(f"god_modules_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.MODULE,
            impact=ReflectionImpact.REFACTOR_RECOMMENDED,
            title="God Modules Detected - Excessive Dependencies",
            content=content,
            evidence=evidence,
            related_modules=related_modules,
            recommendations=recommendations,
            tags=["god-module", "dependencies", "srp-violation"],
            confidence=0.9,
        )

    def _generate_hotspot_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate reflection about hotspot modules."""
        import hashlib
        from datetime import datetime

        hotspots = sm.hotspot_modules[:5]
        evidence = []
        related_modules = []

        for mod_name in hotspots:
            if mod_name in sm.modules:
                mod = sm.modules[mod_name]
                evidence.append(
                    ReflectionEvidence(
                        type="metric",
                        source=f"module:{mod_name}",
                        value={
                            "complexity": mod.avg_complexity,
                            "centrality": mod.centrality,
                            "chunk_count": mod.chunk_count,
                        },
                        context=f"High complexity ({mod.avg_complexity:.1f}) + high centrality ({mod.centrality:.2f})",
                    )
                )
                related_modules.append(mod_name)

        content = (
            f"Identified {len(sm.hotspot_modules)} hotspot module(s) with high complexity and high connectivity. "
            f"Hotspots: {', '.join(hotspots)}. "
            f"These modules are both complex and central to the system, making them risky to modify and "
            f"difficult to maintain. They represent prime candidates for refactoring."
        )

        recommendations = [
            "Prioritize test coverage for these modules to enable safe refactoring",
            "Extract complex logic into smaller, testable functions",
            "Consider splitting modules along feature or domain boundaries",
            "Simplify conditional logic using guard clauses and early returns",
            "Document complex business logic and edge cases",
        ]

        reflection_id = hashlib.sha256(f"hotspots_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.MODULE,
            impact=ReflectionImpact.REFACTOR_RECOMMENDED,
            title="Hotspot Modules - High Risk Areas",
            content=content,
            evidence=evidence,
            related_modules=related_modules,
            recommendations=recommendations,
            tags=["hotspot", "complexity", "risk"],
            confidence=0.85,
        )

    def _generate_complexity_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate reflection about overall complexity."""
        import hashlib
        from datetime import datetime

        evidence = [
            ReflectionEvidence(
                type="metric",
                source="system_model",
                value={"avg_module_complexity": sm.avg_module_complexity},
                context="Average cyclomatic complexity across all modules",
            )
        ]

        # Find modules with highest complexity
        high_complexity_modules = sorted(
            [(m.name, m.avg_complexity) for m in sm.modules.values()], key=lambda x: x[1], reverse=True
        )[:5]

        content = (
            f"System exhibits high overall complexity with average cyclomatic complexity of "
            f"{sm.avg_module_complexity:.1f}. "
            f"High complexity modules: {', '.join([f'{name} ({comp:.1f})' for name, comp in high_complexity_modules])}. "
            f"High cyclomatic complexity indicates code that is difficult to test, understand, and maintain."
        )

        recommendations = [
            "Refactor complex functions by extracting logic into smaller, focused functions",
            "Simplify conditional logic and reduce nested structures",
            "Apply the Single Responsibility Principle at the function level",
            "Add unit tests to enable safe refactoring",
            "Set complexity thresholds in CI/CD to prevent further degradation",
        ]

        reflection_id = hashlib.sha256(f"complexity_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.CODEBASE,
            impact=ReflectionImpact.MONITOR,
            title="High Overall Complexity",
            content=content,
            evidence=evidence,
            related_modules=[name for name, _ in high_complexity_modules],
            recommendations=recommendations,
            tags=["complexity", "maintainability"],
            confidence=0.95,
        )

    def _generate_centralization_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate meta-reflection about centralization."""
        import hashlib
        from datetime import datetime

        central_ratio = len(sm.central_modules) / len(sm.modules) if sm.modules else 0

        evidence = [
            ReflectionEvidence(
                type="analysis",
                source="system_architecture",
                value={
                    "central_modules_count": len(sm.central_modules),
                    "total_modules": len(sm.modules),
                    "centralization_ratio": central_ratio,
                },
                context=f"{central_ratio*100:.1f}% of modules are highly central",
            )
        ]

        content = (
            f"Architecture exhibits high centralization with {len(sm.central_modules)} out of "
            f"{len(sm.modules)} modules ({central_ratio*100:.1f}%) being highly central. "
            f"While central modules are normal in any architecture, excessive centralization creates "
            f"single points of failure and coupling. Changes to central modules ripple through the system. "
            f"This is a meta-observation about the overall architectural pattern."
        )

        recommendations = [
            "Review if all central modules truly need to be so interconnected",
            "Consider introducing abstraction layers to reduce direct dependencies",
            "Evaluate if some central modules can be split along domain boundaries",
            "Ensure central modules have comprehensive test coverage",
            "Monitor changes to central modules carefully via code review",
        ]

        reflection_id = hashlib.sha256(f"centralization_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.META_REFLECTION,
            scope=ReflectionScope.SYSTEM,
            impact=ReflectionImpact.MONITOR,
            title="Over-Centralized Architecture",
            content=content,
            evidence=evidence,
            related_modules=sm.central_modules[:10],
            recommendations=recommendations,
            tags=["architecture", "centralization", "risk"],
            confidence=0.8,
        )

    def _generate_coupling_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate reflection about coupling."""
        import hashlib
        from datetime import datetime

        avg_deps = sum(len(m.dependencies_out) for m in sm.modules.values()) / len(sm.modules) if sm.modules else 0

        evidence = [
            ReflectionEvidence(
                type="metric",
                source="dependency_analysis",
                value={"avg_dependencies_per_module": avg_deps, "total_dependencies": len(sm.dependencies)},
                context=f"Average {avg_deps:.1f} outgoing dependencies per module",
            )
        ]

        content = (
            f"System exhibits high coupling with an average of {avg_deps:.1f} dependencies per module. "
            f"Total {len(sm.dependencies)} dependency relationships exist between {len(sm.modules)} modules. "
            f"High coupling reduces modularity, makes testing difficult, and increases change ripple effects."
        )

        recommendations = [
            "Apply Dependency Inversion Principle to reduce concrete dependencies",
            "Introduce interfaces/contracts between modules",
            "Consider event-driven patterns to decouple modules",
            "Extract shared functionality into dedicated utility modules",
            "Review and eliminate unnecessary cross-module dependencies",
        ]

        reflection_id = hashlib.sha256(f"coupling_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.SYSTEM,
            impact=ReflectionImpact.REFACTOR_RECOMMENDED,
            title="High Module Coupling",
            content=content,
            evidence=evidence,
            related_modules=[],
            recommendations=recommendations,
            tags=["coupling", "dependencies", "modularity"],
            confidence=0.85,
        )

    def _generate_large_modules_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate observation about large modules."""
        import hashlib
        from datetime import datetime

        large_modules = [(m.name, m.chunk_count) for m in sm.modules.values() if m.chunk_count > 20]
        large_modules.sort(key=lambda x: x[1], reverse=True)

        evidence = [
            ReflectionEvidence(
                type="metric",
                source=f"module:{name}",
                value={"chunk_count": count},
                context=f"Module contains {count} chunks",
            )
            for name, count in large_modules[:5]
        ]

        content = (
            f"Observed {len(large_modules)} large module(s) with more than 20 chunks. "
            f"Largest modules: {', '.join([f'{name} ({count})' for name, count in large_modules[:5]])}. "
            f"Large modules may indicate insufficient decomposition or evolving god objects."
        )

        recommendations = [
            "Consider splitting large modules along feature boundaries",
            "Extract reusable components into separate modules",
            "Review if module has grown beyond its intended responsibility",
        ]

        reflection_id = hashlib.sha256(f"large_modules_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.OBSERVATION,
            scope=ReflectionScope.MODULE,
            impact=ReflectionImpact.MONITOR,
            title="Large Modules Observed",
            content=content,
            evidence=evidence,
            related_modules=[name for name, _ in large_modules[:5]],
            recommendations=recommendations,
            tags=["size", "modularity"],
            confidence=1.0,
        )

    def _generate_capability_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate observation about capabilities."""
        import hashlib
        from datetime import datetime

        cap_by_type = {}
        for cap in sm.capabilities:
            if cap.capability_type not in cap_by_type:
                cap_by_type[cap.capability_type] = []
            cap_by_type[cap.capability_type].append(cap.name)

        evidence = [
            ReflectionEvidence(
                type="analysis",
                source="capability_detection",
                value={
                    "total_capabilities": len(sm.capabilities),
                    "by_type": {k: len(v) for k, v in cap_by_type.items()},
                },
                context="Capabilities detected through pattern matching and analysis",
            )
        ]

        content = (
            f"System demonstrates a rich set of {len(sm.capabilities)} capabilities across "
            f"{len(cap_by_type)} categories. "
            f"Capability types: {', '.join([f'{k} ({len(v)})' for k, v in cap_by_type.items()])}. "
            f"This diversity indicates a mature, feature-rich system."
        )

        recommendations = [
            "Document key capabilities for new team members",
            "Ensure each capability has adequate test coverage",
            "Consider capability mapping for architecture documentation",
        ]

        reflection_id = hashlib.sha256(f"capabilities_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.OBSERVATION,
            scope=ReflectionScope.SYSTEM,
            impact=ReflectionImpact.INFORMATIONAL,
            title="Rich Capability Set",
            content=content,
            evidence=evidence,
            related_modules=[],
            recommendations=recommendations,
            tags=["capabilities", "features"],
            confidence=0.8,
        )

    def _generate_architecture_quality_reflection(self, sm: SystemModel) -> MetaReflection:
        """Generate meta-reflection about overall architecture quality."""
        import hashlib
        from datetime import datetime

        # Calculate quality score
        quality_factors = {
            "modularity": 1.0 - (len(sm.god_modules) / max(len(sm.modules), 1)),
            "complexity": max(0, 1.0 - (sm.avg_module_complexity / 100.0)),
            "hotspot_risk": 1.0 - (len(sm.hotspot_modules) / max(len(sm.modules), 1)),
        }
        overall_quality = sum(quality_factors.values()) / len(quality_factors)

        evidence = [
            ReflectionEvidence(
                type="analysis",
                source="architecture_assessment",
                value={
                    "quality_score": overall_quality,
                    "factors": quality_factors,
                    "total_modules": len(sm.modules),
                    "god_modules": len(sm.god_modules),
                    "hotspots": len(sm.hotspot_modules),
                    "avg_complexity": sm.avg_module_complexity,
                },
                context="Composite quality assessment based on multiple factors",
            )
        ]

        if overall_quality >= 0.8:
            assessment = "excellent"
            impact = ReflectionImpact.INFORMATIONAL
        elif overall_quality >= 0.6:
            assessment = "good"
            impact = ReflectionImpact.MONITOR
        elif overall_quality >= 0.4:
            assessment = "fair"
            impact = ReflectionImpact.REFACTOR_RECOMMENDED
        else:
            assessment = "poor"
            impact = ReflectionImpact.CRITICAL

        content = (
            f"Overall architecture quality assessment: {assessment} (score: {overall_quality:.2f}). "
            f"Modularity: {quality_factors['modularity']:.2f}, "
            f"Complexity: {quality_factors['complexity']:.2f}, "
            f"Hotspot Risk: {quality_factors['hotspot_risk']:.2f}. "
            f"This meta-reflection synthesizes multiple architectural concerns into an overall quality assessment."
        )

        recommendations = []
        if quality_factors["modularity"] < 0.7:
            recommendations.append("Focus on reducing god modules and improving module independence")
        if quality_factors["complexity"] < 0.7:
            recommendations.append("Invest in complexity reduction through refactoring")
        if quality_factors["hotspot_risk"] < 0.7:
            recommendations.append("Address hotspot modules as highest priority")
        if not recommendations:
            recommendations.append("Maintain current architectural quality through code reviews and standards")

        reflection_id = hashlib.sha256(f"arch_quality_{sm.project_id}_{sm.timestamp}".encode()).hexdigest()[:16]

        return MetaReflection(
            id=reflection_id,
            timestamp=datetime.utcnow().isoformat(),
            project_id=sm.project_id,
            level=ReflectionLevel.META_REFLECTION,
            scope=ReflectionScope.SYSTEM,
            impact=impact,
            title=f"Architecture Quality: {assessment.title()}",
            content=content,
            evidence=evidence,
            related_modules=[],
            recommendations=recommendations,
            tags=["architecture", "quality", "assessment"],
            confidence=0.75,
        )

    def evaluate(self, system_model: SystemModel) -> List[MetaReflection]:
        """
        Evaluate all rules against a system model.

        Args:
            system_model: The system model to evaluate

        Returns:
            List[MetaReflection]: Generated reflections
        """
        reflections = []

        for rule in self.rules:
            try:
                if rule.condition(system_model):
                    reflection = rule.generate(system_model)
                    reflections.append(reflection)
            except Exception as e:
                # Log but don't fail
                from feniks.infra.logging import get_logger

                log = get_logger("reflection_rules")
                log.warning(f"Rule {rule.id} failed: {e}")

        return reflections
