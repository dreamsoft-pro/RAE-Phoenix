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

def test_load_enriched_chunks_success(tmp_path: Path):
    """Tests successful loading and parsing of an enriched JSONL file."""
    jsonl_path = tmp_path / "enriched.jsonl"
    mock_data = {
        "chunk_id": "123", "file_path": "a/b.js", "start_line": 1, "end_line": 10, 
        "text": "...", "code_snippet": "...", "chunk_name": "testChunk", "module": "testModule",
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
    assert chunk.git_last_commit.author == "tester"
    assert chunk.migration_suggestion.target == "React Hook"

def test_load_enriched_chunks_error(tmp_path: Path, caplog):
    """Tests that corrupted lines in JSONL are skipped and logged."""
    jsonl_path = tmp_path / "corrupted.jsonl"
    jsonl_path.write_text('not a json\n{"id": "123"}\n') # 1st line invalid, 2nd missing keys
    chunks = load_enriched_chunks(jsonl_path)
    assert len(chunks) == 0
    assert "Could not parse enriched chunk line" in caplog.text
    assert "not a json" in caplog.text
    assert "KeyError" in caplog.text

# --- Unit Test for Qdrant Payload ---

def test_upsert_points_payload_creation():
    """Verify that the payload sent to Qdrant is correctly structured."""
    mock_client = MagicMock()
    
    # Create a full-featured chunk
    mock_chunk = Chunk(
        id='1', file_path='a/b.js', start_line=1, end_line=1, text='some code', chunk_name='test',
        cyclomatic_complexity=10,
        git_last_commit=MagicMock(__dict__={'hash': 'abc'}),
        migration_suggestion=MagicMock(__dict__={'target': 'React'})
    )

    # Mock TF-IDF matrix to be sparse
    tfidf_matrix = MagicMock()
    tfidf_matrix.tocoo.return_value = MagicMock(col=[], data=[])

    upsert_points(mock_client, "test_coll", [mock_chunk], np.array([[0.1]*10]), tfidf_matrix, {{}})

    mock_client.upsert.assert_called_once()
    _, kwargs = mock_client.upsert.call_args
    payload = kwargs['points'][0].payload

    assert "text" not in payload  # Ensure large fields are excluded
    assert payload["cyclomatic_complexity"] == 10
    assert payload["git_last_commit"] == {'hash': 'abc'}
    assert payload["migration_suggestion"] == {'target': 'React'}


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
    enriched_chunks_path = tmp_path / "runs" / "latest" / "chunks.enriched.jsonl"
    def create_fake_output(cmd, cwd):
        if "js_html_indexer" in cmd[1]:
            # The indexer is called, but we only care about the final enriched file
            pass
        elif "enrich_git_blame" in cmd[1]:
            # The enricher is called, create its output file
            enriched_chunks_path.parent.mkdir(parents=True, exist_ok=True)
            with enriched_chunks_path.open("w") as f:
                f.write('{"chunk_id": "1", "file_path": "a.js", "start_line": 1, "end_line": 1, "text": "...", "code_snippet": "...", "chunk_name": "test"}\n')
    mock_run_script.side_effect = create_fake_output

    # 3. Mock embedding model
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1]*10])
    mock_get_model.return_value = mock_model

    # 4. Mock Qdrant client
    mock_qdrant_instance = MagicMock()
    mock_qdrant_constructor.return_value = mock_qdrant_instance

    # --- Run Process ---
    run_build_process(reset_collection=True)

    # --- Assertions ---
    # Assert that both external scripts were called
    assert mock_run_script.call_count == 2
    
    # Assert that embedding and Qdrant functions were called
    mock_get_model.assert_called_once()
    mock_qdrant_constructor.assert_called_once()
    mock_qdrant_instance.delete_collection.assert_called_once()
    mock_qdrant_instance.upsert.assert_called_once()
