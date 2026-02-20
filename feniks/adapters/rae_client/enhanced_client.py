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
Enhanced RAE Client - Bidirectional integration with full read/write capabilities.
Enables cross-project learning and reflection enrichment.
"""
from typing import Any, Dict, List, Optional

from feniks.adapters.rae_client.client import RAEClient, RAEError
from feniks.core.models.types import MetaReflection
from feniks.infra.logging import get_logger

log = get_logger("integrations.enhanced_rae_client")


class EnhancedRAEClient(RAEClient):
    """
    Enhanced RAE client with bidirectional sync and intelligent retrieval.

    Extends the base RAEClient with:
    - Query capabilities for historical data
    - Cross-project pattern recognition
    - Reflection enrichment with global insights
    - Refactoring outcome tracking for learning loops
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize enhanced RAE client.

        Args:
            base_url: RAE base URL (defaults to settings)
            api_key: RAE API key (defaults to settings)
            tenant_id: Tenant ID for multi-tenancy support
            timeout: Request timeout in seconds
        """
        super().__init__(base_url=base_url, api_key=api_key, timeout=timeout)
        self.tenant_id = tenant_id or "default-tenant"
        log.info(f"EnhancedRAEClient initialized with tenant_id={self.tenant_id}")

    def query_reflections(
        self,
        project_id: str,
        query_text: str,
        layer: str = "semantic",
        top_k: int = 10,
        min_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Query RAE for relevant reflections using semantic search.

        Args:
            project_id: Project identifier
            query_text: Natural language query
            layer: Memory layer to search (episodic, working, semantic, ltm)
            top_k: Maximum number of results
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            List[Dict[str, Any]]: List of relevant reflections with similarity scores

        Raises:
            RAEError: If query fails
        """
        log.info(f"Querying RAE reflections: project={project_id}, layer={layer}, query='{query_text[:50]}...'")

        try:
            payload = {
                "project_id": project_id,
                "tenant_id": self.tenant_id,
                "query": query_text,
                "layer": layer,
                "top_k": top_k,
                "min_similarity": min_similarity,
                "include_metadata": True,
            }

            response = self._make_request(method="POST", endpoint="/memory/query", data=payload)

            results = response.get("results", [])
            log.info(f"Found {len(results)} relevant reflections")
            return results

        except Exception as e:
            raise RAEError(f"Failed to query reflections: {e}") from e

    def get_cross_project_patterns(
        self,
        pattern_type: str,
        min_confidence: float = 0.7,
        limit: int = 20,
        exclude_projects: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cross-project patterns from RAE semantic memory.

        Useful for learning best practices, common anti-patterns, and
        successful refactoring strategies from other projects.

        Args:
            pattern_type: Type of pattern (refactoring, architecture, anti-pattern, best-practice)
            min_confidence: Minimum confidence score (0.0-1.0)
            limit: Maximum number of patterns to return
            exclude_projects: Optional list of project IDs to exclude

        Returns:
            List[Dict[str, Any]]: List of cross-project patterns with metadata

        Raises:
            RAEError: If retrieval fails
        """
        log.info(f"Retrieving cross-project patterns: type={pattern_type}, min_confidence={min_confidence}")

        try:
            payload = {
                "tenant_id": self.tenant_id,
                "pattern_type": pattern_type,
                "min_confidence": min_confidence,
                "limit": limit,
                "exclude_projects": exclude_projects or [],
                "aggregate": True,
            }

            response = self._make_request(method="POST", endpoint="/memory/patterns/cross-project", data=payload)

            patterns = response.get("patterns", [])
            log.info(f"Retrieved {len(patterns)} cross-project patterns")
            return patterns

        except Exception as e:
            raise RAEError(f"Failed to get cross-project patterns: {e}") from e

    def get_historical_refactorings(
        self,
        refactor_type: str,
        project_tags: Optional[List[str]] = None,
        min_success_rate: float = 0.6,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get historical refactoring decisions and outcomes from RAE.

        Enables learning from past refactorings across all projects.

        Args:
            refactor_type: Type of refactoring (extract-method, rename, move-class, etc.)
            project_tags: Optional tags to filter projects (python, typescript, microservice, etc.)
            min_success_rate: Minimum success rate threshold
            limit: Maximum number of results

        Returns:
            List[Dict[str, Any]]: Historical refactorings with outcomes

        Raises:
            RAEError: If retrieval fails
        """
        log.info(f"Retrieving historical refactorings: type={refactor_type}, tags={project_tags}")

        try:
            payload = {
                "tenant_id": self.tenant_id,
                "refactor_type": refactor_type,
                "project_tags": project_tags or [],
                "min_success_rate": min_success_rate,
                "limit": limit,
                "include_outcomes": True,
            }

            response = self._make_request(method="POST", endpoint="/memory/refactorings/historical", data=payload)

            refactorings = response.get("refactorings", [])
            log.info(f"Retrieved {len(refactorings)} historical refactorings")
            return refactorings

        except Exception as e:
            raise RAEError(f"Failed to get historical refactorings: {e}") from e

    def enrich_reflection(
        self, local_reflection: MetaReflection, context: Optional[Dict[str, Any]] = None
    ) -> MetaReflection:
        """
        Enrich local Feniks reflection with RAE insights.

        This is the key method for synergy - takes a local reflection
        and enhances it with global knowledge from RAE.

        Args:
            local_reflection: MetaReflection from Feniks MetaReflectionEngine
            context: Optional additional context (project_id, tags, etc.)

        Returns:
            MetaReflection: Enriched reflection with RAE insights

        Raises:
            RAEError: If enrichment fails
        """
        log.info(f"Enriching reflection: {local_reflection.id}")

        try:
            # Build enrichment query from reflection content
            query_text = self._build_enrichment_query(local_reflection)

            # Query RAE for relevant insights
            rae_insights = self.query_reflections(
                project_id=context.get("project_id", "default") if context else "default",
                query_text=query_text,
                layer="semantic",
                top_k=5,
                min_similarity=0.7,
            )

            # If this is a refactoring-related reflection, get historical patterns
            refactor_insights = []
            # Check if reflection is about refactoring (in content, title, or tags)
            is_refactor = any(
                "refactor" in str(field).lower()
                for field in [local_reflection.content, local_reflection.title, local_reflection.tags]
            )
            if is_refactor:
                refactor_type = self._extract_refactor_type(local_reflection)
                if refactor_type:
                    refactor_insights = self.get_historical_refactorings(
                        refactor_type=refactor_type, project_tags=context.get("tags") if context else None, limit=10
                    )

            # Enrich the reflection with RAE insights
            enriched_reflection = self._merge_insights(local_reflection, rae_insights, refactor_insights)

            log.info(
                f"Reflection enriched: {len(rae_insights)} semantic insights, "
                f"{len(refactor_insights)} refactor insights"
            )
            return enriched_reflection

        except Exception as e:
            log.warning(f"Failed to enrich reflection, returning original: {e}")
            return local_reflection

    def store_refactor_outcome(self, refactor_decision: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store refactoring outcome for learning - creates feedback loop.

        This enables RAE to learn from Feniks refactorings and improve
        future recommendations.

        Args:
            refactor_decision: Original refactoring decision with metadata
            outcome: Outcome data (success, metrics, issues)

        Returns:
            Dict[str, Any]: Storage confirmation

        Raises:
            RAEError: If storage fails
        """
        log.info(f"Storing refactor outcome: {refactor_decision.get('refactor_id')}")

        try:
            payload = {
                "tenant_id": self.tenant_id,
                "project_id": refactor_decision.get("project_id", "default"),
                "refactor_id": refactor_decision.get("refactor_id"),
                "refactor_type": refactor_decision.get("refactor_type"),
                "decision": refactor_decision,
                "outcome": {
                    "success": outcome.get("success", False),
                    "timestamp": outcome.get("timestamp"),
                    "metrics": outcome.get("metrics", {}),
                    "issues": outcome.get("issues", []),
                    "rollback_required": outcome.get("rollback_required", False),
                },
                "learning_signals": {
                    "improve_confidence": outcome.get("success", False),
                    "pattern_validity": outcome.get("pattern_match", True),
                    "context_relevance": outcome.get("context_score", 0.5),
                },
            }

            response = self._make_request(method="POST", endpoint="/memory/refactorings/outcome", data=payload)

            log.info(f"Refactor outcome stored successfully: {refactor_decision.get('refactor_id')}")
            return response

        except Exception as e:
            raise RAEError(f"Failed to store refactor outcome: {e}") from e

    def batch_enrich_reflections(
        self, reflections: List[MetaReflection], context: Optional[Dict[str, Any]] = None
    ) -> List[MetaReflection]:
        """
        Enrich multiple reflections in a single batch operation.

        More efficient than calling enrich_reflection() multiple times.

        Args:
            reflections: List of MetaReflections to enrich
            context: Optional context shared by all reflections

        Returns:
            List[MetaReflection]: Enriched reflections
        """
        log.info(f"Batch enriching {len(reflections)} reflections")

        enriched = []
        for reflection in reflections:
            try:
                enriched.append(self.enrich_reflection(reflection, context))
            except Exception as e:
                log.warning(f"Failed to enrich reflection {reflection.id}: {e}")
                enriched.append(reflection)

        log.info(f"Batch enrichment complete: {len(enriched)}/{len(reflections)} successful")
        return enriched

    # Private helper methods

    def _build_enrichment_query(self, reflection: MetaReflection) -> str:
        """Build semantic query from reflection for RAE search."""
        components = []

        # Use scope instead of insight_type
        if reflection.scope:
            components.append(f"Scope: {reflection.scope.value}")

        # Use title and content instead of summary
        if reflection.title:
            components.append(reflection.title)

        if reflection.content:
            # Take first 200 chars of content
            components.append(reflection.content[:200])

        if reflection.recommendations:
            components.append(f"Context: {' '.join(reflection.recommendations[:2])}")

        return " | ".join(components)

    def _extract_refactor_type(self, reflection: MetaReflection) -> Optional[str]:
        """Extract refactor type from reflection metadata."""
        if not hasattr(reflection, "metadata") or not reflection.metadata:
            return None

        return reflection.metadata.get("refactor_type")

    def _merge_insights(
        self, local_reflection: MetaReflection, rae_insights: List[Dict], refactor_insights: List[Dict]
    ) -> MetaReflection:
        """
        Merge RAE insights into local reflection.

        Creates an enriched copy with additional metadata and recommendations.
        """
        from copy import deepcopy

        # Create enriched copy with correct MetaReflection structure
        enriched = MetaReflection(
            id=local_reflection.id,
            timestamp=local_reflection.timestamp,
            project_id=local_reflection.project_id,
            level=local_reflection.level,
            scope=local_reflection.scope,
            impact=local_reflection.impact,
            title=local_reflection.title,
            content=local_reflection.content,
            evidence=deepcopy(local_reflection.evidence),
            related_modules=list(local_reflection.related_modules),
            related_files=list(local_reflection.related_files),
            recommendations=list(local_reflection.recommendations),
            origin=local_reflection.origin,
            tags=list(local_reflection.tags),
            confidence=local_reflection.confidence,
            metadata=deepcopy(local_reflection.metadata),
        )

        # Add RAE insights to metadata
        enriched.metadata["rae_enriched"] = True
        enriched.metadata["rae_insights_count"] = len(rae_insights)
        enriched.metadata["refactor_insights_count"] = len(refactor_insights)

        # Extract top insights and add to recommendations
        if rae_insights:
            top_insights = [
                insight.get("content", {}).get("summary", "")
                for insight in rae_insights[:3]
                if insight.get("similarity_score", 0) > 0.8
            ]
            if top_insights:
                enriched.recommendations.extend([f"[RAE] {insight}" for insight in top_insights])

        # Add refactoring patterns if available
        if refactor_insights:
            patterns = [
                f"Pattern: {r.get('pattern_name')} (success rate: {r.get('success_rate', 0):.0%})"
                for r in refactor_insights[:2]
            ]
            if patterns:
                enriched.recommendations.extend([f"[Historical] {p}" for p in patterns])

        return enriched


def create_enhanced_rae_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Optional[EnhancedRAEClient]:
    """
    Factory function to create enhanced RAE client.

    Returns:
        Optional[EnhancedRAEClient]: Enhanced client instance or None if disabled
    """
    from feniks.config.settings import settings

    if not settings.rae_enabled:
        log.debug("RAE integration is disabled")
        return None

    try:
        client = EnhancedRAEClient(
            base_url=base_url or settings.rae_base_url,
            api_key=api_key or settings.rae_api_key,
            tenant_id=tenant_id or getattr(settings, "rae_tenant_id", "default-tenant"),
            timeout=getattr(settings, "rae_timeout", 30),
        )
        return client
    except RAEError as e:
        log.warning(f"Failed to create enhanced RAE client: {e}")
        return None
