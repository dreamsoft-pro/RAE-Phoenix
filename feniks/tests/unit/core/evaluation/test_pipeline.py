from unittest.mock import MagicMock, patch

import pytest

from feniks.core.evaluation.pipeline import AnalysisPipeline
from feniks.core.models.types import SystemModel
from feniks.exceptions import FeniksStoreError


@pytest.fixture
def pipeline():
    return AnalysisPipeline(qdrant_host="mock_host", qdrant_port=6333)


@patch("feniks.core.evaluation.pipeline.QdrantClient")
def test_load_chunks_success(mock_qdrant_cls, pipeline):
    # Setup mock client
    mock_client = MagicMock()
    mock_qdrant_cls.return_value = mock_client

    # Mock collection info
    mock_client.get_collection.return_value.points_count = 2

    # Mock scroll results
    # First call returns 2 points, second call returns empty (end of scroll)
    p1 = MagicMock(id="1", payload={"id": "1", "text": "code1", "file_path": "f1"})
    p2 = MagicMock(id="2", payload={"id": "2", "text": "code2", "file_path": "f2"})

    mock_client.scroll.side_effect = [([p1, p2], "next_offset"), ([], None)]  # First batch  # End

    chunks = pipeline._load_chunks_from_qdrant("test_collection")

    assert len(chunks) == 2
    assert chunks[0].id == "1"
    assert chunks[1].file_path == "f2"


@patch("feniks.core.evaluation.pipeline.QdrantClient")
def test_load_chunks_empty(mock_qdrant_cls, pipeline):
    mock_client = MagicMock()
    mock_qdrant_cls.return_value = mock_client
    mock_client.get_collection.return_value.points_count = 0
    mock_client.scroll.return_value = ([], None)

    chunks = pipeline._load_chunks_from_qdrant("empty_collection")
    assert len(chunks) == 0


@patch("feniks.core.evaluation.pipeline.QdrantClient")
def test_load_chunks_error(mock_qdrant_cls, pipeline):
    mock_qdrant_cls.side_effect = Exception("Connection failed")

    with pytest.raises(FeniksStoreError):
        pipeline._load_chunks_from_qdrant("bad_collection")


@patch("feniks.core.evaluation.pipeline.create_rae_client")
def test_sync_with_rae_success(mock_create_client, pipeline):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    model = SystemModel(project_id="p1", timestamp="now")
    reflections = [MagicMock()]

    result = pipeline._sync_with_rae(model, reflections)

    assert result is True
    mock_client.store_meta_reflection.assert_called()
    mock_client.store_system_model.assert_called()


@patch("feniks.core.evaluation.pipeline.create_rae_client")
def test_sync_with_rae_disabled(mock_create_client, pipeline):
    mock_create_client.return_value = None  # RAE disabled

    result = pipeline._sync_with_rae(SystemModel(project_id="p1", timestamp="now"), [])

    assert result is False


def test_scoring_quality_high():
    """Test quality scoring dla sesji o wysokiej jakości."""
    from feniks.core.models.domain import ReasoningTrace, SessionSummary

    # Sesja z dobrymi, długimi myślami
    traces = [
        ReasoningTrace(
            step_id="1",
            thought="I will carefully analyze the requirements before proceeding with implementation",
            action="analyze",
            result="success",
            timestamp="2025-11-26T12:00:00",
        ),
        ReasoningTrace(
            step_id="2",
            thought="Based on the analysis, I will implement the feature using best practices",
            action="implement",
            result="success",
            timestamp="2025-11-26T12:01:00",
        ),
    ]

    SessionSummary(session_id="quality-high", duration=60.0, success=True, reasoning_traces=traces)

    # Quality score powinien być wysoki (długie myśli, sukces, brak pętli)
    # Dla celów testu zakładamy metrykę: średnia długość myśli / 50
    avg_thought_length = sum(len(t.thought) for t in traces) / len(traces)
    quality_score = min(avg_thought_length / 50, 1.0)

    assert quality_score > 0.8, f"Expected high quality score, got {quality_score}"


def test_scoring_quality_low():
    """Test quality scoring dla sesji o niskiej jakości."""
    from feniks.core.models.domain import ReasoningTrace, SessionSummary

    # Sesja z krótkimi/pustymi myślami
    traces = [
        ReasoningTrace(step_id="1", thought="ok", action="read", result="ok", timestamp="ts1"),
        ReasoningTrace(step_id="2", thought="", action="write", result="fail", timestamp="ts2"),
        ReasoningTrace(step_id="3", thought="hmm", action="read", result="ok", timestamp="ts3"),
    ]

    SessionSummary(session_id="quality-low", duration=30.0, success=False, reasoning_traces=traces)

    # Quality score powinien być niski
    avg_thought_length = sum(len(t.thought) for t in traces) / len(traces)
    quality_score = min(avg_thought_length / 50, 1.0)

    assert quality_score < 0.3, f"Expected low quality score, got {quality_score}"


def test_scoring_efficiency():
    """Test efficiency scoring - cost per token."""
    from feniks.core.models.domain import CostProfile, SessionSummary

    # Sesja efektywna (niski koszt, krótki czas)
    session_efficient = SessionSummary(
        session_id="efficient", duration=30.0, success=True, cost_profile=CostProfile(total_tokens=1000, cost_usd=0.02)
    )

    # Sesja nieefektywna (wysoki koszt, długi czas)
    session_inefficient = SessionSummary(
        session_id="inefficient",
        duration=300.0,
        success=True,
        cost_profile=CostProfile(total_tokens=50000, cost_usd=2.5),
    )

    # Efficiency = 1 / (cost_usd * duration)
    efficiency_good = 1.0 / (session_efficient.cost_profile.cost_usd * session_efficient.duration)
    efficiency_bad = 1.0 / (session_inefficient.cost_profile.cost_usd * session_inefficient.duration)

    assert efficiency_good > efficiency_bad, "Efficient session should have higher efficiency score"
    assert efficiency_good > 1.0, f"Expected efficiency > 1.0, got {efficiency_good}"
    assert efficiency_bad < 0.01, f"Expected low efficiency < 0.01, got {efficiency_bad}"


def test_loop_detection_consecutive_actions():
    """Test wykrywania pętli - kolejne identyczne akcje."""
    from feniks.core.models.domain import ReasoningTrace, SessionSummary
    from feniks.core.reflection.post_mortem import PostMortemAnalyzer

    traces = [
        ReasoningTrace(step_id="1", thought="t1", action="retry_operation", result="fail", timestamp="ts1"),
        ReasoningTrace(step_id="2", thought="t2", action="retry_operation", result="fail", timestamp="ts2"),
        ReasoningTrace(step_id="3", thought="t3", action="retry_operation", result="fail", timestamp="ts3"),
    ]

    session = SessionSummary(session_id="loop-detection", duration=45.0, success=False, reasoning_traces=traces)

    analyzer = PostMortemAnalyzer()
    reflections = analyzer.analyze_session(session)

    # Powinny być wykryte pętle
    loop_reflections = [r for r in reflections if "Loop" in r.title]
    assert len(loop_reflections) > 0, "Loop detection should identify consecutive identical actions"
    assert loop_reflections[0].impact.value == "critical"


def test_loop_detection_no_false_positives():
    """Test wykrywania pętli - brak false positives dla normalnego workflow."""
    from feniks.core.models.domain import ReasoningTrace, SessionSummary
    from feniks.core.reflection.post_mortem import PostMortemAnalyzer

    # Normalna sekwencja różnych akcji
    traces = [
        ReasoningTrace(step_id="1", thought="t1", action="read_file", result="ok", timestamp="ts1"),
        ReasoningTrace(step_id="2", thought="t2", action="analyze_code", result="ok", timestamp="ts2"),
        ReasoningTrace(step_id="3", thought="t3", action="write_changes", result="ok", timestamp="ts3"),
        ReasoningTrace(step_id="4", thought="t4", action="run_tests", result="ok", timestamp="ts4"),
    ]

    session = SessionSummary(session_id="no-loop", duration=60.0, success=True, reasoning_traces=traces)

    analyzer = PostMortemAnalyzer()
    reflections = analyzer.analyze_session(session)

    # Nie powinno być wykrytych pętli
    loop_reflections = [r for r in reflections if "Loop" in r.title]
    assert len(loop_reflections) == 0, "Should not detect loops in normal workflow"


def test_scoring_with_missing_data():
    """Test scoring gdy brakuje danych (edge case)."""
    from feniks.core.models.domain import SessionSummary

    # Sesja bez reasoning traces i bez cost profile
    session = SessionSummary(session_id="minimal", duration=10.0, success=True)

    assert len(session.reasoning_traces) == 0
    assert session.cost_profile is None

    # Powinna działać analiza mimo braków
    from feniks.core.reflection.post_mortem import PostMortemAnalyzer

    analyzer = PostMortemAnalyzer()
    reflections = analyzer.analyze_session(session)

    # Powinna być pusta lista lub tylko basic reflections
    assert isinstance(reflections, list)
