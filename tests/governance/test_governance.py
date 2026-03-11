from datetime import datetime

from feniks.core.models.types import SystemModel
from feniks.governance.engine import GovernanceEngine


def test_governance_engine_init():
    engine = GovernanceEngine()
    assert engine.rules == []


def test_governance_check_stub():
    engine = GovernanceEngine()
    # Mock system model
    model = SystemModel(
        project_id="test",
        timestamp=datetime.now().isoformat(),
        modules={},
        dependencies=[],
        capabilities=[],
    )
    result = engine.run_checks(model)

    assert result["status"] == "PASSED"
    assert result["violations"] == []
