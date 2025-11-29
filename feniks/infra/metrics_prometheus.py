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
Prometheus Metrics Infrastructure - Enterprise-grade metrics collection.
"""
import time
from typing import Optional

try:
    from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Gauge = Histogram = None

from feniks.infra.logging import get_logger

log = get_logger("infra.metrics_prometheus")


class PrometheusMetricsCollector:
    """
    Prometheus-based metrics collector.

    Provides standard Prometheus metrics for Feniks operations:
    - Counters: feniks_cost_total, feniks_recommendations_count, feniks_operations_total
    - Gauges: feniks_quality_score
    - Histograms: feniks_operation_duration_seconds
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus metrics collector.

        Args:
            registry: Optional custom registry (defaults to global REGISTRY)
        """
        if not PROMETHEUS_AVAILABLE:
            log.warning("prometheus-client not available. Install with: pip install feniks[observability]")
            log.info("Metrics collection disabled")
            self.enabled = False
            return

        self.enabled = True
        self.registry = registry or REGISTRY
        self.start_time = time.time()

        # Define metrics (Task 12 from plan)
        try:
            self.cost_total = Counter(
                "feniks_cost_total",
                "Total cost in USD for all operations",
                ["project_id", "operation"],
                registry=self.registry,
            )

            self.quality_score = Gauge(
                "feniks_quality_score",
                "Current quality score of the system (0.0 - 1.0)",
                ["project_id"],
                registry=self.registry,
            )

            self.recommendations_count = Counter(
                "feniks_recommendations_count",
                "Total number of recommendations generated",
                ["project_id", "severity"],
                registry=self.registry,
            )

            self.operations_total = Counter(
                "feniks_operations_total",
                "Total number of operations executed",
                ["operation", "status"],
                registry=self.registry,
            )

            self.errors_total = Counter(
                "feniks_errors_total", "Total number of errors encountered", ["error_type"], registry=self.registry
            )

            self.operation_duration = Histogram(
                "feniks_operation_duration_seconds",
                "Duration of operations in seconds",
                ["operation"],
                registry=self.registry,
            )

            # Uptime gauge
            self.uptime = Gauge(
                "feniks_uptime_seconds", "Uptime of the Feniks service in seconds", registry=self.registry
            )

            log.info("PrometheusMetricsCollector initialized successfully")

        except Exception as e:
            log.error(f"Failed to initialize Prometheus metrics: {e}")
            self.enabled = False

    def inc_cost(self, cost_usd: float, project_id: str = "default", operation: str = "general"):
        """Increment total cost."""
        if self.enabled:
            self.cost_total.labels(project_id=project_id, operation=operation).inc(cost_usd)

    def set_quality_score(self, score: float, project_id: str = "default"):
        """Set current quality score (0.0 - 1.0)."""
        if self.enabled:
            self.quality_score.labels(project_id=project_id).set(score)

    def inc_recommendations(self, count: int = 1, project_id: str = "default", severity: str = "info"):
        """Increment recommendations count."""
        if self.enabled:
            self.recommendations_count.labels(project_id=project_id, severity=severity).inc(count)

    def inc_operations(self, operation: str, status: str = "success"):
        """Increment operations count."""
        if self.enabled:
            self.operations_total.labels(operation=operation, status=status).inc()

    def inc_errors(self, error_type: str = "unknown"):
        """Increment errors count."""
        if self.enabled:
            self.errors_total.labels(error_type=error_type).inc()

    def observe_duration(self, operation: str, duration_seconds: float):
        """Record operation duration."""
        if self.enabled:
            self.operation_duration.labels(operation=operation).observe(duration_seconds)

    def update_uptime(self):
        """Update uptime gauge."""
        if self.enabled:
            uptime_seconds = time.time() - self.start_time
            self.uptime.set(uptime_seconds)

    def export_prometheus(self) -> bytes:
        """
        Export metrics in Prometheus text format.

        Returns:
            bytes: Prometheus-formatted metrics
        """
        if not self.enabled:
            return b"# Prometheus metrics not available\n"

        try:
            self.update_uptime()
            return generate_latest(self.registry)
        except Exception as e:
            log.error(f"Failed to generate Prometheus metrics: {e}")
            return b"# Error generating metrics\n"


# Global instance
_prometheus_collector: Optional[PrometheusMetricsCollector] = None


def get_prometheus_collector(registry: Optional[CollectorRegistry] = None) -> PrometheusMetricsCollector:
    """
    Get global Prometheus metrics collector instance.

    Args:
        registry: Optional custom registry

    Returns:
        PrometheusMetricsCollector: Global instance
    """
    global _prometheus_collector
    if _prometheus_collector is None:
        _prometheus_collector = PrometheusMetricsCollector(registry=registry)
    return _prometheus_collector
