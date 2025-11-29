from datetime import datetime

import pytest

from feniks.core.models.domain import CostProfile, FeniksReport, ReasoningTrace, SessionSummary


def test_cost_profile_creation():
    profile = CostProfile(total_tokens=150, cost_usd=0.002, breakdown={"gpt-4": 0.002})
    assert profile.total_tokens == 150
    assert profile.cost_usd == 0.002
    assert profile.breakdown["gpt-4"] == 0.002


def test_reasoning_trace_creation():
    trace = ReasoningTrace(
        step_id="step-1",
        thought="Thinking about life",
        action="Consult oracle",
        result="42",
        timestamp="2025-11-26T12:00:00",
    )
    assert trace.step_id == "step-1"
    assert trace.result == "42"


def test_session_summary_defaults():
    summary = SessionSummary(session_id="sess-123", duration=10.5, success=True)
    assert summary.session_id == "sess-123"
    assert summary.reasoning_traces == []
    assert summary.cost_profile is None


def test_feniks_report_full_structure():
    profile = CostProfile(total_tokens=100, cost_usd=0.01)
    summary = SessionSummary(session_id="sess-1", duration=5.0, success=True, cost_profile=profile)

    report = FeniksReport(
        project_id="proj-alpha",
        timestamp=datetime.now().isoformat(),
        summary=summary,
        metrics={"complexity": 10},
        recommendations=["Refactor X"],
    )

    assert report.project_id == "proj-alpha"
    assert report.summary.cost_profile.total_tokens == 100
    assert report.metrics["complexity"] == 10

    # Test Serialization
    json_output = report.model_dump_json()
    assert "proj-alpha" in json_output
    assert "Refactor X" in json_output


def test_feniks_report_validation_error():
    # Missing required fields
    with pytest.raises(ValueError):
        FeniksReport(project_id="fail")


def test_session_with_1000_reasoning_steps():
    """Test dla dużej sesji (>1000 steps) - weryfikacja skalowalności."""
    traces = [
        ReasoningTrace(
            step_id=f"step-{i}",
            thought=f"Thought number {i}",
            action=f"action-{i % 5}",  # Rotacja akcji
            result="ok",
            timestamp=f"2025-11-26T12:{i % 60:02d}:00",
        )
        for i in range(1500)
    ]

    session = SessionSummary(session_id="large-session", duration=300.0, success=True, reasoning_traces=traces)

    assert len(session.reasoning_traces) == 1500
    assert session.reasoning_traces[0].step_id == "step-0"
    assert session.reasoning_traces[1499].step_id == "step-1499"
    assert session.success is True


def test_session_without_reasoning():
    """Test dla sesji bez reasoning traces - edge case."""
    session = SessionSummary(session_id="empty-reasoning", duration=10.0, success=True, reasoning_traces=[])

    assert session.reasoning_traces == []
    assert len(session.reasoning_traces) == 0
    assert session.success is True


def test_session_with_loops():
    """Test dla sesji z pętlami - powtarzające się akcje."""
    traces = [
        ReasoningTrace(
            step_id="1",
            thought="First attempt to read file",
            action="read_file",
            result="ok",
            timestamp="2025-11-26T12:00:00",
        ),
        ReasoningTrace(
            step_id="2",
            thought="Second attempt to read file",
            action="read_file",  # Loop!
            result="ok",
            timestamp="2025-11-26T12:00:01",
        ),
        ReasoningTrace(
            step_id="3",
            thought="Third attempt to read file",
            action="read_file",  # Loop again!
            result="ok",
            timestamp="2025-11-26T12:00:02",
        ),
        ReasoningTrace(
            step_id="4",
            thought="Finally writing changes",
            action="write_file",
            result="ok",
            timestamp="2025-11-26T12:00:03",
        ),
    ]

    session = SessionSummary(
        session_id="loop-session",
        duration=30.0,
        success=False,  # Sesja z pętlą zazwyczaj kończy się niepowodzeniem
        reasoning_traces=traces,
        cost_profile=CostProfile(total_tokens=5000, cost_usd=0.15),
    )

    assert len(session.reasoning_traces) == 4
    assert session.success is False

    # Weryfikacja, że PostMortemAnalyzer wykryje pętlę
    from feniks.core.reflection.post_mortem import PostMortemAnalyzer

    analyzer = PostMortemAnalyzer()
    reflections = analyzer.analyze_session(session)

    # Powinna być refleksja o pętli
    loop_reflections = [r for r in reflections if "Loop" in r.title]
    assert len(loop_reflections) > 0, "PostMortemAnalyzer should detect reasoning loop"


def test_session_with_empty_thoughts():
    """Test dla sesji z pustymi myślami - quality issue."""
    traces = [
        ReasoningTrace(
            step_id="1",
            thought="Good thought with content",
            action="read_file",
            result="ok",
            timestamp="2025-11-26T12:00:00",
        ),
        ReasoningTrace(
            step_id="2", thought="", action="write_file", result="ok", timestamp="2025-11-26T12:00:01"  # Empty thought!
        ),
        ReasoningTrace(
            step_id="3",
            thought="   ",  # Whitespace only!
            action="commit",
            result="ok",
            timestamp="2025-11-26T12:00:02",
        ),
    ]

    session = SessionSummary(session_id="empty-thoughts-session", duration=15.0, success=True, reasoning_traces=traces)

    assert len(session.reasoning_traces) == 3

    # Weryfikacja wykrycia pustych myśli przez PostMortemAnalyzer
    from feniks.core.reflection.post_mortem import PostMortemAnalyzer

    analyzer = PostMortemAnalyzer()
    reflections = analyzer.analyze_session(session)

    empty_thought_reflections = [r for r in reflections if "Empty Reasoning" in r.title]
    assert len(empty_thought_reflections) > 0, "PostMortemAnalyzer should detect empty thoughts"


def test_session_cost_profile_optional():
    """Test dla sesji bez cost profile - opcjonalne pole."""
    session = SessionSummary(session_id="no-cost", duration=5.0, success=True, cost_profile=None)

    assert session.cost_profile is None

    # Powinna działać analiza nawet bez cost profile
    from feniks.core.reflection.post_mortem import PostMortemAnalyzer

    analyzer = PostMortemAnalyzer()
    reflections = analyzer.analyze_session(session)

    # Nie powinno być refleksji o kosztach
    cost_reflections = [r for r in reflections if "Cost" in r.title]
    assert len(cost_reflections) == 0
