import pytest
from datetime import datetime
from feniks.core.models.domain import FeniksReport, SessionSummary, CostProfile, ReasoningTrace

def test_cost_profile_creation():
    profile = CostProfile(
        total_tokens=150,
        cost_usd=0.002,
        breakdown={"gpt-4": 0.002}
    )
    assert profile.total_tokens == 150
    assert profile.cost_usd == 0.002
    assert profile.breakdown["gpt-4"] == 0.002

def test_reasoning_trace_creation():
    trace = ReasoningTrace(
        step_id="step-1",
        thought="Thinking about life",
        action="Consult oracle",
        result="42",
        timestamp="2025-11-26T12:00:00"
    )
    assert trace.step_id == "step-1"
    assert trace.result == "42"

def test_session_summary_defaults():
    summary = SessionSummary(
        session_id="sess-123",
        duration=10.5,
        success=True
    )
    assert summary.session_id == "sess-123"
    assert summary.reasoning_traces == []
    assert summary.cost_profile is None

def test_feniks_report_full_structure():
    profile = CostProfile(total_tokens=100, cost_usd=0.01)
    summary = SessionSummary(
        session_id="sess-1", 
        duration=5.0, 
        success=True, 
        cost_profile=profile
    )
    
    report = FeniksReport(
        project_id="proj-alpha",
        timestamp=datetime.now().isoformat(),
        summary=summary,
        metrics={"complexity": 10},
        recommendations=["Refactor X"]
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
