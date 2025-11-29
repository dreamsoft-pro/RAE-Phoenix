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
Tests for Quality Policy enforcement.
"""
import pytest

from feniks.core.models.domain import ReasoningTrace, SessionSummary
from feniks.core.policies.quality_policy import QualityPolicyConfig, QualityPolicyEnforcer


@pytest.fixture
def enforcer():
    """Create a QualityPolicyEnforcer with default config."""
    config = QualityPolicyConfig(
        min_thought_length=10,
        forbidden_patterns=[r"I don't know what to do", r"just guessing", r"random try"],
        require_thought_before_action=True,
    )
    return QualityPolicyEnforcer(config)


def test_quality_policy_short_thoughts(enforcer):
    """Test dla wykrywania zbyt krótkich myśli."""
    traces = [
        ReasoningTrace(step_id="1", thought="ok", action="read", result="ok", timestamp="ts1"),
        ReasoningTrace(step_id="2", thought="hmm", action="write", result="ok", timestamp="ts2"),
        ReasoningTrace(step_id="3", thought="yes", action="commit", result="ok", timestamp="ts3"),
    ]

    session = SessionSummary(session_id="short-thoughts", duration=30.0, success=True, reasoning_traces=traces)

    reflections = enforcer.check_trace_quality(session)

    # Powinny być wykryte krótkie myśli (< 10 znaków)
    short_thought_reflections = [r for r in reflections if "Too Short" in r.title or "Short" in r.title]
    assert len(short_thought_reflections) > 0, "Should detect short thoughts"
    assert short_thought_reflections[0].impact.value == "refactor-recommended"


def test_quality_policy_good_thoughts(enforcer):
    """Test dla sesji z dobrymi, długimi myślami."""
    traces = [
        ReasoningTrace(
            step_id="1",
            thought="I will analyze the code structure before making changes",
            action="analyze",
            result="ok",
            timestamp="ts1",
        ),
        ReasoningTrace(
            step_id="2",
            thought="Based on the analysis, I will refactor the function to improve readability",
            action="refactor",
            result="ok",
            timestamp="ts2",
        ),
    ]

    session = SessionSummary(session_id="good-thoughts", duration=60.0, success=True, reasoning_traces=traces)

    reflections = enforcer.check_trace_quality(session)

    # Nie powinno być refleksji o krótkich myślach
    short_thought_reflections = [r for r in reflections if "Short" in r.title]
    assert len(short_thought_reflections) == 0, "Should not detect short thoughts in good session"


def test_quality_policy_forbidden_patterns(enforcer):
    """Test dla wykrywania zabronionych wzorców."""
    traces = [
        ReasoningTrace(
            step_id="1",
            thought="I don't know what to do, so I'll try something random",
            action="random_action",
            result="fail",
            timestamp="ts1",
        ),
        ReasoningTrace(
            step_id="2", thought="Just guessing here, hoping it works", action="guess", result="fail", timestamp="ts2"
        ),
    ]

    session = SessionSummary(session_id="forbidden-patterns", duration=45.0, success=False, reasoning_traces=traces)

    reflections = enforcer.check_trace_quality(session)

    # Powinny być wykryte zabronione wzorce
    forbidden_reflections = [r for r in reflections if "Forbidden" in r.title or "Pattern" in r.title]
    assert len(forbidden_reflections) > 0, "Should detect forbidden patterns"

    # Sprawdź critical impact
    critical_reflections = [r for r in forbidden_reflections if r.impact.value == "critical"]
    assert len(critical_reflections) > 0, "Forbidden patterns should be critical"


def test_quality_policy_no_traces():
    """Test dla sesji bez reasoning traces."""
    config = QualityPolicyConfig()
    enforcer = QualityPolicyEnforcer(config)

    session = SessionSummary(session_id="no-traces", duration=10.0, success=True, reasoning_traces=[])

    reflections = enforcer.check_trace_quality(session)

    assert len(reflections) == 0, "Should not generate reflections for empty traces"


def test_quality_policy_custom_min_length():
    """Test dla niestandardowego minimum długości myśli."""
    config = QualityPolicyConfig(min_thought_length=50)  # Bardzo wysokie wymaganie
    enforcer = QualityPolicyEnforcer(config)

    traces = [
        ReasoningTrace(
            step_id="1",
            thought="This is a moderate length thought",  # 36 znaków
            action="action",
            result="ok",
            timestamp="ts1",
        )
    ]

    session = SessionSummary(session_id="custom-threshold", duration=10.0, success=True, reasoning_traces=traces)

    reflections = enforcer.check_trace_quality(session)

    # Powinna być refleksja, bo 36 < 50
    short_thought_reflections = [r for r in reflections if "Short" in r.title or "Too Short" in r.title]
    assert len(short_thought_reflections) > 0, "Should detect thoughts below custom threshold"


def test_quality_policy_case_insensitive_patterns():
    """Test dla wykrywania wzorców niezależnie od wielkości liter."""
    config = QualityPolicyConfig(min_thought_length=5, forbidden_patterns=[r"don't know"])
    enforcer = QualityPolicyEnforcer(config)

    traces = [
        ReasoningTrace(
            step_id="1",
            thought="I DON'T KNOW what to do here",  # Wielkie litery
            action="confused",
            result="fail",
            timestamp="ts1",
        )
    ]

    session = SessionSummary(session_id="case-test", duration=10.0, success=False, reasoning_traces=traces)

    reflections = enforcer.check_trace_quality(session)

    # Powinno wykryć mimo wielkich liter (re.IGNORECASE w implementacji)
    forbidden_reflections = [r for r in reflections if "Forbidden" in r.title or "Pattern" in r.title]
    assert len(forbidden_reflections) > 0, "Should detect patterns case-insensitively"


def test_quality_policy_empty_and_whitespace_thoughts():
    """Test dla pustych i białych znaków w myślach."""
    config = QualityPolicyConfig(min_thought_length=5)
    enforcer = QualityPolicyEnforcer(config)

    traces = [
        ReasoningTrace(step_id="1", thought="", action="action1", result="ok", timestamp="ts1"),
        ReasoningTrace(step_id="2", thought="   ", action="action2", result="ok", timestamp="ts2"),
        ReasoningTrace(step_id="3", thought="\t\n", action="action3", result="ok", timestamp="ts3"),
    ]

    session = SessionSummary(session_id="empty-whitespace", duration=15.0, success=True, reasoning_traces=traces)

    reflections = enforcer.check_trace_quality(session)

    # Wszystkie 3 powinny być wykryte jako zbyt krótkie (po strip())
    short_thought_reflections = [r for r in reflections if "Short" in r.title or "Too Short" in r.title]
    assert len(short_thought_reflections) > 0, "Should detect empty/whitespace thoughts"

    # Sprawdź czy w content jest liczba 3
    if short_thought_reflections:
        assert "3" in short_thought_reflections[0].content


def test_quality_policy_recommendations():
    """Test dla treści rekomendacji w refleksjach."""
    config = QualityPolicyConfig(min_thought_length=20)
    enforcer = QualityPolicyEnforcer(config)

    traces = [ReasoningTrace(step_id="1", thought="short", action="act", result="ok", timestamp="ts1")]

    session = SessionSummary(session_id="recs-test", duration=10.0, success=True, reasoning_traces=traces)

    reflections = enforcer.check_trace_quality(session)

    assert len(reflections) > 0
    assert len(reflections[0].recommendations) > 0
    # Sprawdź czy rekomendacje są sensowne
    recs_text = " ".join(reflections[0].recommendations).lower()
    assert "prompt" in recs_text or "reasoning" in recs_text or "verbose" in recs_text
