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
OpenTelemetry Tracing Infrastructure - Enterprise-grade distributed tracing.
Provides Trace IDs, Spans, and integration with Jaeger/Zipkin.
"""
import contextvars
import functools
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

from feniks.infra.logging import get_logger

log = get_logger("infra.tracing_otel")

# Context variables for storing trace state (fallback)
_trace_id_ctx = contextvars.ContextVar("trace_id", default=None)
_span_id_ctx = contextvars.ContextVar("span_id", default=None)
_project_id_ctx = contextvars.ContextVar("project_id", default=None)

# Global tracer instance
_tracer = None
_tracer_provider = None


def init_tracing(
    service_name: str = "feniks",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    enable_console_export: bool = False,
) -> bool:
    """
    Initialize OpenTelemetry tracing with Jaeger exporter.

    Args:
        service_name: Service name for telemetry
        jaeger_host: Jaeger agent host
        jaeger_port: Jaeger agent port
        enable_console_export: Also export to console (for debugging)

    Returns:
        bool: True if OpenTelemetry was initialized successfully
    """
    global _tracer, _tracer_provider

    if not OTEL_AVAILABLE:
        log.warning("OpenTelemetry not available. Install with: pip install feniks[observability]")
        log.info("Falling back to custom tracing implementation")
        return False

    try:
        # Create resource with service name
        resource = Resource.create({SERVICE_NAME: service_name})

        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)

        # Add Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )
        _tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # Add console exporter for debugging
        if enable_console_export:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter

            console_exporter = ConsoleSpanExporter()
            _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(_tracer_provider)

        # Get tracer
        _tracer = trace.get_tracer(__name__)

        log.info(f"OpenTelemetry tracing initialized: service={service_name}, jaeger={jaeger_host}:{jaeger_port}")
        return True

    except Exception as e:
        log.error(f"Failed to initialize OpenTelemetry: {e}")
        log.info("Falling back to custom tracing implementation")
        return False


def get_tracer(name: str = "feniks"):
    """
    Get OpenTelemetry tracer or fallback tracer.

    Args:
        name: Tracer name

    Returns:
        Tracer instance
    """
    if OTEL_AVAILABLE and _tracer:
        return trace.get_tracer(name)
    return None


def get_trace_id() -> str:
    """Get current trace ID (OpenTelemetry or fallback)."""
    if OTEL_AVAILABLE and trace:
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                trace_id = format(current_span.get_span_context().trace_id, "032x")
                return trace_id
        except Exception:
            pass

    # Fallback to context var
    tid = _trace_id_ctx.get()
    if not tid:
        tid = f"trace-{uuid.uuid4().hex[:8]}"
        _trace_id_ctx.set(tid)
    return tid


def get_span_id() -> Optional[str]:
    """Get current span ID (OpenTelemetry or fallback)."""
    if OTEL_AVAILABLE and trace:
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                span_id = format(current_span.get_span_context().span_id, "016x")
                return span_id
        except Exception:
            pass

    # Fallback to context var
    return _span_id_ctx.get()


def get_project_id() -> Optional[str]:
    """Get current project ID from context."""
    return _project_id_ctx.get()


def set_project_context(project_id: str):
    """Set the project ID for the current context."""
    _project_id_ctx.set(project_id)


@contextmanager
def span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating a tracing span (OpenTelemetry or fallback).

    Args:
        name: Span name
        attributes: Optional span attributes

    Yields:
        Span (OpenTelemetry) or None (fallback)
    """
    # Try OpenTelemetry first
    if OTEL_AVAILABLE and _tracer:
        try:
            with _tracer.start_as_current_span(name, attributes=attributes or {}) as otel_span:
                if attributes:
                    for key, value in attributes.items():
                        otel_span.set_attribute(key, value)
                yield otel_span
                return
        except Exception as e:
            log.warning(f"OpenTelemetry span creation failed: {e}")

    # Fallback to custom implementation
    parent_span = _span_id_ctx.get()
    current_span = f"span-{uuid.uuid4().hex[:8]}"
    trace_id = get_trace_id()

    token = _span_id_ctx.set(current_span)
    start_time = time.time()

    log.info(
        f"SPAN_START: {name}",
        extra={
            "span.name": name,
            "span.id": current_span,
            "span.parent_id": parent_span,
            "trace.id": trace_id,
            **(attributes or {}),
        },
    )

    try:
        yield None
    except Exception as e:
        log.error(f"SPAN_ERROR: {name}", extra={"span.name": name, "span.id": current_span, "error": str(e)})
        raise
    finally:
        duration = time.time() - start_time
        log.info(
            f"SPAN_END: {name}", extra={"span.name": name, "span.id": current_span, "duration_ms": duration * 1000}
        )
        _span_id_ctx.reset(token)


def trace_function(name: Optional[str] = None):
    """
    Decorator to wrap a function in a trace span.

    Args:
        name: Optional span name (defaults to function name)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with span(span_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Backward compatibility aliases
trace = trace_function  # Alias for existing code
