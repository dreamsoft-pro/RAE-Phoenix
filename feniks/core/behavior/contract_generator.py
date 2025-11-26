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
Contract Generator - Derives behavior contracts from observed snapshots.

Analyzes legacy system snapshots to automatically generate behavioral contracts
for regression testing without traditional test suites.
"""
import uuid
import statistics
from typing import List, Optional, Set
from datetime import datetime
from collections import Counter

from feniks.infra.logging import get_logger
from feniks.core.models.behavior import (
    BehaviorSnapshot,
    BehaviorContract,
    HTTPSuccessCriteria,
    CLISuccessCriteria,
    DOMSuccessCriteria,
    LogSuccessCriteria,
    SuccessCriteria
)
from feniks.exceptions import FeniksError

log = get_logger("core.behavior.contract_generator")


class ContractGenerator:
    """
    Generates behavior contracts from observed snapshots.

    Uses statistical analysis and pattern detection to derive:
    - Expected status codes, exit codes
    - Response time thresholds (percentiles)
    - Common JSON paths and DOM selectors
    - Log patterns and error markers
    """

    def __init__(
        self,
        min_snapshots: int = 3,
        confidence_threshold: float = 0.8,
        percentile: int = 95
    ):
        """
        Initialize contract generator.

        Args:
            min_snapshots: Minimum snapshots required to generate contract
            confidence_threshold: Minimum frequency for pattern inclusion (0.0-1.0)
            percentile: Percentile for duration thresholds (e.g., 95 = p95)
        """
        self.min_snapshots = min_snapshots
        self.confidence_threshold = confidence_threshold
        self.percentile = percentile
        log.info(f"ContractGenerator initialized (min_snapshots={min_snapshots}, confidence={confidence_threshold}, p{percentile})")

    def generate_contract(
        self,
        snapshots: List[BehaviorSnapshot],
        contract_id: Optional[str] = None,
        version: str = "1.0.0"
    ) -> BehaviorContract:
        """
        Generate behavior contract from snapshots.

        Args:
            snapshots: List of behavior snapshots (from legacy environment)
            contract_id: Optional contract ID (generated if not provided)
            version: Contract version

        Returns:
            BehaviorContract derived from snapshot analysis

        Raises:
            FeniksError: If insufficient snapshots or inconsistent data
        """
        if len(snapshots) < self.min_snapshots:
            raise FeniksError(
                f"Insufficient snapshots: {len(snapshots)} < {self.min_snapshots}. "
                f"Need at least {self.min_snapshots} snapshots to generate reliable contract."
            )

        # Validate all snapshots are from same scenario
        scenario_ids = {s.scenario_id for s in snapshots}
        if len(scenario_ids) > 1:
            raise FeniksError(f"Snapshots from multiple scenarios: {scenario_ids}")

        scenario_id = snapshots[0].scenario_id
        project_id = snapshots[0].project_id

        log.info(f"Generating contract from {len(snapshots)} snapshots (scenario={scenario_id})")

        # Derive success criteria
        success_criteria = self._derive_success_criteria(snapshots)

        # Calculate duration threshold
        durations = [s.duration_ms for s in snapshots if s.duration_ms]
        max_duration_ms = None
        if durations:
            max_duration_ms = int(self._calculate_percentile(durations, self.percentile))
            log.debug(f"Duration threshold (p{self.percentile}): {max_duration_ms}ms")

        # Create contract
        contract = BehaviorContract(
            id=contract_id or f"contract-{scenario_id}-{uuid.uuid4().hex[:8]}",
            scenario_id=scenario_id,
            project_id=project_id,
            version=version,
            success_criteria=success_criteria,
            max_duration_ms=max_duration_ms,
            created_at=datetime.now(),
            created_from_snapshots=len(snapshots),
            confidence_score=self._calculate_confidence_score(snapshots)
        )

        log.info(f"Contract generated: {contract.id} (confidence={contract.confidence_score:.2f})")
        return contract

    def _derive_success_criteria(self, snapshots: List[BehaviorSnapshot]) -> SuccessCriteria:
        """Derive success criteria from snapshots."""
        criteria = SuccessCriteria()

        # HTTP criteria
        http_snapshots = [s for s in snapshots if s.observed_http]
        if http_snapshots:
            criteria.http = self._derive_http_criteria(http_snapshots)

        # CLI criteria
        cli_snapshots = [s for s in snapshots if s.observed_cli]
        if cli_snapshots:
            criteria.cli = self._derive_cli_criteria(cli_snapshots)

        # DOM criteria
        dom_snapshots = [s for s in snapshots if s.observed_dom]
        if dom_snapshots:
            criteria.dom = self._derive_dom_criteria(dom_snapshots)

        # Log criteria
        log_snapshots = [s for s in snapshots if s.observed_logs]
        if log_snapshots:
            criteria.logs = self._derive_log_criteria(log_snapshots)

        return criteria

    def _derive_http_criteria(self, snapshots: List[BehaviorSnapshot]) -> HTTPSuccessCriteria:
        """Derive HTTP success criteria."""
        # Collect status codes
        status_codes = [s.observed_http.status_code for s in snapshots]
        status_counter = Counter(status_codes)

        # Include status codes above confidence threshold
        total = len(status_codes)
        expected_status_codes = [
            code for code, count in status_counter.items()
            if count / total >= self.confidence_threshold
        ]

        # If no codes meet threshold, take most common
        if not expected_status_codes:
            expected_status_codes = [status_counter.most_common(1)[0][0]]

        log.debug(f"HTTP expected status codes: {expected_status_codes} (from {status_counter})")

        # Extract common JSON paths
        json_paths = self._extract_common_json_paths(snapshots)

        return HTTPSuccessCriteria(
            expected_status_codes=expected_status_codes,
            forbidden_status_codes=[],  # User can customize
            must_contain_json_paths=json_paths,
            must_not_contain_json_paths=[],
            must_contain_header_patterns=[],
            must_not_contain_header_patterns=[]
        )

    def _derive_cli_criteria(self, snapshots: List[BehaviorSnapshot]) -> CLISuccessCriteria:
        """Derive CLI success criteria."""
        # Collect exit codes
        exit_codes = [s.observed_cli.exit_code for s in snapshots]
        exit_counter = Counter(exit_codes)

        # Include exit codes above confidence threshold
        total = len(exit_codes)
        expected_exit_codes = [
            code for code, count in exit_counter.items()
            if count / total >= self.confidence_threshold
        ]

        # If no codes meet threshold, take most common
        if not expected_exit_codes:
            expected_exit_codes = [exit_counter.most_common(1)[0][0]]

        log.debug(f"CLI expected exit codes: {expected_exit_codes} (from {exit_counter})")

        # Extract common stdout patterns
        stdout_patterns = self._extract_common_patterns(
            [s.observed_cli.stdout for s in snapshots if s.observed_cli.stdout]
        )

        return CLISuccessCriteria(
            expected_exit_codes=expected_exit_codes,
            forbidden_exit_codes=[],
            must_contain_stdout_patterns=stdout_patterns,
            must_not_contain_stdout_patterns=[],
            must_contain_stderr_patterns=[],
            must_not_contain_stderr_patterns=[]
        )

    def _derive_dom_criteria(self, snapshots: List[BehaviorSnapshot]) -> DOMSuccessCriteria:
        """Derive DOM success criteria."""
        # Extract common selectors from all snapshots
        all_selectors: Set[str] = set()

        for snapshot in snapshots:
            if snapshot.observed_dom and snapshot.observed_dom.elements:
                for element in snapshot.observed_dom.elements:
                    if element.selector:
                        all_selectors.add(element.selector)

        # Count selector occurrences across snapshots
        selector_counts = Counter()
        for snapshot in snapshots:
            if snapshot.observed_dom and snapshot.observed_dom.elements:
                snapshot_selectors = {e.selector for e in snapshot.observed_dom.elements if e.selector}
                for selector in snapshot_selectors:
                    selector_counts[selector] += 1

        # Include selectors above confidence threshold
        total = len(snapshots)
        required_selectors = [
            selector for selector, count in selector_counts.items()
            if count / total >= self.confidence_threshold
        ]

        log.debug(f"DOM required selectors: {len(required_selectors)} (from {len(all_selectors)} total)")

        return DOMSuccessCriteria(
            must_exist_selectors=required_selectors,
            must_not_exist_selectors=[],
            must_be_visible_selectors=[],
            must_contain_text_patterns=[]
        )

    def _derive_log_criteria(self, snapshots: List[BehaviorSnapshot]) -> LogSuccessCriteria:
        """Derive log success criteria."""
        # Extract common log patterns
        all_logs = []
        for snapshot in snapshots:
            if snapshot.observed_logs and snapshot.observed_logs.lines:
                all_logs.extend(snapshot.observed_logs.lines)

        # Identify error patterns (heuristic)
        error_patterns = self._identify_error_patterns(all_logs)

        return LogSuccessCriteria(
            must_contain_patterns=[],  # User can customize
            must_not_contain_patterns=error_patterns,
            max_error_count=0  # No errors expected
        )

    def _extract_common_json_paths(self, snapshots: List[BehaviorSnapshot]) -> List[str]:
        """Extract common JSON paths from HTTP responses."""
        all_paths: Set[str] = set()

        for snapshot in snapshots:
            if snapshot.observed_http and isinstance(snapshot.observed_http.body, dict):
                paths = self._extract_json_paths_from_dict(snapshot.observed_http.body)
                all_paths.update(paths)

        # Count path occurrences
        path_counts = Counter()
        for snapshot in snapshots:
            if snapshot.observed_http and isinstance(snapshot.observed_http.body, dict):
                snapshot_paths = self._extract_json_paths_from_dict(snapshot.observed_http.body)
                for path in snapshot_paths:
                    path_counts[path] += 1

        # Include paths above confidence threshold
        total = len(snapshots)
        common_paths = [
            path for path, count in path_counts.items()
            if count / total >= self.confidence_threshold
        ]

        log.debug(f"Common JSON paths: {len(common_paths)} (from {len(all_paths)} total)")
        return sorted(common_paths)[:10]  # Limit to top 10

    def _extract_json_paths_from_dict(self, data: dict, prefix: str = "$") -> Set[str]:
        """Recursively extract JSON paths from dictionary."""
        paths = set()

        for key, value in data.items():
            current_path = f"{prefix}.{key}"
            paths.add(current_path)

            if isinstance(value, dict):
                # Recurse into nested dict
                nested_paths = self._extract_json_paths_from_dict(value, current_path)
                paths.update(nested_paths)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Handle array of objects
                paths.add(f"{current_path}[0]")
                nested_paths = self._extract_json_paths_from_dict(value[0], f"{current_path}[0]")
                paths.update(nested_paths)

        return paths

    def _extract_common_patterns(self, texts: List[str]) -> List[str]:
        """Extract common patterns from text outputs."""
        if not texts:
            return []

        # Simple heuristic: find common lines
        line_counter = Counter()
        for text in texts:
            lines = text.strip().split('\n')
            for line in lines:
                if line.strip():
                    line_counter[line.strip()] += 1

        # Include patterns above confidence threshold
        total = len(texts)
        common_patterns = [
            line for line, count in line_counter.items()
            if count / total >= self.confidence_threshold
        ]

        return sorted(common_patterns)[:5]  # Limit to top 5

    def _identify_error_patterns(self, logs: List[str]) -> List[str]:
        """Identify error patterns in logs (heuristic)."""
        error_keywords = [
            "error", "ERROR", "Error",
            "exception", "Exception", "EXCEPTION",
            "failed", "Failed", "FAILED",
            "fatal", "Fatal", "FATAL"
        ]

        error_patterns = set()
        for log in logs:
            for keyword in error_keywords:
                if keyword in log:
                    error_patterns.add(keyword)

        return sorted(error_patterns)

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _calculate_confidence_score(self, snapshots: List[BehaviorSnapshot]) -> float:
        """
        Calculate confidence score for contract (0.0-1.0).

        Based on:
        - Number of snapshots (more = higher confidence)
        - Success rate (higher = higher confidence)
        - Consistency of observations
        """
        # Base score from sample size
        sample_score = min(len(snapshots) / 10.0, 1.0)  # Cap at 10 snapshots

        # Success rate score
        success_count = sum(1 for s in snapshots if s.success)
        success_score = success_count / len(snapshots)

        # Combine scores
        confidence = (sample_score * 0.4 + success_score * 0.6)

        return round(confidence, 2)


# ============================================================================
# Factory Function
# ============================================================================

def create_contract_generator(
    min_snapshots: int = 3,
    confidence_threshold: float = 0.8,
    percentile: int = 95
) -> ContractGenerator:
    """
    Create contract generator instance.

    Args:
        min_snapshots: Minimum snapshots required
        confidence_threshold: Minimum frequency for pattern inclusion
        percentile: Percentile for duration thresholds

    Returns:
        ContractGenerator instance
    """
    return ContractGenerator(
        min_snapshots=min_snapshots,
        confidence_threshold=confidence_threshold,
        percentile=percentile
    )
