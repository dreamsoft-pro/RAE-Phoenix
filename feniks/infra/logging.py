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
Feniks centralized logging system.
Provides structured JSON logging with Trace ID support.
"""
import datetime
import json
import logging
import sys
from typing import Optional

# Delayed import inside formatting to avoid circular imports if needed,
# or just import trace functions directly.
# Note: get_trace_id depends on contextvars which is safe.
from feniks.infra.tracing import get_project_id, get_span_id, get_trace_id


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings with context information.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
            "span_id": get_span_id(),
            "project_id": get_project_id(),
            "module": record.module,
            "line": record.lineno,
        }

        # Include extra fields passed via 'extra={...}'
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in [
                    "args",
                    "asctime",
                    "created",
                    "exc_info",
                    "exc_text",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "msg",
                    "name",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "thread",
                    "threadName",
                ]:
                    log_record[key] = value

        # Handle exceptions
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a configured logger instance with JSON formatting.

    Args:
        name: Optional name for the logger. If None, returns the root feniks logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger_name = f"feniks.{name}" if name else "feniks"
    logger = logging.getLogger(logger_name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Create JSON formatter
        formatter = JSONFormatter()
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

    return logger


def setup_logger():
    """Legacy compatibility."""
    return get_logger()


# Global instance
log = get_logger()
