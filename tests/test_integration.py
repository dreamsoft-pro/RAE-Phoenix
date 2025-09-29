import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
from pydantic import ValidationError as PydanticValidationError

from scripts.feniks_cli import run_build_process
from feniks.config import settings

@pytest.fixture
def mock_frontend_repo(tmp_path: Path) -> Path:
    """Creates a temporary mock frontend repository structure."""
    src_path = tmp_path / "app" / "src" / "index"
    src_path.mkdir(parents=True)
    (src_path / "test.controller.js").write_text(
        """
        angular.module('testApp').controller('TestCtrl', function($scope) {});
        """
    )
    (src_path / "test.template.html").write_text("<div>Hello</div>")
    return tmp_path

def test_full_build_pipeline(mock_frontend_repo: Path, monkeypatch):
    """
    Integration test for the full build pipeline.
    """
    # Override settings for the test
    monkeypatch.setattr(settings, 'FRONTEND_ROOT', mock_frontend_repo)
    monkeypatch.setattr(settings, 'OUTPUT_DIR', mock_frontend_repo / "output")
    monkeypatch.setattr(settings, 'QDRANT_HOST', 'localhost') # Avoid actual network
    monkeypatch.setenv("FENIKS_TEST_MIN_DF", "1")

    with patch('scripts.feniks.qdrant.QdrantClient') as mock_qdrant_client_constructor, \
         patch('scripts.feniks.embed.SentenceTransformer') as mock_st_constructor, \
         patch('scripts.feniks.parser.run_ast_indexer') as mock_run_ast_indexer, \
         patch('scripts.feniks_cli.get_blame_for_chunk') as mock_get_blame:

        # Mock instances
        mock_qdrant_instance = MagicMock()
        mock_qdrant_client_constructor.return_value = mock_qdrant_instance

        mock_model_instance = MagicMock()
        mock_model_instance.get_sentence_embedding_dimension.return_value = 384
        mock_model_instance.encode.return_value = [[0.1] * 384] * 2 # 2 chunks
        mock_st_constructor.return_value = mock_model_instance

        # Mock the indexer to return a predictable chunks.jsonl
        chunks_jsonl_path = mock_frontend_repo / "output" / "data" / "chunks.jsonl"
        chunks_jsonl_path.parent.mkdir(parents=True)
        with chunks_jsonl_path.open("w") as f:
            f.write('{"file_path": "app/src/index/test.controller.js", "chunk_name": "TestCtrl", "ast_node_type": "CallExpression", "code_snippet": "...", "start_line": 1, "end_line": 2, "dependencies_di": []}\n')
            f.write('{"file_path": "app/src/index/test.template.html", "chunk_name": "html_section", "ast_node_type": "NgTemplate", "code_snippet": "...", "start_line": 1, "end_line": 2, "dependencies_di": []}\n')
        mock_run_ast_indexer.return_value = chunks_jsonl_path

        # Run the main build process
        run_build_process(reset_collection=True)

        # Assertions
        mock_run_ast_indexer.assert_called_once()
        mock_st_constructor.assert_called_with(settings.EMBEDDING_MODEL)
        mock_qdrant_client_constructor.assert_called_with(host='localhost', port=settings.QDRANT_PORT)
        
        mock_qdrant_instance.delete_collection.assert_called_once_with(settings.QDRANT_COLLECTION)
        mock_qdrant_instance.create_collection.assert_called_once()
        mock_qdrant_instance.upsert.assert_called_once()

        # Check if upsert was called with 2 points
        _, kwargs = mock_qdrant_instance.upsert.call_args
        assert len(kwargs['points']) == 2

        # Check if git blame was called for each chunk
        assert mock_get_blame.call_count == 2


def test_ensure_collection_with_reset():
    """Tests that ensure_collection correctly resets an existing collection."""
    from scripts.feniks.qdrant import ensure_collection

    mock_client = MagicMock()
    # Simulate collection exists
    mock_client.get_collection.return_value = True

    ensure_collection(client=mock_client, name="test_coll", dim=10, reset=True)

    mock_client.delete_collection.assert_called_once_with("test_coll")
    mock_client.create_collection.assert_called_once()


@patch('scripts.feniks.qdrant.QdrantClient')
def test_upsert_fallback_on_pydantic_error(mock_qdrant_client_constructor, caplog):
    """Tests the fallback mechanism on PydanticValidationError during upsert."""
    from scripts.feniks.qdrant import upsert_points
    mock_client = MagicMock()
    mock_qdrant_client_constructor.return_value = mock_client

    # First call raises Pydantic error, second succeeds
    mock_client.upsert.side_effect = [
        PydanticValidationError.from_exception_data(title="dummy", line_errors=[]),
        None
    ]

    # Dummy data
    chunks = [MagicMock()] * 2
    dense_embs = np.array([[0.1] * 10] * 2)
    tfidf_matrix = MagicMock()
    tfidf_matrix.tocoo.return_value = MagicMock(col=[], data=[])

    upsert_points(mock_client, "test_coll", chunks, dense_embs, tfidf_matrix, {})

    assert mock_client.upsert.call_count == 2
    assert "falling back to dense-only" in caplog.text


@patch('scripts.feniks.qdrant.QdrantClient')
def test_upsert_fallback_on_generic_error(mock_qdrant_client_constructor, caplog):
    """Tests the fallback mechanism on a generic Exception during upsert."""
    from scripts.feniks.qdrant import upsert_points
    mock_client = MagicMock()
    mock_qdrant_client_constructor.return_value = mock_client

    # First call raises a generic error, second succeeds
    mock_client.upsert.side_effect = [Exception("some generic error"), None]

    # Dummy data
    chunks = [MagicMock()] * 2
    dense_embs = np.array([[0.1] * 10] * 2)
    tfidf_matrix = MagicMock()
    tfidf_matrix.tocoo.return_value = MagicMock(col=[], data=[])

    upsert_points(mock_client, "test_coll", chunks, dense_embs, tfidf_matrix, {})

    assert mock_client.upsert.call_count == 2
    assert "Dense+sparse upsert failed" in caplog.text