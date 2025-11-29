from typing import Any, Dict

from feniks.infra.logging import get_logger
from feniks.infra.metrics import get_metrics_collector

log = get_logger("observability")


class ObservabilityFacade:
    """
    Unified facade for Logging, Tracing, and Metrics.
    Acts as the single point of entry for observability concerns.
    """

    def __init__(self):
        self.metrics = get_metrics_collector()

    def record_event(self, event_name: str, attributes: Dict[str, Any] = None):
        """Record a business event."""
        log.info(f"Event: {event_name}", extra=attributes)
        self.metrics.inc(f"event_{event_name}")

    def start_trace(self, trace_name: str):
        """Start a distributed trace (stub)."""
        log.debug(f"Starting trace: {trace_name}")
        # Real impl would return a span context

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric."""
        # Simplified for this implementation
        log.debug(f"Metric {name}: {value}")
