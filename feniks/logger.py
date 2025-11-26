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
Provides consistent logging across all modules with proper formatting and levels.
"""
import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a configured logger instance.

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

        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Prevent propagation to avoid duplicate logs
        logger.propagate = False

    return logger


def setup_logger():
    """
    Legacy function for backwards compatibility.
    Configures and returns a logger for the application.
    """
    return get_logger()


# Create a single, importable instance of the logger for backwards compatibility
log = get_logger()
