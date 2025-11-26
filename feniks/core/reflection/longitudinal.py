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
Longitudinal Analysis Loop - analyzes trends across multiple sessions over time.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import statistics

from feniks.infra.logging import get_logger
from feniks.core.models.domain import SessionSummary
from feniks.core.models.types import MetaReflection, ReflectionLevel, ReflectionScope, ReflectionImpact, ReflectionEvidence

log = get_logger("core.reflection.longitudinal")

class LongitudinalAnalyzer:
    """
    Analyzes trends across multiple sessions (Longitudinal).
    """
    
    def analyze_trends(self, sessions: List[SessionSummary]) -> List[MetaReflection]:
        """
        Analyze multiple sessions to detect trends.
        
        Args:
            sessions: List of session summaries (historical data).
            
        Returns:
            List[MetaReflection]: Trend-based reflections.
        """
        log.info(f"Starting Longitudinal analysis on {len(sessions)} sessions.")
        if len(sessions) < 2:
            log.info("Not enough sessions for longitudinal analysis.")
            return []
            
        reflections = []
        
        # 1. Success Rate Trend
        success_ref = self._analyze_success_rate(sessions)
        if success_ref:
            reflections.append(success_ref)
            
        # 2. Cost Trend
        cost_ref = self._analyze_cost_trend(sessions)
        if cost_ref:
            reflections.append(cost_ref)
            
        log.info(f"Longitudinal analysis complete. Generated {len(reflections)} reflections.")
        return reflections

    def _analyze_success_rate(self, sessions: List[SessionSummary]) -> Optional[MetaReflection]:
        success_count = sum(1 for s in sessions if s.success)
        rate = success_count / len(sessions)
        
        if rate < 0.7: # Below 70% success rate
             return MetaReflection(
                id=f"long-success-{uuid.uuid4()}",
                timestamp=datetime.now().isoformat(),
                project_id="longitudinal",
                level=ReflectionLevel.META_REFLECTION,
                scope=ReflectionScope.SYSTEM,
                impact=ReflectionImpact.CRITICAL,
                title="Low Global Success Rate",
                content=f"Global success rate is {rate:.1%} across {len(sessions)} sessions.",
                evidence=[
                    ReflectionEvidence(type="metric", source="session_history", value=rate)
                ],
                recommendations=["Conduct deep dive into failed sessions", "Review recent changes to agent logic"]
            )
        return None

    def _analyze_cost_trend(self, sessions: List[SessionSummary]) -> Optional[MetaReflection]:
        costs = [s.cost_profile.cost_usd for s in sessions if s.cost_profile]
        if not costs or len(costs) < 5:
            return None
            
        # Simple linear trend check (comparing avg of first half vs last half)
        mid = len(costs) // 2
        first_half_avg = statistics.mean(costs[:mid])
        last_half_avg = statistics.mean(costs[mid:])
        
        if last_half_avg > first_half_avg * 1.2: # 20% increase
            return MetaReflection(
                id=f"long-cost-inc-{uuid.uuid4()}",
                timestamp=datetime.now().isoformat(),
                project_id="longitudinal",
                level=ReflectionLevel.REFLECTION,
                scope=ReflectionScope.TECHNICAL_DEBT,
                impact=ReflectionImpact.MONITOR,
                title="Rising Cost Trend",
                content=f"Average session cost increased from ${first_half_avg:.3f} to ${last_half_avg:.3f} (+{((last_half_avg/first_half_avg)-1)*100:.1f}%)",
                evidence=[
                    ReflectionEvidence(type="trend", source="cost_history", value=last_half_avg)
                ],
                recommendations=["Audit token usage", "Check for prompt bloating"]
            )
        return None
