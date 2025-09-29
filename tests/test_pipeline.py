import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from pydantic import ValidationError as PydanticValidationError

# Add project root to path to allow imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.feniks_cli import run_external_script, load_enriched_chunks, run_build_process
from scripts.feniks.qdrant import upsert_points # For testing payload creation
from scripts.feniks.config import settings
from scripts.feniks.types import Chunk

# --- Unit Tests for Helper Functions ---

@patch('scripts.feniks_cli.subprocess.run')
def test_run_external_script_success(mock_run, caplog):
    """Tests that the external script helper logs stdout on success."""
    mock_run.return_value = MagicMock(stdout="success", stderr="", check_returncode=lambda: None)
    run_external_script(["echo", "hello"], cwd=Path("."))
    assert "success" in caplog.text

@patch('scripts.feniks_cli.subprocess.run')
def test_run_external_script_failure(mock_run, caplog):
    """Tests that the external script helper raises RuntimeError on failure."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
    with pytest.raises(RuntimeError):
        run_external_script(["bad_cmd"], cwd=Path("."))
    assert "Script failed" in caplog.text
    assert "error" in caplog.text

from scipy.sparse import csr_matrix

from scipy.sparse import csr_matrix
from scripts.feniks.types import GitInfo, MigrationSuggestion

def test_load_enriched_chunks_success(tmp_path: Path):
    """Tests successful loading and parsing of an enriched JSONL file."""
    jsonl_path = tmp_path / "enriched.jsonl"
    mock_data = {
        "id": "123", "filePath": "a/b.js", "start": 1, "end": 10,
        "text": "...", "name": "testChunk", "module": "testModule",
        "kind": "service", "cyclomatic_complexity": 5, "api_endpoints": ["/api/test"],
        "git_last_commit": {"hash": "abc", "author": "tester", "date": "2024-01-01", "summary": "test"},
        "migration_suggestion": {"target": "React Hook", "notes": "..."}
    }
    with jsonl_path.open("w") as f:
        f.write(json.dumps(mock_data) + "\n")

    chunks = load_enriched_chunks(jsonl_path)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.id == "123"
    assert chunk.module == "testModule"
    assert chunk.cyclomatic_complexity == 5
    assert chunk.api_endpoints == ["/api/test"]
    assert chunk.git_last_commit is not None and chunk.git_last_commit.author == "tester"
    assert chunk.migration_suggestion is not None and chunk.migration_suggestion.target == "React Hook"

def test_load_enriched_chunks_error(tmp_path: Path, caplog):
    """Tests that corrupted lines in JSONL are skipped and logged."""
    jsonl_path = tmp_path / "corrupted.jsonl"
    jsonl_path.write_text('not a json\n{"id": "123"}\n') # 1st line invalid, 2nd missing keys
    chunks = load_enriched_chunks(jsonl_path)
    assert len(chunks) == 0
    assert "Could not parse enriched chunk line" in caplog.text
    assert "not a json" in caplog.text
    assert "'filePath'" in caplog.text

# --- Unit Test for Qdrant Payload ---

def test_upsert_points_payload_creation():
    """Verify that the payload sent to Qdrant is correctly structured."""
    mock_client = MagicMock()
    
    # Create a full-featured chunk using real dataclasses
    git_info = GitInfo(hash='abc', author='test', date='2024', summary='commit')
    mig_sug = MigrationSuggestion(target='React', notes='...')

    mock_chunk = Chunk(
        id='1', file_path='a/b.js', start_line=1, end_line=1, text='some code', chunk_name='test',
        cyclomatic_complexity=10,
        git_last_commit=git_info,
        migration_suggestion=mig_sug
    )

    # Mock TF-IDF matrix to be sparse and have the correct shape
    tfidf_matrix = csr_matrix(([[1, 1]]), dtype=np.float64)

    upsert_points(mock_client, "test_coll", [mock_chunk], np.array([[0.1]*10]), tfidf_matrix, {'a': 0, 'b': 1})

    mock_client.upsert.assert_called_once()
    _, kwargs = mock_client.upsert.call_args
    payload = kwargs['points'][0].payload

    assert "text" not in payload  # Ensure large fields are excluded
    assert payload["cyclomatic_complexity"] == 10
    assert payload["git_last_commit"] == git_info.__dict__
    assert payload["migration_suggestion"] == mig_sug.__dict__


# --- Integration Test for the Full Pipeline ---

@patch('scripts.feniks_cli.run_external_script')
@patch('scripts.feniks_cli.get_embedding_model')
@patch('scripts.feniks_cli.QdrantClient')
def test_full_build_process(mock_qdrant_constructor, mock_get_model, mock_run_script, tmp_path, monkeypatch):
    """An end-to-end test verifying the main build process orchestration."""
    # --- Setup Mocks ---
    # 1. Mock settings to use a temporary directory
    monkeypatch.setattr(settings, 'PROJECT_ROOT', tmp_path)

    # 2. Mock the external script runner to create a fake enriched file
    def create_fake_output(cmd, cwd):
        try:
            out_index = cmd.index("--out") + 1
            out_path = Path(cmd[out_index])
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # The first script (indexer) creates the initial file with real text
            if "js_html_indexer" in cmd[1]:
                 with out_path.open("w") as f:
                    f.write('{"id": "1", "filePath": "a.js", "start": 1, "end": 1, "text": "function hello() { console.log(\'world\'); }", "name": "test1"}\n')
                    f.write('{"id": "2", "filePath": "b.js", "start": 1, "end": 1, "text": "function goodbye() { console.log(\'world\'); }", "name": "test2"}\n')
            # Subsequent scripts just pass the data through
            elif "--in" in cmd:
                 in_index = cmd.index("--in") + 1
                 in_path = Path(cmd[in_index])
                 if in_path.exists():
                    out_path.write_text(in_path.read_text())
        except (ValueError, IndexError):
            pass

    mock_run_script.side_effect = create_fake_output

    # 3. Mock embedding model to return 2 embeddings
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1]*10, [0.2]*10])
    mock_get_model.return_value = mock_model

    # 4. Mock Qdrant client
    mock_qdrant_instance = MagicMock()
    mock_qdrant_constructor.return_value = mock_qdrant_instance

    # --- Run Process ---
    # We need to wrap this in a try/except block because sys.exit(1) is called on error
    try:
        run_build_process(reset_collection=True)
    except SystemExit as e:
        pytest.fail(f"run_build_process exited unexpectedly with code {e.code}")


    # --- Assertions ---
    assert mock_run_script.call_count == 4
    mock_get_model.assert_called_once()
    mock_qdrant_constructor.assert_called_once()
    mock_qdrant_instance.delete_collection.assert_called_once()
    mock_qdrant_instance.create_collection.assert_called_once()
    mock_qdrant_instance.upsert.assert_called_once()
    
    _, kwargs = mock_qdrant_instance.upsert.call_args
    assert len(kwargs['points']) == 2
