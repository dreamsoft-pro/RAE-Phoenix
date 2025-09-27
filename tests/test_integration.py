import pytest
import argparse
from pathlib import Path

from scripts.build_kb import cmd_index, KBConfig

@pytest.fixture
def mock_frontend_repo(tmp_path: Path) -> Path:
    """Creates a temporary mock frontend repository structure."""
    src_path = tmp_path / "app" / "src" / "index"
    src_path.mkdir(parents=True)

    # Mock JS file with a simple AngularJS controller
    (src_path / "test.controller.js").write_text(
        """
        /**
         * This is a test controller.
         */
        angular.module('testApp').controller('TestCtrl', ['$scope', function($scope) {
            $scope.message = 'Hello, World!';
        }]);
        """
    )

    # Mock HTML file
    (src_path / "test.template.html").write_text(
        """
        <div class="container">
            <h1>Test Template</h1>
            <p>{{ message }}</p>
        </div>
        """
    )
    return tmp_path

def test_full_indexing_pipeline(mocker, mock_frontend_repo: Path):
    """
    Integration test for the full indexing pipeline.
    It mocks external services to avoid network calls.
    """
    # Mock Qdrant client to prevent actual DB operations
    mocker.patch('scripts.build_kb.QdrantClient')
    mock_ensure_collection = mocker.patch('scripts.build_kb.ensure_collection')
    mock_upsert_points = mocker.patch('scripts.build_kb.upsert_points')

    # Mock the model loading and embedding functions to prevent network calls and speed up the test.
    # We patch them in 'scripts.build_kb' because that's where they are imported and called from.
    mock_model_instance = mocker.MagicMock()
    mock_model_instance.get_sentence_embedding_dimension.return_value = 768
    mocker.patch('scripts.build_kb.get_embedding_model', return_value=mock_model_instance)
    mocker.patch('scripts.build_kb.create_dense_embeddings', return_value=mocker.MagicMock())

    # Simulate command line arguments
    args = argparse.Namespace(
        root=str(mock_frontend_repo),
        out=".",
        collection="test_collection",
        host="localhost",
        port=6333,
        model="mock_model",
        reset=True,
        write_ignores=False
    )

    # Run the main indexing command
    cmd_index(args)

    # Assert that the key functions were called, verifying the pipeline flow
    mock_ensure_collection.assert_called_once()
    mock_upsert_points.assert_called_once()

    # Check if upsert was called with a reasonable number of chunks
    # Based on the mock files, we expect 1 JS chunk and 1 HTML chunk.
    call_args, _ = mock_upsert_points.call_args
    upserted_chunks = call_args[2] # chunks is the 3rd argument
    assert len(upserted_chunks) > 0
    assert len(upserted_chunks) <= 5 # Flexible check for number of chunks

    # Verify that a js chunk was created
    assert any(c.kind == "js_function" for c in upserted_chunks)
    # Verify that an html chunk was created
    assert any(c.kind == "html_section" for c in upserted_chunks)
    # Verify that comments were extracted
    js_chunk = next(c for c in upserted_chunks if c.kind == "js_function")
    assert "This is a test controller" in js_chunk.text