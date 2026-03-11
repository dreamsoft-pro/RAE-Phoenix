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
"""Feniks ingest module - handles data ingestion from various indexers."""

from .filters import ChunkFilter, create_default_filter
from .jsonl_loader import generate_stable_id, load_jsonl

__all__ = ["load_jsonl", "generate_stable_id", "ChunkFilter", "create_default_filter"]
