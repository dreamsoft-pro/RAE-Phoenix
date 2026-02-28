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
Quality Policies - Declarative rules for reasoning quality.
"""
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List

from feniks.core.models.domain import SessionSummary
from feniks.core.models.types import (
    MetaReflection,
    ReflectionEvidence,
    ReflectionImpact,
    ReflectionLevel,
    ReflectionScope,
)
from feniks.infra.logging import get_logger

log = get_logger("core.policies.quality_policy")


@dataclass
class QualityPolicyConfig:
    """Configuration for reasoning quality policies."""

    min_thought_length: int = 10  # Minimum characters in a thought
    forbidden_patterns: List[str] = None  # Regex patterns that shouldn't appear in thoughts
    require_thought_before_action: bool = True


class QualityPolicyEnforcer:
    """Enforces quality policies on reasoning traces."""

    def __init__(self, config: QualityPolicyConfig = QualityPolicyConfig()):
        self.config = config
        if self.config.forbidden_patterns is None:
            self.config.forbidden_patterns = [
                r"I don't know what to do",
                r"just guessing",
            ]

    def check_trace_quality(self, session: SessionSummary) -> List[MetaReflection]:
        """
        Validate reasoning traces against quality rules.
        """
        reflections = []
        traces = session.reasoning_traces

        if not traces:
            return reflections

        # Rule 1: Minimum Thought Length
        short_thoughts = [t for t in traces if len(t.thought.strip()) < self.config.min_thought_length]
        if short_thoughts:
            reflections.append(
                MetaReflection(
                    id=f"policy-quality-len-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="quality-policy",
                    level=ReflectionLevel.REFLECTION,
                    scope=ReflectionScope.PATTERN,
                    impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                    title="Reasoning Steps Too Short",
                    content=f"Found {len(short_thoughts)} steps with thoughts shorter than {self.config.min_thought_length} chars.",
                    evidence=[ReflectionEvidence(type="count", source="quality_policy", value=len(short_thoughts))],
                    recommendations=["Adjust system prompt to encourage verbose reasoning"],
                )
            )

        # Rule 2: Forbidden Patterns
        for pattern in self.config.forbidden_patterns:
            matches = [t for t in traces if re.search(pattern, t.thought, re.IGNORECASE)]
            if matches:
                reflections.append(
                    MetaReflection(
                        id=f"policy-quality-pattern-{uuid.uuid4()}",
                        timestamp=datetime.now().isoformat(),
                        project_id="quality-policy",
                        level=ReflectionLevel.META_REFLECTION,
                        scope=ReflectionScope.PATTERN,
                        impact=ReflectionImpact.CRITICAL,
                        title="Forbidden Reasoning Pattern Detected",
                        content=f"Found {len(matches)} steps matching forbidden pattern: '{pattern}'",
                        recommendations=["Investigate agent confusion or hallucinations"],
                    )
                )

        return reflections
