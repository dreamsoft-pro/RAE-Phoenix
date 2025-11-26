"""
Metrics Collector - Collects and exposes metrics for monitoring.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import time

from feniks.logger import get_logger

log = get_logger("observability.metrics")


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""
    operation_type: str  # ingest, analyze, refactor
    project_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark operation as complete."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error


@dataclass
class SystemMetrics:
    """Aggregated system metrics."""
    total_projects: int = 0
    total_ingests: int = 0
    total_analyses: int = 0
    total_refactorings: int = 0

    # Success rates
    successful_ingests: int = 0
    successful_analyses: int = 0
    successful_refactorings: int = 0

    # Timing stats
    avg_ingest_duration: float = 0.0
    avg_analysis_duration: float = 0.0
    avg_refactor_duration: float = 0.0

    # Volume stats
    total_chunks_ingested: int = 0
    total_meta_reflections: int = 0
    total_patches_generated: int = 0

    # Per-project stats
    projects: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and aggregates metrics for enterprise monitoring.

    Tracks:
    - Operation counts (ingest, analyze, refactor)
    - Timing statistics
    - Success/failure rates
    - Volume metrics (chunks, reflections, patches)
    - Per-project breakdowns
    """

    _instance: Optional['MetricsCollector'] = None

    def __init__(self):
        """Initialize metrics collector."""
        self.operations: list[OperationMetrics] = []
        self.system_metrics = SystemMetrics()
        self.start_time = time.time()
        log.info("MetricsCollector initialized")

    @classmethod
    def get_instance(cls) -> 'MetricsCollector':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_operation(
        self,
        operation_type: str,
        project_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OperationMetrics:
        """
        Start tracking an operation.

        Args:
            operation_type: Type of operation (ingest, analyze, refactor)
            project_id: Project identifier
            metadata: Additional metadata

        Returns:
            OperationMetrics instance
        """
        op = OperationMetrics(
            operation_type=operation_type,
            project_id=project_id,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self.operations.append(op)
        log.debug(f"Started operation: {operation_type} for project {project_id}")
        return op

    def complete_operation(
        self,
        operation: OperationMetrics,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Mark operation as complete and update metrics.

        Args:
            operation: The operation metrics
            success: Whether operation succeeded
            error: Error message if failed
            metadata: Additional metadata to merge
        """
        operation.complete(success, error)

        if metadata:
            operation.metadata.update(metadata)

        # Update aggregated metrics
        self._update_aggregates(operation)

        log.debug(
            f"Completed operation: {operation.operation_type} "
            f"({operation.duration:.2f}s, success={success})"
        )

    def _update_aggregates(self, operation: OperationMetrics):
        """Update aggregated metrics based on completed operation."""
        op_type = operation.operation_type
        project_id = operation.project_id

        # Ensure project exists in metrics
        if project_id not in self.system_metrics.projects:
            self.system_metrics.total_projects += 1
            self.system_metrics.projects[project_id] = {
                "ingests": 0,
                "analyses": 0,
                "refactorings": 0,
                "chunks": 0,
                "meta_reflections": 0,
                "patches": 0
            }

        project_metrics = self.system_metrics.projects[project_id]

        # Update counts
        if op_type == "ingest":
            self.system_metrics.total_ingests += 1
            project_metrics["ingests"] += 1
            if operation.success:
                self.system_metrics.successful_ingests += 1

            # Update timing
            if operation.duration:
                total = self.system_metrics.avg_ingest_duration * (self.system_metrics.total_ingests - 1)
                self.system_metrics.avg_ingest_duration = (total + operation.duration) / self.system_metrics.total_ingests

            # Volume stats
            if "chunks_ingested" in operation.metadata:
                chunks = operation.metadata["chunks_ingested"]
                self.system_metrics.total_chunks_ingested += chunks
                project_metrics["chunks"] += chunks

        elif op_type == "analyze":
            self.system_metrics.total_analyses += 1
            project_metrics["analyses"] += 1
            if operation.success:
                self.system_metrics.successful_analyses += 1

            # Update timing
            if operation.duration:
                total = self.system_metrics.avg_analysis_duration * (self.system_metrics.total_analyses - 1)
                self.system_metrics.avg_analysis_duration = (total + operation.duration) / self.system_metrics.total_analyses

            # Volume stats
            if "meta_reflections" in operation.metadata:
                count = operation.metadata["meta_reflections"]
                self.system_metrics.total_meta_reflections += count
                project_metrics["meta_reflections"] += count

        elif op_type == "refactor":
            self.system_metrics.total_refactorings += 1
            project_metrics["refactorings"] += 1
            if operation.success:
                self.system_metrics.successful_refactorings += 1

            # Update timing
            if operation.duration:
                total = self.system_metrics.avg_refactor_duration * (self.system_metrics.total_refactorings - 1)
                self.system_metrics.avg_refactor_duration = (total + operation.duration) / self.system_metrics.total_refactorings

            # Volume stats
            if "patches_generated" in operation.metadata:
                count = operation.metadata["patches_generated"]
                self.system_metrics.total_patches_generated += count
                project_metrics["patches"] += count

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.

        Returns:
            Dict with all metrics
        """
        uptime = time.time() - self.start_time

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "system": {
                "total_projects": self.system_metrics.total_projects,
                "total_operations": len(self.operations),
                "ingests": {
                    "total": self.system_metrics.total_ingests,
                    "successful": self.system_metrics.successful_ingests,
                    "success_rate": self._success_rate(
                        self.system_metrics.successful_ingests,
                        self.system_metrics.total_ingests
                    ),
                    "avg_duration": self.system_metrics.avg_ingest_duration,
                    "total_chunks": self.system_metrics.total_chunks_ingested
                },
                "analyses": {
                    "total": self.system_metrics.total_analyses,
                    "successful": self.system_metrics.successful_analyses,
                    "success_rate": self._success_rate(
                        self.system_metrics.successful_analyses,
                        self.system_metrics.total_analyses
                    ),
                    "avg_duration": self.system_metrics.avg_analysis_duration,
                    "total_meta_reflections": self.system_metrics.total_meta_reflections
                },
                "refactorings": {
                    "total": self.system_metrics.total_refactorings,
                    "successful": self.system_metrics.successful_refactorings,
                    "success_rate": self._success_rate(
                        self.system_metrics.successful_refactorings,
                        self.system_metrics.total_refactorings
                    ),
                    "avg_duration": self.system_metrics.avg_refactor_duration,
                    "total_patches": self.system_metrics.total_patches_generated
                }
            },
            "projects": self.system_metrics.projects
        }

    def _success_rate(self, successful: int, total: int) -> float:
        """Calculate success rate."""
        return (successful / total * 100) if total > 0 else 0.0

    def export_metrics(self, output_path: Path):
        """
        Export metrics to JSON file.

        Args:
            output_path: Path to export metrics
        """
        metrics = self.get_metrics()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        log.info(f"Metrics exported to {output_path}")

    def get_project_metrics(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific project.

        Args:
            project_id: Project identifier

        Returns:
            Project metrics or None
        """
        return self.system_metrics.projects.get(project_id)

    def reset_metrics(self):
        """Reset all metrics (for testing)."""
        self.operations.clear()
        self.system_metrics = SystemMetrics()
        self.start_time = time.time()
        log.info("Metrics reset")


# Global instance accessor
def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return MetricsCollector.get_instance()
