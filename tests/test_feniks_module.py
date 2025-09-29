import hashlib
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from pydantic import ValidationError as PydanticValidationError

# Add project root to path to allow imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.feniks.utils import ensure_dir, sha1, extract_module_from_path
from scripts.feniks.logger import setup_logger
from scripts.feniks.qdrant import ensure_collection, upsert_points
from scripts.feniks.types import Chunk

# --- Tests for utils.py ---

def test_ensure_dir(tmp_path: Path):
    """Tests that ensure_dir creates a directory."""
    dir_path = tmp_path / "new_dir"
    assert not dir_path.exists()
    ensure_dir(dir_path)
    assert dir_path.exists()
    assert dir_path.is_dir()

def test_sha1():
    """Tests the sha1 hashing function."""
    assert sha1("hello world") == hashlib.sha1(b"hello world").hexdigest()

@pytest.mark.parametrize("path_str, expected", [
    ("app/src/my_module/file.js", "my_module"),
    ("/abs/path/app/src/another_module/service.js", "another_module"),
    ("app/src/file.js", None),
    ("no/module/here.js", None),
    ("", None)
])
def test_extract_module_from_path(path_str, expected):
    """Tests the module extraction logic."""
    path = Path(path_str)
    assert extract_module_from_path(path) == expected

# --- Tests for logger.py ---

def test_setup_logger_is_singleton():
    """Tests the logger setup and singleton behavior."""
    logger1 = setup_logger()
    logger2 = setup_logger()
    assert logger1 is logger2

# --- Tests for qdrant.py ---

def test_ensure_collection_does_nothing_if_exists(mocker):
    """Tests that ensure_collection does nothing if the collection exists and reset is False."""
    mock_client = MagicMock()
    mock_client.get_collection.return_value = True # Simulate collection exists
    
    ensure_collection(mock_client, "test_coll", 10, reset=False)

    mock_client.get_collection.assert_called_once_with("test_coll")
    mock_client.delete_collection.assert_not_called()
    mock_client.create_collection.assert_not_called()

def test_ensure_collection_resets_if_exists(mocker):
    """Tests that ensure_collection deletes and recreates the collection if reset is True."""
    mock_client = MagicMock()
    mock_client.get_collection.return_value = True # Simulate collection exists
    
    ensure_collection(mock_client, "test_coll", 10, reset=True)

    mock_client.get_collection.assert_called_once()
    mock_client.delete_collection.assert_called_once_with("test_coll")
    mock_client.create_collection.assert_called_once()

def test_upsert_points_fallback(mocker, caplog):
    """Tests that upsert_points falls back to dense-only if sparse vectors fail."""
    mock_client = MagicMock()
    # First call (hybrid) fails with a generic exception, second call succeeds
    mock_client.upsert.side_effect = [Exception("sparse vectors not supported"), None]

    mock_chunk = Chunk(id='1', file_path='a.js', start_line=1, end_line=1, text='code', chunk_name='test')
    
    with caplog.at_level(logging.WARNING):
        upsert_points(
            client=mock_client,
            collection="test_coll",
            chunks=[mock_chunk],
            dense=MagicMock(__getitem__=lambda _, __: np.array([0.1]*10)),
            X_tfidf=MagicMock(shape=(1,1), tocoo=lambda: MagicMock(col=[], data=[])),
            vocab={}
        )

    assert mock_client.upsert.call_count == 2
    assert "Retrying with dense-only" in caplog.text
