import pytest
import argparse
from pathlib import Path

from scripts.build_kb import cmd_index

@pytest.fixture
def mock_repo_for_ignore_test(tmp_path: Path) -> Path:
    """
    Creates a temporary directory structure to test the .feniksignore functionality.

    Structure:
    /tmp_path
    |-- .feniksignore
    |-- app/
    |   |-- src/
    |   |   |-- core/
    |   |   |   |-- core.js          # Should be indexed
    |   |-- assets/
    |   |   |-- libraries/
    |   |   |   |-- jquery.js        # Should be ignored
    |   |   |-- css/
    |   |   |   |-- app.css          # Should be indexed (as it's not .html or .js)
    |-- vendor/
    |   |-- some_lib.js              # Should be ignored
    |-- test.spec.js                 # Should be ignored
    """
    # Create .feniksignore
    (tmp_path / ".feniksignore").write_text(
        """
# Ignore standard vendor directories
vendor/
app/assets/libraries/

# Ignore test files
**/*.spec.js
        """
    )

    # Create files to be indexed
    core_path = tmp_path / "app" / "src" / "core"
    core_path.mkdir(parents=True)
    (core_path / "core.js").write_text("angular.module('core', []);")

    # Create files to be ignored
    libs_path = tmp_path / "app" / "assets" / "libraries"
    libs_path.mkdir(parents=True)
    (libs_path / "jquery.js").write_text("/* jQuery library */");

    vendor_path = tmp_path / "vendor"
    vendor_path.mkdir(parents=True)
    (vendor_path / "some_lib.js").write_text("/* Some vendor lib */");

    (tmp_path / "test.spec.js").write_text("describe('a test', () => {});");

    # Create a file that should NOT be ignored (to check for false positives)
    css_path = tmp_path / "app" / "assets" / "css"
    css_path.mkdir(parents=True)
    (css_path / "app.css").write_text("body { color: red; }") # Not .js or .html, so won't be chunked

    return tmp_path


def test_ignore_logic(mocker, mock_repo_for_ignore_test: Path):
    """
    Integration test to verify that the .feniksignore functionality works correctly.
    """
    # We will let the Node.js script run to test the ignore logic,
    # but we will mock the services that require network access.

    # We need to get the list of files passed to the indexer
    # For this test, we can directly call the Node script logic via a helper
    # or check the results from the mocked call. Let's inspect the results.

    # Since we can't easily inspect inside the node script, we will check
    # the output files. The easiest is to let it run and check the result.
    mocker.patch('scripts.build_kb.QdrantClient')
    mocker.patch('scripts.build_kb.ensure_collection')
    mock_upsert_points = mocker.patch('scripts.build_kb.upsert_points')
    mocker.patch('scripts.build_kb.get_embedding_model')
    mocker.patch('scripts.build_kb.create_dense_embeddings')

    args = argparse.Namespace(
        root=str(mock_repo_for_ignore_test),
        out=str(mock_repo_for_ignore_test / "output"),
        collection="ignore_test_collection",
        host="localhost",
        port=6333,
        model="mock_model",
        reset=True,
        write_ignores=False
    )

    cmd_index(args)

    # Now, let's verify what chunks were created.
    # We expect only one chunk from app/src/core/core.js
    mock_upsert_points.assert_called_once()

    call_args, _ = mock_upsert_points.call_args
    upserted_chunks = call_args[2] # chunks is the 3rd argument

    assert len(upserted_chunks) == 1

    indexed_file_path = upserted_chunks[0].file_path
    assert indexed_file_path == "app/src/core/core.js"
    assert "jquery.js" not in [c.file_path for c in upserted_chunks]
    assert "some_lib.js" not in [c.file_path for c in upserted_chunks]
    assert "test.spec.js" not in [c.file_path for c in upserted_chunks]