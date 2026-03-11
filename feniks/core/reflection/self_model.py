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
Self-Model Loop - maintains and updates the system's understanding of its own performance.
"""
import uuid
from datetime import datetime
from typing import List

from feniks.core.models.types import (
    MetaReflection,
    ReflectionEvidence,
    ReflectionImpact,
    ReflectionLevel,
    ReflectionScope,
)
from feniks.infra.logging import get_logger

log = get_logger("core.reflection.self_model")


class SelfModelAnalyzer:
    """
    Analyzes the system's own performance and updates its self-model.
    """

    def update_self_model(self, recent_reflections: List[MetaReflection]) -> List[MetaReflection]:
        """
        Update self-model based on recent meta-reflections.

        Args:
            recent_reflections: List of reflections generated in recent cycles.

        Returns:
            List[MetaReflection]: New reflections about the system itself.
        """
        log.info("Updating Self-Model...")
        self_reflections = []

        # 1. Check for Reflection Fatigue (too many critical alerts)
        critical_count = sum(1 for r in recent_reflections if r.impact == ReflectionImpact.CRITICAL)
        if critical_count > 5:
            self_reflections.append(
                MetaReflection(
                    id=f"self-fatigue-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="self-model",
                    level=ReflectionLevel.META_REFLECTION,
                    scope=ReflectionScope.SYSTEM,
                    impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                    title="High Critical Alert Volume",
                    content=f"Generated {critical_count} critical reflections recently. Danger of alert fatigue.",
                    evidence=[ReflectionEvidence(type="count", source="meta_reflection_engine", value=critical_count)],
                    recommendations=["Prioritize fixing root causes", "Tune criticality thresholds"],
                )
            )

        log.info(f"Self-Model update complete. Generated {len(self_reflections)} insights.")
        return self_reflections
