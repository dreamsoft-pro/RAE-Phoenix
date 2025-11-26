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
Post-Mortem Analysis Loop - analyzes completed sessions to identify failures and inefficiencies.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from feniks.infra.logging import get_logger
from feniks.core.models.domain import SessionSummary, FeniksReport, ReasoningTrace, CostProfile
from feniks.core.models.types import MetaReflection, ReflectionLevel, ReflectionScope, ReflectionImpact, ReflectionEvidence

log = get_logger("core.reflection.post_mortem")

class PostMortemAnalyzer:
    """
    Analyzes individual sessions (Post-Mortem) to generate insights and recommendations.
    """
    
    def analyze_session(self, session_summary: SessionSummary) -> List[MetaReflection]:
        """
        Analyze a single session and generate meta-reflections.
        
        Args:
            session_summary: The session summary to analyze.
            
        Returns:
            List[MetaReflection]: List of generated meta-reflections.
        """
        log.info(f"Starting Post-Mortem analysis for session: {session_summary.session_id}")
        reflections = []
        
        # 1. Analyze Success/Failure
        if not session_summary.success:
            reflections.append(self._create_failure_reflection(session_summary))
            
        # 2. Analyze Cost
        if session_summary.cost_profile:
            cost_ref = self._analyze_cost(session_summary)
            if cost_ref:
                reflections.append(cost_ref)
                
        # 3. Analyze Reasoning Traces (e.g. loops, empty thoughts)
        trace_refs = self._analyze_traces(session_summary)
        reflections.extend(trace_refs)
        
        log.info(f"Post-Mortem analysis complete. Generated {len(reflections)} reflections.")
        return reflections

    def _create_failure_reflection(self, session: SessionSummary) -> MetaReflection:
        return MetaReflection(
            id=f"pm-fail-{uuid.uuid4()}",
            timestamp=datetime.now().isoformat(),
            project_id="post-mortem", # Context dependent, maybe passed in
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.TECHNICAL_DEBT, # Or PROCESS
            impact=ReflectionImpact.CRITICAL,
            title="Session Failure Detected",
            content=f"Session {session.session_id} marked as failed.",
            evidence=[
                ReflectionEvidence(type="status", source="session_summary", value=False)
            ],
            recommendations=["Investigate logs for errors", "Check reasoning trace for abandonment"]
        )

    def _analyze_cost(self, session: SessionSummary) -> Optional[MetaReflection]:
        # Simple heuristic: Cost > $0.50 is high for a single session (example threshold)
        COST_THRESHOLD = 0.50
        if session.cost_profile.cost_usd > COST_THRESHOLD:
            return MetaReflection(
                id=f"pm-cost-{uuid.uuid4()}",
                timestamp=datetime.now().isoformat(),
                project_id="post-mortem",
                level=ReflectionLevel.OBSERVATION,
                scope=ReflectionScope.TECHNICAL_DEBT,
                impact=ReflectionImpact.MONITOR,
                title="High Session Cost",
                content=f"Session cost ${session.cost_profile.cost_usd:.2f} exceeded threshold ${COST_THRESHOLD:.2f}",
                evidence=[
                    ReflectionEvidence(type="metric", source="cost_profile", value=session.cost_profile.cost_usd)
                ],
                recommendations=["Review prompt verbosity", "Check for reasoning loops"]
            )
        return None

    def _analyze_traces(self, session: SessionSummary) -> List[MetaReflection]:
        reflections = []
        traces = session.reasoning_traces
        if not traces:
            return reflections
            
        # Check for empty thoughts
        empty_thoughts = [t for t in traces if not t.thought.strip()]
        if empty_thoughts:
             reflections.append(MetaReflection(
                id=f"pm-empty-{uuid.uuid4()}",
                timestamp=datetime.now().isoformat(),
                project_id="post-mortem",
                level=ReflectionLevel.REFLECTION,
                scope=ReflectionScope.PATTERN,
                impact=ReflectionImpact.REFACTOR_RECOMMENDED,
                title="Empty Reasoning Steps",
                content=f"Found {len(empty_thoughts)} steps with empty reasoning thoughts.",
                recommendations=["Improve prompt instructions to enforce reasoning before action"]
            ))
            
        # Detect simple repetitions (loops) - consecutive identical actions
        for i in range(1, len(traces)):
            if traces[i].action == traces[i-1].action and traces[i].action.strip():
                reflections.append(MetaReflection(
                    id=f"pm-loop-{uuid.uuid4()}",
                    timestamp=datetime.now().isoformat(),
                    project_id="post-mortem",
                    level=ReflectionLevel.META_REFLECTION,
                    scope=ReflectionScope.PATTERN,
                    impact=ReflectionImpact.CRITICAL,
                    title="Reasoning Loop Detected",
                    content=f"Identical action repeated at step {traces[i].step_id}: {traces[i].action}",
                    recommendations=["Implement loop detection mechanism in agent core", "Increase penalties for repeated actions"]
                ))
                break # Report one loop per session to avoid noise
                
        return reflections