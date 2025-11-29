import json
from pathlib import Path

import pytest

from feniks.core.models.domain import SessionSummary
from feniks.core.reflection.engine import MetaReflectionEngine

# Adjust path to point to root tests/fixtures
GOLDEN_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "golden"


def load_golden_session(name: str) -> SessionSummary:
    path = GOLDEN_DIR / "sessions" / f"{name}.json"
    if not path.exists():
        pytest.fail(f"Golden session file not found: {path}")
    with path.open() as f:
        data = json.load(f)
    return SessionSummary(**data)


def load_expected_report(name: str) -> list:
    path = GOLDEN_DIR / "reports" / f"{name}.json"
    if not path.exists():
        pytest.fail(f"Golden report file not found: {path}")
    with path.open() as f:
        return json.load(f)


@pytest.fixture
def engine():
    return MetaReflectionEngine()


def test_golden_success_session(engine):
    """
    Verify that a successful session generates no critical alerts.
    """
    session = load_golden_session("success")
    reflections = engine.run_post_mortem(session, project_id="golden-test")

    # Should be 0 critical alerts
    criticals = [r for r in reflections if r.impact.value == "critical"]
    assert len(criticals) == 0, f"Expected 0 criticals, got {len(criticals)}: {[r.title for r in criticals]}"


def test_golden_failure_loop_session(engine):
    """
    Verify that a failed looping session is correctly diagnosed.
    Snaphost testing against expected report.
    """
    session = load_golden_session("failure_loop")
    reflections = engine.run_post_mortem(session, project_id="golden-test")

    expected = load_expected_report("expected_failure_report")

    # Check for key reflection types
    titles = [r.title for r in reflections]

    assert "Session Failure Detected" in titles
    assert "Reasoning Loop Detected" in titles

    # Note: "Reasoning Steps Too Short" might depend on specific policy config default values.
    # The fixture has an empty thought in step 4, which should trigger it if min_length > 0.
    assert "Reasoning Steps Too Short" in titles

    # Check count (approximate, as policies might evolve)
    assert len(reflections) >= len(expected)


def test_golden_high_cost_session(engine):
    """
    Verify that a high-cost session triggers cost alert.
    """
    session = load_golden_session("high_cost")
    reflections = engine.run_post_mortem(session, project_id="golden-test")

    # Should detect high cost (2.5 USD > default threshold)
    titles = [r.title for r in reflections]
    assert any("Cost" in title for title in titles), "Should detect high cost"

    # Should have no failure alert (session was successful)
    assert "Session Failure Detected" not in titles


def test_golden_warning_quality_session(engine):
    """
    Verify that a session with quality warnings is detected correctly.
    """
    session = load_golden_session("warning_quality")
    reflections = engine.run_post_mortem(session, project_id="golden-test")

    # Should detect short thoughts
    titles = [r.title for r in reflections]
    assert any("Short" in title or "Too Short" in title for title in titles), "Should detect short thoughts"

    # Should have warnings but NOT critical failures
    critical_reflections = [r for r in reflections if r.impact.value == "critical"]
    assert len(critical_reflections) == 0, "Should not have critical reflections for warning-level issues"


def test_golden_perfect_session(engine):
    """
    Verify that a perfect session generates no alerts (no false positives).
    """
    session = load_golden_session("perfect")
    reflections = engine.run_post_mortem(session, project_id="golden-test")

    # Should generate ZERO reflections (perfect quality, good cost, no loops, success)
    assert (
        len(reflections) == 0
    ), f"Expected 0 reflections for perfect session, got {len(reflections)}: {[r.title for r in reflections]}"
