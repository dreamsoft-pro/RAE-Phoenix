# Copyright 2025 Grzegorz Le[niowski
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
Feniks Core Models.

Export all domain and behavior models for easy import.
"""
from feniks.core.models.domain import (
    ReasoningTrace,
    CostProfile,
    SessionSummary,
    FeniksReport,
)

from feniks.core.models.behavior import (
    # Input models
    UIAction,
    APIRequest,
    CLICommand,
    BehaviorInput,
    # Criteria models
    HTTPCriteria,
    DOMCriteria,
    LogCriteria,
    BehaviorSuccessCriteria,
    # Scenario
    BehaviorScenario,
    # Observation models
    ObservedHTTP,
    ObservedDOM,
    ObservedLogs,
    # Violation and Snapshot
    BehaviorViolation,
    BehaviorSnapshot,
    # Contract models
    HTTPContract,
    DOMContract,
    LogContract,
    BehaviorContract,
    # Check result
    BehaviorCheckResult,
    BehaviorChecksSummary,
)

__all__ = [
    # Domain models
    "ReasoningTrace",
    "CostProfile",
    "SessionSummary",
    "FeniksReport",
    # Behavior input models
    "UIAction",
    "APIRequest",
    "CLICommand",
    "BehaviorInput",
    # Behavior criteria
    "HTTPCriteria",
    "DOMCriteria",
    "LogCriteria",
    "BehaviorSuccessCriteria",
    # Behavior scenario
    "BehaviorScenario",
    # Behavior observations
    "ObservedHTTP",
    "ObservedDOM",
    "ObservedLogs",
    # Behavior violations and snapshots
    "BehaviorViolation",
    "BehaviorSnapshot",
    # Behavior contracts
    "HTTPContract",
    "DOMContract",
    "LogContract",
    "BehaviorContract",
    # Behavior check results
    "BehaviorCheckResult",
    "BehaviorChecksSummary",
]
