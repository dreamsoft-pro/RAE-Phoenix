
import pytest
import argparse
import numpy as np # Import numpy
from pathlib import Path

from scripts.build_kb import cmd_index

@pytest.fixture
def mock_repo_for_ignore_test(tmp_path: Path) -> Path:
    """
    Creates a temporary directory structure with AngularJS-style code that the indexer can parse.
    """
    core_path = tmp_path / "app" / "src" / "core"
    core_path.mkdir(parents=True)

    (core_path / "core.js").write_text(
        """ 
        angular.module('core').controller('CoreController', function($scope) { 
            // This is the core controller 
        });
        """
    )
    (core_path / "core_service.js").write_text(
        """
        angular.module('core').service('CoreService', function(CoreApi) {
            // This is the core service
        });
        """
    )

    (tmp_path / ".feniksignore").write_text("vendor/")
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "jquery.js").write_text("// ignored")

    return tmp_path

def test_ignore_logic_and_indexing(mocker, mock_repo_for_ignore_test: Path):
    """
    Final test: Verifies that .feniksignore works AND the pipeline successfully
    indexes the remaining files, fixing the 'empty vocabulary' error.
    """
    mocker.patch('scripts.build_kb.QdrantClient')
    mocker.patch('scripts.build_kb.ensure_collection')
    mock_upsert_points = mocker.patch('scripts.build_kb.upsert_points')
    mocker.patch('scripts.build_kb.get_embedding_model')
    # CORRECTED MOCK: Return a single numpy array, as the real function does.
    mock_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    mocker.patch('scripts.build_kb.create_dense_embeddings', return_value=mock_embeddings)

    args = argparse.Namespace(
        root=str(mock_repo_for_ignore_test),
        out=str(mock_repo_for_ignore_test / "output"),
        collection="final_test_collection",
        host="localhost", port=6333, model="mock_model",
        reset=True, write_ignores=False, verbose=True
    )

    # This should now complete without any errors
    cmd_index(args)

    # Assert that chunks were generated and passed to upsert
    mock_upsert_points.assert_called_once()
    call_args, _ = mock_upsert_points.call_args
    upserted_chunks = call_args[2]

    assert len(upserted_chunks) == 2, "Expected exactly two chunks from the two core files"

    chunk_names = {c.chunk_name for c in upserted_chunks}
    assert "CoreController" in chunk_names
    assert "CoreService" in chunk_names
