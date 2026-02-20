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
Meta-Reflection Engine - generates meta-reflections about code quality and architecture.
Analyzes system model and generates insights, recommendations, and meta-observations.
"""
import json
from pathlib import Path
from typing import List

from feniks.core.models.domain import SessionSummary
from feniks.core.models.types import MetaReflection, ReflectionLevel, SystemModel
from feniks.core.policies.manager import PolicyManager
from feniks.core.reflection.longitudinal import LongitudinalAnalyzer
from feniks.core.reflection.post_mortem import PostMortemAnalyzer
from feniks.core.reflection.rules import ReflectionRuleSet
from feniks.core.reflection.self_model import SelfModelAnalyzer
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("core.meta_reflection")


class MetaReflectionEngine:
    """
    Engine for generating meta-reflections from system analysis.
    """

    def __init__(self):
        """Initialize the meta-reflection engine."""
        self.rule_set = ReflectionRuleSet()
        self.post_mortem = PostMortemAnalyzer()
        self.longitudinal = LongitudinalAnalyzer()
        self.self_model = SelfModelAnalyzer()
        self.policy_manager = PolicyManager()
        log.info("MetaReflectionEngine initialized")

    def run_post_mortem(self, session_summary: SessionSummary, project_id: str = "unknown") -> List[MetaReflection]:
        """
        Run post-mortem analysis on a session, including policy checks.
        """
        # Standard post-mortem insights
        reflections = self.post_mortem.analyze_session(session_summary)

        # Policy compliance checks
        policy_violations = self.policy_manager.check_session_compliance(session_summary, project_id)
        reflections.extend(policy_violations)

        return reflections

    def run_longitudinal(self, sessions: List[SessionSummary]) -> List[MetaReflection]:
        """Run longitudinal analysis on multiple sessions."""
        return self.longitudinal.analyze_trends(sessions)

    def run_self_model_update(self, recent_reflections: List[MetaReflection]) -> List[MetaReflection]:
        """Update self-model based on recent reflections."""
        return self.self_model.update_self_model(recent_reflections)

    def generate_reflections(self, system_model: SystemModel) -> List[MetaReflection]:
        """
        Generate meta-reflections for a system model.

        Args:
            system_model: The system model to analyze

        Returns:
            List[MetaReflection]: Generated meta-reflections
        """
        log.info(f"Generating meta-reflections for project: {system_model.project_id}")

        # Evaluate all rules
        reflections = self.rule_set.evaluate(system_model)

        # Sort by impact and level
        reflections.sort(
            key=lambda r: (
                ["critical", "refactor-recommended", "monitor", "informational"].index(r.impact.value),
                -r.level.value,
            )
        )

        log.info(f"Generated {len(reflections)} meta-reflections")

        # Log summary by level
        by_level = {}
        for r in reflections:
            level_name = r.level.name
            if level_name not in by_level:
                by_level[level_name] = 0
            by_level[level_name] += 1

        for level, count in by_level.items():
            log.info(f"  {level}: {count} reflections")

        return reflections

    def save_reflections_jsonl(self, reflections: List[MetaReflection], output_path: Path) -> None:
        """
        Save reflections to JSONL file.

        Args:
            reflections: List of reflections to save
            output_path: Path to output JSONL file
        """
        log.info(f"Saving {len(reflections)} reflections to {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            for reflection in reflections:
                # Convert to dict
                data = {
                    "id": reflection.id,
                    "timestamp": reflection.timestamp,
                    "project_id": reflection.project_id,
                    "level": reflection.level.value,
                    "level_name": reflection.level.name,
                    "scope": reflection.scope.value,
                    "impact": reflection.impact.value,
                    "title": reflection.title,
                    "content": reflection.content,
                    "evidence": [
                        {"type": e.type, "source": e.source, "value": e.value, "context": e.context}
                        for e in reflection.evidence
                    ],
                    "related_modules": reflection.related_modules,
                    "related_files": reflection.related_files,
                    "recommendations": reflection.recommendations,
                    "origin": reflection.origin,
                    "tags": reflection.tags,
                    "confidence": reflection.confidence,
                    "metadata": reflection.metadata,
                }

                # Write as JSON line
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

        log.info(f"Reflections saved to {output_path}")

    def load_reflections_jsonl(self, input_path: Path) -> List[MetaReflection]:
        """
        Load reflections from JSONL file.

        Args:
            input_path: Path to input JSONL file

        Returns:
            List[MetaReflection]: Loaded reflections
        """
        from feniks.core.models.types import ReflectionEvidence, ReflectionImpact, ReflectionScope

        log.info(f"Loading reflections from {input_path}")

        if not input_path.exists():
            raise FeniksError(f"Reflection file not found: {input_path}")

        reflections = []

        with input_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                try:
                    data = json.loads(line)

                    # Parse enums
                    level = ReflectionLevel(data["level"])
                    scope = ReflectionScope(data["scope"])
                    impact = ReflectionImpact(data["impact"])

                    # Parse evidence
                    evidence = [
                        ReflectionEvidence(
                            type=e["type"], source=e["source"], value=e["value"], context=e.get("context")
                        )
                        for e in data.get("evidence", [])
                    ]

                    # Create reflection
                    reflection = MetaReflection(
                        id=data["id"],
                        timestamp=data["timestamp"],
                        project_id=data["project_id"],
                        level=level,
                        scope=scope,
                        impact=impact,
                        title=data["title"],
                        content=data["content"],
                        evidence=evidence,
                        related_modules=data.get("related_modules", []),
                        related_files=data.get("related_files", []),
                        recommendations=data.get("recommendations", []),
                        origin=data.get("origin", "feniks"),
                        tags=data.get("tags", []),
                        confidence=data.get("confidence", 1.0),
                        metadata=data.get("metadata", {}),
                    )

                    reflections.append(reflection)

                except Exception as e:
                    log.warning(f"Failed to parse reflection on line {line_num}: {e}")

        log.info(f"Loaded {len(reflections)} reflections")

        return reflections

    def generate_reflection_summary(self, reflections: List[MetaReflection]) -> str:
        """
        Generate a text summary of reflections.

        Args:
            reflections: List of reflections

        Returns:
            str: Text summary
        """
        lines = []
        lines.append("=" * 80)
        lines.append("Meta-Reflections Summary")
        lines.append("=" * 80)
        lines.append(f"Total Reflections: {len(reflections)}")
        lines.append("")

        # Group by impact
        by_impact = {}
        for r in reflections:
            impact_name = r.impact.value
            if impact_name not in by_impact:
                by_impact[impact_name] = []
            by_impact[impact_name].append(r)

        # Display by impact priority
        impact_order = ["critical", "refactor-recommended", "monitor", "informational"]
        for impact in impact_order:
            if impact in by_impact:
                reflections_list = by_impact[impact]
                lines.append(f"## {impact.upper().replace('-', ' ')} ({len(reflections_list)})")
                lines.append("")

                for r in reflections_list:
                    lines.append(f"### {r.title}")
                    lines.append(f"Level: {r.level.name} | Scope: {r.scope.value} | Confidence: {r.confidence:.2f}")
                    lines.append("")
                    lines.append(r.content)
                    lines.append("")

                    if r.recommendations:
                        lines.append("Recommendations:")
                        for i, rec in enumerate(r.recommendations, 1):
                            lines.append(f"  {i}. {rec}")
                        lines.append("")

                    if r.related_modules:
                        lines.append(f"Related Modules: {', '.join(r.related_modules[:5])}")
                        if len(r.related_modules) > 5:
                            lines.append(f"  ... and {len(r.related_modules) - 5} more")
                        lines.append("")

                    lines.append("-" * 80)
                    lines.append("")

        lines.append("=" * 80)
        lines.append("End of Meta-Reflections")
        lines.append("=" * 80)

        return "\n".join(lines)


def generate_meta_reflections(system_model: SystemModel) -> List[MetaReflection]:
    """
    Convenience function to generate meta-reflections.

    Args:
        system_model: The system model to analyze

    Returns:
        List[MetaReflection]: Generated reflections
    """
    engine = MetaReflectionEngine()
    return engine.generate_reflections(system_model)


def save_meta_reflections(reflections: List[MetaReflection], output_path: Path, format: str = "jsonl") -> None:
    """
    Convenience function to save meta-reflections.

    Args:
        reflections: Reflections to save
        output_path: Output file path
        format: Output format ('jsonl' or 'txt')
    """
    engine = MetaReflectionEngine()

    if format == "jsonl":
        engine.save_reflections_jsonl(reflections, output_path)
    elif format == "txt":
        summary = engine.generate_reflection_summary(reflections)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(summary)
        log.info(f"Reflection summary saved to {output_path}")
    else:
        raise FeniksError(f"Unsupported format: {format}")
