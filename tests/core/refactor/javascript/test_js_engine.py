from unittest.mock import patch

import pytest

from feniks.core.refactor.javascript.engine import JSRefactorEngine


@pytest.fixture
def engine():
    return JSRefactorEngine()


@patch("subprocess.run")
def test_scan_angular(mock_run, engine):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Scan complete"

    res = engine.scan_angular_project(".")
    assert res["success"] is True
    assert "ngma" in mock_run.call_args[0][0]


@patch("subprocess.run")
def test_apply_codemod(mock_run, engine):
    mock_run.return_value.returncode = 0

    res = engine.apply_codemod("ng-to-react-component", ["app.js"])

    assert res["success"] is True
    cmd = mock_run.call_args[0][0]
    assert "jscodeshift" in cmd
    assert "transforms/ng-controller-to-component.js" in cmd
    assert "app.js" in cmd
