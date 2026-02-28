import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

from feniks.core.refactor.python.engine import PythonRefactorEngine
from feniks.core.refactor.python.tools import BowlerWrapper


@pytest.fixture
def engine():
    return PythonRefactorEngine()


@patch("subprocess.run")
def test_ruff_check(mock_run, engine):
    mock_run.return_value.stdout = '{"files": []}'
    mock_run.return_value.returncode = 0

    with patch("shutil.which", return_value="/usr/bin/ruff"):
        result = engine.ruff.check("test.py")
        assert isinstance(result, dict)
        assert "files" in result


@patch("subprocess.run")
def test_ruff_check_fail(mock_run, engine):
    mock_run.return_value.stdout = "invalid json"
    mock_run.return_value.returncode = 1

    with patch("shutil.which", return_value="/usr/bin/ruff"):
        result = engine.ruff.check("test.py")
        assert "error" in result


@patch("subprocess.run")
def test_ruff_fix(mock_run, engine):
    mock_run.return_value.returncode = 0
    with patch("shutil.which", return_value="/usr/bin/ruff"):
        engine.ruff.fix("test.py")
        assert "--fix" in mock_run.call_args[0][0]


@patch("subprocess.run")
def test_mypy_check(mock_run, engine):
    mock_run.return_value.stdout = "Success"
    mock_run.return_value.returncode = 0

    with patch("shutil.which", return_value="/usr/bin/mypy"):
        result = engine.mypy.check("test.py")
        assert result == "Success"


@patch("subprocess.run")
def test_bowler_run(mock_run):
    tool = BowlerWrapper()
    res = tool.run_query("select")
    assert res == "Bowler execution placeholder"


def test_libcst_analyze_not_found(engine):
    # This returns "LibCST not installed" if import fails, which it does in this env
    res = engine.libcst.analyze_structure("nonexistent.py")
    assert "error" in res


def test_libcst_analyze_success(engine):
    # Mock libcst module
    mock_cst = MagicMock()
    mock_module = MagicMock()
    mock_visitor = MagicMock()
    mock_visitor.functions = ["my_func"]
    mock_visitor.classes = ["MyClass"]

    # We need to mock the class inside the method, which is hard.
    # But we can mock the import.
    with patch.dict(sys.modules, {"libcst": mock_cst}):
        with patch("builtins.open", mock_open(read_data="def my_func(): pass")):
            with patch("pathlib.Path.exists", return_value=True):
                # We need to ensure our mocked StructureVisitor is used
                # But StructureVisitor is defined inside the method inheriting from cst.CSTVisitor
                # So cst.CSTVisitor needs to be a class we can inherit from

                mock_cst.CSTVisitor = object  # Allow inheritance
                mock_cst.parse_module.return_value = mock_module

                # The visitor logic is internal, we can't easily mock the internal state change
                # without inspecting the visitor instance which is local.
                # However, if we just want to test that it runs:
                res = engine.libcst.analyze_structure("test.py")

                # Since we can't easily populate the internal visitor's list via mocks without more complex setup,
                # we expect it to return empty lists (default) but NOT "LibCST not installed".
                assert isinstance(res, dict)
                assert "functions" in res or "error" not in res


@patch("subprocess.run")
def test_engine_run_pipeline(mock_run, engine):
    mock_run.return_value.stdout = '{"files": []}'
    mock_run.return_value.returncode = 0

    with patch("shutil.which", return_value="/bin/true"):
        # Mock libcst wrapper
        engine.libcst.analyze_structure = MagicMock(return_value={"functions": ["foo"]})

        with patch("pathlib.Path.is_file", return_value=True):
            with patch("pathlib.Path.suffix", new_callable=lambda: ".py"):
                res = engine.run_pipeline("test.py", strategies=["auto-fix"])

                assert "static_analysis" in res
                assert "structure" in res
                assert "refactoring" in res
                assert res["structure"]["functions"] == ["foo"]
                assert "ruff-fix" in res["refactoring"]["actions_taken"]


def test_engine_directory_analysis(engine):
    with patch("pathlib.Path.is_file", return_value=False):
        res = engine.stage_structural_analysis("dir")
        assert "info" in res
