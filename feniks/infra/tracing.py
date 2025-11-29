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
Tracing Infrastructure - Lightweight tracing context management.
Provides Trace IDs and Spans for operations.
"""
import contextvars
import functools
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

# Context variables for storing trace state
_trace_id_ctx = contextvars.ContextVar("trace_id", default=None)
_span_id_ctx = contextvars.ContextVar("span_id", default=None)
_project_id_ctx = contextvars.ContextVar("project_id", default=None)


def get_trace_id() -> str:
    """Get current trace ID or generate a new one if none exists."""
    tid = _trace_id_ctx.get()
    if not tid:
        tid = f"trace-{uuid.uuid4().hex[:8]}"
        _trace_id_ctx.set(tid)
    return tid


def get_span_id() -> Optional[str]:
    """Get current span ID."""
    return _span_id_ctx.get()


def get_project_id() -> Optional[str]:
    """Get current project ID."""
    return _project_id_ctx.get()


def set_project_context(project_id: str):
    """Set the project ID for the current context."""
    _project_id_ctx.set(project_id)


@contextmanager
def span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for a tracing span.
    """
    from feniks.infra.logging import get_logger  # Delayed import to avoid circular dep

    log = get_logger("infra.tracing")

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
        yield
    except Exception as e:
        log.error(f"SPAN_ERROR: {name}", extra={"span.name": name, "span.id": current_span, "error": str(e)})
        raise
    finally:
        duration = time.time() - start_time
        log.info(
            f"SPAN_END: {name}", extra={"span.name": name, "span.id": current_span, "duration_ms": duration * 1000}
        )
        _span_id_ctx.reset(token)


def trace(name: Optional[str] = None):
    """
    Decorator to wrap a function in a trace span.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with span(span_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
