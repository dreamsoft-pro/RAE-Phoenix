import logging
import subprocess
import json
from pathlib import Path
import pytest
from feniks.utils import sha1, extract_module_from_path
from feniks.parser import (
    run_ast_indexer,
    load_chunks_from_jsonl
)
from feniks.types import Chunk
from feniks.kb_builder import build_module_cards_from_chunks
from feniks.git_utils import get_blame_for_chunk
from feniks.logger import setup_logger
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_chunks_jsonl(tmp_path: Path) -> Path:
    """Creates a temporary chunks.jsonl file for testing."""
    jsonl_path = tmp_path / "chunks.jsonl"
    chunks_data = [
        {
            "chunk_id": "1",
            "file_path": "/app/src/cart/services/CartService.js",
            "chunk_name": "CartService",
            "ast_node_type": "CallExpression",
            "dependencies_di": ["$http", "API"],
            "code_snippet": "angular.module('cart').service('CartService', ...)",
            "start_line": 10,
            "end_line": 25,
            "api_endpoints": ["/api/cart/items"],
            "migration_suggestion": { "target": "Custom Hook" }
        },
        {
            "chunk_id": "2",
            "file_path": "/app/src/cart/controllers/CartCtrl.js",
            "chunk_name": "CartCtrl",
            "ast_node_type": "CallExpression",
            "dependencies_di": ["$scope", "CartService"],
            "code_snippet": "angular.module('cart').controller('CartCtrl', ...)",
            "start_line": 5,
            "end_line": 30,
        },
        {
            "chunk_id": "3",
            "file_path": "/app/src/index/controllers/HomeCtrl.js",
            "chunk_name": "HomeCtrl",
            "ast_node_type": "CallExpression",
            "dependencies_di": ["$scope"],
            "code_snippet": "angular.module('index').controller('HomeCtrl', ...)",
            "start_line": 1,
            "end_line": 15,
        },
        {
            "chunk_id": "4",
            "file_path": "/app/src/cart/views/cart.html",
            "chunk_name": "cart.html",
            "ast_node_type": "NgTemplate",
            "dependencies_di": [],
            "code_snippet": "<div>...</div>",
            "start_line": 1,
            "end_line": 50,
        },
        {
            "chunk_id": "5",
            "file_path": "/app/src/cart/directives/cartDirective.js",
            "chunk_name": "cartDirective",
            "ast_node_type": "CallExpression",
            "dependencies_di": [],
            "code_snippet": "angular.module('cart').directive('cartDirective', ...)",
            "start_line": 1, "end_line": 10
        },
        {
            "chunk_id": "6",
            "file_path": "/app/src/cart/factories/cartFactory.js",
            "chunk_name": "cartFactory",
            "ast_node_type": "CallExpression",
            "dependencies_di": [],
            "code_snippet": "angular.module('cart').factory('cartFactory', ...)",
            "start_line": 1, "end_line": 10
        },
    ]
    with jsonl_path.open("w", encoding="utf-8") as f:
        for chunk in chunks_data:
            f.write(json.dumps(chunk) + "\n")
    return jsonl_path


def test_load_chunks_from_jsonl(mock_chunks_jsonl: Path):
    """Tests that chunks are loaded correctly from a JSONL file."""
    chunks = load_chunks_from_jsonl(mock_chunks_jsonl)
    assert len(chunks) == 6
    
    # Test the first chunk (CartService)
    cart_service_chunk = chunks[0]
    assert cart_service_chunk.id == "1"
    assert cart_service_chunk.module == "cart"
    assert cart_service_chunk.chunk_name == "CartService"
    assert cart_service_chunk.kind == "js_function"
    assert "$http" in cart_service_chunk.dependencies_di
    assert "API" in cart_service_chunk.dependencies_di
    assert cart_service_chunk.start_line == 10
    assert cart_service_chunk.api_endpoints == ["/api/cart/items"]
    assert cart_service_chunk.migration_suggestion["target"] == "Custom Hook"

    # Test the html chunk
    html_chunk = chunks[3]
    assert html_chunk.module == "cart"
    assert html_chunk.kind == "html_section"
    assert html_chunk.ast_node_type == "NgTemplate"


def test_build_module_cards_from_chunks(mock_chunks_jsonl: Path):
    """Tests the aggregation of chunks into module cards."""
    chunks = load_chunks_from_jsonl(mock_chunks_jsonl)
    module_cards = build_module_cards_from_chunks(chunks)

    assert "cart" in module_cards
    assert "index" in module_cards

    cart_card = module_cards["cart"]
    assert cart_card["module"] == "cart"
    assert cart_card["services"] == ["CartService"]
    assert cart_card["controllers"] == ["CartCtrl"]
    assert cart_card["templates"] == ["cart.html"]
    assert cart_card["directives"] == ["cartDirective"]
    assert cart_card["factories"] == ["cartFactory"]
    assert len(cart_card["files"]) == 5 # Service, Controller, Template, Directive, Factory

    index_card = module_cards["index"]
    assert index_card["module"] == "index"
    assert index_card["controllers"] == ["HomeCtrl"]
    assert not index_card["services"]
    assert len(index_card["files"]) == 1


@pytest.mark.parametrize("path_str, expected_module", [
    ("app/src/cart/services/service.js", "cart"),
    ("/abs/path/to/app/src/index/ctrl.js", "index"),
    ("app/src/client-zone/client.js", "client-zone"),
    ("app/src/layout/header.html", "layout"),
    ("app/src/app.js", None), # No module
    ("frontend/app/src/photo-folders/directives/a.js", "photo-folders"),
    ("random/path/file.js", None),
])
def test_extract_module_from_path(path_str, expected_module):
    """Tests the module extraction logic from a file path."""
    path = Path(path_str)
    assert extract_module_from_path(path) == expected_module

def test_sha1_consistency():
    """
    Tests that the sha1 function produces a consistent, expected hash for a given string.
    """
    input_string = "hello world"
    expected_hash = "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"

    actual_hash = sha1(input_string)

    assert actual_hash == expected_hash

def test_sha1_empty_string():
    """
    Tests that the sha1 function correctly handles an empty string.
    """
    input_string = ""
    # SHA1 hash for an empty string
    expected_hash = "da39a3ee5e6b4b0d3255bfef95601890afd80709"

    actual_hash = sha1(input_string)

    assert actual_hash == expected_hash

def test_sha1_different_strings():
    """
    Tests that different input strings produce different hashes.
    """
    hash1 = sha1("string one")
    hash2 = sha1("string two")

    assert hash1 != hash2


def test_load_chunks_from_empty_file(tmp_path: Path):
    """Tests that loading from an empty or invalid JSONL file returns an empty list."""
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("\n  \n") # Empty lines
    assert load_chunks_from_jsonl(empty_file) == []

    invalid_json_file = tmp_path / "invalid.jsonl"
    invalid_json_file.write_text("this is not json")
    assert load_chunks_from_jsonl(invalid_json_file) == []


def test_build_module_cards_from_empty_chunks():
    """Tests that building cards from an empty list of chunks returns an empty dict."""
    assert build_module_cards_from_chunks([]) == {}


def test_module_extraction_no_module():
    """Tests that no module is extracted if the path doesn't match."""
    path = Path("/some/other/structure/file.js")
    assert extract_module_from_path(path) is None


@patch('scripts.feniks.parser.subprocess.run')
def test_run_ast_indexer_failure(mock_subprocess_run):
    """Tests that run_ast_indexer raises RuntimeError on subprocess failure."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
    with pytest.raises(RuntimeError):
        run_ast_indexer(Path("/tmp"))


def test_load_chunks_with_missing_key(tmp_path: Path, caplog):
    """Tests parsing a JSONL file with a missing required key."""
    jsonl_path = tmp_path / "missing_key.jsonl"
    # 'file_path' is missing
    jsonl_path.write_text('{"chunk_name": "Test", "ast_node_type": "A", "code_snippet": "...", "start_line": 1, "end_line": 2}\n')
    chunks = load_chunks_from_jsonl(jsonl_path)
    assert chunks == []
    assert "Could not parse line" in caplog.text


# --- Tests for git_utils.py ---

@patch('scripts.feniks.git_utils.subprocess.run')
def test_get_blame_for_chunk_success(mock_run):
    """Tests successful parsing of git blame output."""
    mock_output = (
        "a1b2c3d4 (John Doe 2023-10-27 10:00:00 +0200 1)\n"
        "author John Doe\n"
        "summary fix: handle null price\n"
    )
    mock_run.return_value = MagicMock(stdout=mock_output, check_returncode=lambda: None)
    
    mock_chunk = Chunk(
        id='1', file_path='app/app.js', start_line=1, end_line=10, text='',
        module='test', chunk_name='test', kind='service', ast_node_type='CallExpression',
        dependencies_di=[], anti_patterns=[]
    )
    # Create a dummy file for the exists() check
    with patch.object(Path, 'exists', return_value=True):
        git_info = get_blame_for_chunk(mock_chunk, repo_root=Path("/fake/repo"))

    assert git_info is not None
    assert git_info["hash"] == "a1b2c3d4"
    assert git_info["author"] == "John Doe"
    assert git_info["summary"] == "fix: handle null price"

@patch('scripts.feniks.git_utils.subprocess.run')
def test_get_blame_for_chunk_error(mock_run, caplog):
    """Tests that blame failure is handled gracefully."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
    mock_chunk = Chunk(
        id='1', file_path='app/app.js', start_line=1, end_line=10, text='',
        module='test', chunk_name='test', kind='service', ast_node_type='CallExpression',
        dependencies_di=[], anti_patterns=[]
    )
    with patch.object(Path, 'exists', return_value=True):
        git_info = get_blame_for_chunk(mock_chunk, repo_root=Path("/fake/repo"))
    
    assert git_info is None
    assert "Could not run git blame" in caplog.text

def test_get_blame_for_chunk_no_file():
    """Tests that no blame is attempted for a non-existent file."""
    mock_chunk = Chunk(
        id='1', file_path='nonexistent.js', start_line=1, end_line=1, text='',
        module='test', chunk_name='test', kind='service', ast_node_type='CallExpression',
        dependencies_di=[], anti_patterns=[]
    )
    with patch.object(Path, 'exists', return_value=False):
        git_info = get_blame_for_chunk(mock_chunk, repo_root=Path("/fake/repo"))
    assert git_info is None


def test_logger_avoids_duplicate_handlers():
    """Ensures the logger setup is truly idempotent by pre-adding a handler."""
    # Get the logger and manually add a handler
    logger = logging.getLogger("feniks_kb")
    # Clear existing handlers from previous tests if any
    if logger.hasHandlers():
        logger.handlers.clear()
    
    dummy_handler = logging.NullHandler()
    logger.addHandler(dummy_handler)
    assert len(logger.handlers) == 1

    # Run the setup function again
    setup_logger()

    # It should not add a new handler
    assert len(logger.handlers) == 1
    # Clean up
    logger.removeHandler(dummy_handler)
