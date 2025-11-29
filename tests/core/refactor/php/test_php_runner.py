from unittest.mock import patch

from feniks.core.refactor.php.tools import DeptracWrapper, PHPStanWrapper, RectorWrapper


@patch("subprocess.run")
def test_rector_process(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "{}"

    tool = RectorWrapper()
    res = tool.process("src")

    assert res["success"] is True
    assert "--dry-run" in mock_run.call_args[0][0]


@patch("subprocess.run")
def test_phpstan_analyze(mock_run):
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = "Errors"

    tool = PHPStanWrapper()
    res = tool.analyze("src")

    assert res["success"] is False
    assert "--level=5" in mock_run.call_args[0][0]


@patch("subprocess.run")
def test_deptrac_analyze(mock_run):
    tool = DeptracWrapper()
    tool.analyze()
    assert "vendor/bin/deptrac" in mock_run.call_args[0][0]


@patch("subprocess.run")
def test_runner_file_not_found(mock_run):
    mock_run.side_effect = FileNotFoundError
    tool = RectorWrapper()
    res = tool.process()
    assert res["success"] is False
    assert res["error"] == "Tool not found"
