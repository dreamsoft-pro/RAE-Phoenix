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
Metrics Infrastructure - Prometheus-style metrics collection.
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from feniks.infra.logging import get_logger

log = get_logger("infra.metrics")


@dataclass
class Counter:
    name: str
    help_text: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)

    def inc(self, amount: float = 1.0):
        self.value += amount


@dataclass
class Gauge:
    name: str
    help_text: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float):
        self.value = value


class MetricsCollector:
    """
    Central collector for system metrics.
    Mimics Prometheus client structure for easier future migration.
    """

    def __init__(self):
        self.metrics: Dict[str, Any] = {}

        # Initialize standard metrics (Task 12)
        self.cost_total = self._create_counter("feniks_cost_total", "Total cost in USD")
        self.quality_score = self._create_gauge("feniks_quality_score", "Current quality score of the system")
        self.recommendations_count = self._create_counter(
            "feniks_recommendations_count", "Total recommendations generated"
        )

        # Operational metrics
        self.operations_total = self._create_counter("feniks_operations_total", "Total operations count")
        self.errors_total = self._create_counter("feniks_errors_total", "Total errors count")

        self.start_time = time.time()
        log.info("MetricsCollector initialized")

    def _create_counter(self, name: str, help_text: str) -> Counter:
        counter = Counter(name, help_text)
        self.metrics[name] = counter
        return counter

    def _create_gauge(self, name: str, help_text: str) -> Gauge:
        gauge = Gauge(name, help_text)
        self.metrics[name] = gauge
        return gauge

    def inc(self, metric_name: str, amount: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter."""
        if metric_name in self.metrics:
            self.metrics[metric_name].inc(amount)
            if labels:
                self.metrics[metric_name].labels.update(labels)

    def set_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value."""
        if metric_name in self.metrics:
            self.metrics[metric_name].set(value)
            if labels:
                self.metrics[metric_name].labels.update(labels)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics in a serializable format."""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "metrics": {
                k: {"value": v.value, "labels": v.labels, "help": v.help_text} for k, v in self.metrics.items()
            },
            # Backward compatibility for existing calls (e.g. CLI handle_metrics)
            "system": {
                "total_projects": 0,  # Placeholder
                "total_operations": self.operations_total.value,
                "ingests": {"total": 0, "successful": 0, "success_rate": 0, "avg_duration": 0, "total_chunks": 0},
                "analyses": {
                    "total": 0,
                    "successful": 0,
                    "success_rate": 0,
                    "avg_duration": 0,
                    "total_meta_reflections": 0,
                },
                "refactorings": {"total": 0, "successful": 0, "success_rate": 0, "avg_duration": 0, "total_patches": 0},
            },
        }

    def get_project_metrics(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Placeholder for project-specific metrics."""
        return {"ingests": 0, "analyses": 0, "refactorings": 0, "chunks": 0, "meta_reflections": 0, "patches": 0}

    def export_metrics(self, output_path: Path):
        """Export metrics to JSON."""
        data = self.get_metrics()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        log.info(f"Metrics exported to {output_path}")


# Global instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
