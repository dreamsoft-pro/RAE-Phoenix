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
Filtering utilities for ingested chunks.
Supports include/exclude patterns for files and directories.
"""
import re
from pathlib import Path
from typing import List, Optional

from feniks.core.models.types import Chunk
from feniks.infra.logging import get_logger

log = get_logger("ingest.filters")


class ChunkFilter:
    """
    Filter for chunks based on file patterns and other criteria.
    """

    def __init__(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        min_complexity: int = 0,
        max_complexity: Optional[int] = None,
    ):
        """
        Initialize chunk filter.

        Args:
            include_patterns: Glob-like patterns to include (e.g., ["*.js", "src/**"])
            exclude_patterns: Glob-like patterns to exclude (e.g., ["*.test.js", "*.spec.js"])
            exclude_dirs: Directory names to exclude (e.g., ["node_modules", "vendor", "test"])
            min_complexity: Minimum cyclomatic complexity to include
            max_complexity: Maximum cyclomatic complexity to include
        """
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or ["**/node_modules/**", "**/vendor/**", "**/.git/**"]
        self.exclude_dirs = set(exclude_dirs or ["node_modules", "vendor", ".git", "dist", "build"])
        self.min_complexity = min_complexity
        self.max_complexity = max_complexity

        # Convert glob patterns to regex
        self.include_regexes = [self._glob_to_regex(p) for p in self.include_patterns]
        self.exclude_regexes = [self._glob_to_regex(p) for p in self.exclude_patterns]

        log.info(
            f"ChunkFilter initialized with {len(self.include_patterns)} include patterns, "
            f"{len(self.exclude_patterns)} exclude patterns"
        )

    @staticmethod
    def _glob_to_regex(pattern: str) -> re.Pattern:
        """Convert a glob pattern to a regex pattern."""
        # Replace glob wildcards with regex equivalents
        regex_pattern = pattern.replace(".", r"\.")
        regex_pattern = regex_pattern.replace("*", "[^/]*")
        regex_pattern = regex_pattern.replace("?", ".")
        regex_pattern = regex_pattern.replace("/**/", "/(.*/)?")
        regex_pattern = "^" + regex_pattern + "$"
        return re.compile(regex_pattern)

    def _matches_pattern(self, path: str, regexes: List[re.Pattern]) -> bool:
        """Check if path matches any of the regex patterns."""
        if not regexes:
            return False
        return any(regex.match(path) for regex in regexes)

    def _is_in_excluded_dir(self, path: str) -> bool:
        """Check if path is within an excluded directory."""
        path_parts = Path(path).parts
        return any(excluded_dir in path_parts for excluded_dir in self.exclude_dirs)

    def should_include(self, chunk: Chunk) -> bool:
        """
        Determine if a chunk should be included based on filter criteria.

        Args:
            chunk: The chunk to evaluate

        Returns:
            bool: True if chunk should be included, False otherwise
        """
        # Check directory exclusions
        if self._is_in_excluded_dir(chunk.file_path):
            log.debug(f"Excluding {chunk.file_path}: in excluded directory")
            return False

        # Check exclude patterns
        if self._matches_pattern(chunk.file_path, self.exclude_regexes):
            log.debug(f"Excluding {chunk.file_path}: matches exclude pattern")
            return False

        # Check include patterns (if specified)
        if self.include_regexes and not self._matches_pattern(chunk.file_path, self.include_regexes):
            log.debug(f"Excluding {chunk.file_path}: doesn't match include pattern")
            return False

        # Check complexity bounds
        complexity = chunk.cyclomatic_complexity
        if complexity < self.min_complexity:
            log.debug(f"Excluding {chunk.chunk_name}: complexity {complexity} < {self.min_complexity}")
            return False

        if self.max_complexity is not None and complexity > self.max_complexity:
            log.debug(f"Excluding {chunk.chunk_name}: complexity {complexity} > {self.max_complexity}")
            return False

        return True

    def filter_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Filter a list of chunks based on criteria.

        Args:
            chunks: List of chunks to filter

        Returns:
            List[Chunk]: Filtered list of chunks
        """
        filtered = [chunk for chunk in chunks if self.should_include(chunk)]

        excluded_count = len(chunks) - len(filtered)
        if excluded_count > 0:
            log.info(f"Filtered out {excluded_count} chunks, {len(filtered)} remaining")

        return filtered


def create_default_filter() -> ChunkFilter:
    """
    Create a default filter with sensible exclusions.

    Returns:
        ChunkFilter: Filter with default settings
    """
    return ChunkFilter(
        exclude_patterns=[
            "**/node_modules/**",
            "**/vendor/**",
            "**/.git/**",
            "**/dist/**",
            "**/build/**",
            "**/*.test.js",
            "**/*.spec.js",
            "**/*.min.js",
        ],
        exclude_dirs=["node_modules", "vendor", ".git", "dist", "build", "__pycache__"],
    )
