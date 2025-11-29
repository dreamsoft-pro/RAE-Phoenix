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
Feniks custom exceptions for domain-level error handling.
"""


class FeniksError(Exception):
    """Base exception for all Feniks errors."""

    pass


class FeniksConfigError(FeniksError):
    """Raised when there's an issue with Feniks configuration."""

    pass


class FeniksIngestError(FeniksError):
    """Raised when there's an issue during data ingestion."""

    pass


class FeniksStoreError(FeniksError):
    """Raised when there's an issue with the storage backend (e.g., Qdrant)."""

    pass


class FeniksPluginError(FeniksError):
    """Raised when there's an issue with a language plugin."""

    pass
