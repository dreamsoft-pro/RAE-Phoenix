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
from collections import Counter
from datetime import datetime
from typing import List, Optional, Set

from feniks.core.models.behavior import (
    BehaviorContract,
    BehaviorSnapshot,
    DOMContract,
    HTTPContract,
    LogContract,
)
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

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

    def __init__(self, min_snapshots: int = 3, confidence_threshold: float = 0.8, percentile: int = 95):
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
        log.info(
            f"ContractGenerator initialized (min_snapshots={min_snapshots}, confidence={confidence_threshold}, p{percentile})"
        )

    def generate_contract(
        self, snapshots: List[BehaviorSnapshot], contract_id: Optional[str] = None, version: str = "1.0.0"
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

        # Derive contracts
        http_contract = self._derive_http_contract(snapshots)
        dom_contract = self._derive_dom_contract(snapshots)
        log_contract = self._derive_log_contract(snapshots)

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
            http_contract=http_contract,
            dom_contract=dom_contract,
            log_contract=log_contract,
            max_duration_ms_p95=max_duration_ms,
            created_at=datetime.now(),
            derived_from_snapshot_ids=[s.id for s in snapshots],
            confidence_score=self._calculate_confidence_score(snapshots),
        )

        log.info(f"Contract generated: {contract.id} (confidence={contract.confidence_score:.2f})")
        return contract

    def _derive_http_contract(self, snapshots: List[BehaviorSnapshot]) -> Optional[HTTPContract]:
        """Derive HTTP contract."""
        http_snapshots = [s for s in snapshots if s.observed_http]
        if not http_snapshots:
            return None

        # Collect status codes
        status_codes = [s.observed_http.status_code for s in http_snapshots]
        status_counter = Counter(status_codes)

        # Include status codes above confidence threshold
        total = len(status_codes)
        required_status_codes = [
            code for code, count in status_counter.items() if count / total >= self.confidence_threshold
        ]

        # If no codes meet threshold, take most common
        if not required_status_codes and status_counter:
            required_status_codes = [status_counter.most_common(1)[0][0]]

        log.debug(f"HTTP required status codes: {required_status_codes} (from {status_counter})")

        # Extract common JSON paths
        json_paths = self._extract_common_json_paths(http_snapshots)

        return HTTPContract(
            required_status_codes=required_status_codes,
            allowed_status_codes=sorted(list(status_counter.keys())),  # Allow any seen status code
            forbidden_status_codes=[],  # User can customize
            required_json_paths=json_paths,
            forbidden_json_paths=[],
        )

    def _derive_dom_contract(self, snapshots: List[BehaviorSnapshot]) -> Optional[DOMContract]:
        """Derive DOM contract."""
        dom_snapshots = [s for s in snapshots if s.observed_dom]
        if not dom_snapshots:
            return None

        # Extract common selectors from all snapshots
        all_selectors: Set[str] = set()

        for snapshot in dom_snapshots:
            if snapshot.observed_dom and snapshot.observed_dom.present_selectors:
                for selector in snapshot.observed_dom.present_selectors:
                    all_selectors.add(selector)

        # Count selector occurrences across snapshots
        selector_counts = Counter()
        for snapshot in dom_snapshots:
            if snapshot.observed_dom and snapshot.observed_dom.present_selectors:
                for selector in snapshot.observed_dom.present_selectors:
                    selector_counts[selector] += 1

        # Include selectors above confidence threshold
        total = len(dom_snapshots)
        must_have_selectors = [
            selector for selector, count in selector_counts.items() if count / total >= self.confidence_threshold
        ]

        log.debug(f"DOM must-have selectors: {len(must_have_selectors)} (from {len(all_selectors)} total)")

        return DOMContract(
            must_have_selectors=must_have_selectors,
            must_not_have_selectors=[],
            must_have_text_snippets=[],
            must_not_have_text_snippets=[],
        )

    def _derive_log_contract(self, snapshots: List[BehaviorSnapshot]) -> Optional[LogContract]:
        """Derive log contract."""
        log_snapshots = [s for s in snapshots if s.observed_logs]
        if not log_snapshots:
            return None

        # Extract common log patterns
        all_logs = []
        for snapshot in log_snapshots:
            if snapshot.observed_logs and snapshot.observed_logs.lines:
                all_logs.extend(snapshot.observed_logs.lines)

        # Identify error patterns (heuristic)
        # In a contract, we usually define what is FORBIDDEN (errors)
        # We don't auto-generate forbidden patterns from successful snapshots usually,
        # unless we see them in failed snapshots?
        # Here we assume the input snapshots are "good" (legacy behavior).
        # If legacy has errors, maybe we shouldn't forbid them?
        # For now, we use defaults for forbidden_patterns in LogContract (Exception, ERROR).

        return LogContract(
            required_patterns=[],  # Hard to derive meaningful required patterns automatically
            forbidden_patterns=["Exception", "Traceback", "ERROR"],  # Default forbidden
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
        common_paths = [path for path, count in path_counts.items() if count / total >= self.confidence_threshold]

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
            lines = text.strip().split("\n")
            for line in lines:
                if line.strip():
                    line_counter[line.strip()] += 1

        # Include patterns above confidence threshold
        total = len(texts)
        common_patterns = [line for line, count in line_counter.items() if count / total >= self.confidence_threshold]

        return sorted(common_patterns)[:5]  # Limit to top 5

    def _identify_error_patterns(self, logs: List[str]) -> List[str]:
        """Identify error patterns in logs (heuristic)."""
        error_keywords = [
            "error",
            "ERROR",
            "Error",
            "exception",
            "Exception",
            "EXCEPTION",
            "failed",
            "Failed",
            "FAILED",
            "fatal",
            "Fatal",
            "FATAL",
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
        confidence = sample_score * 0.4 + success_score * 0.6

        return round(confidence, 2)


# ============================================================================
# Factory Function
# ============================================================================


def create_contract_generator(
    min_snapshots: int = 3, confidence_threshold: float = 0.8, percentile: int = 95
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
        min_snapshots=min_snapshots, confidence_threshold=confidence_threshold, percentile=percentile
    )
