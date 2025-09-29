import json
from pathlib import Path
import pytest
from scripts.feniks.core import (
    sha1,
    load_chunks_from_jsonl,
    build_module_cards_from_chunks,
    extract_module_from_path,
)
from scripts.feniks.types import Chunk


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
    ]
    with jsonl_path.open("w", encoding="utf-8") as f:
        for chunk in chunks_data:
            f.write(json.dumps(chunk) + "\n")
    return jsonl_path


def test_load_chunks_from_jsonl(mock_chunks_jsonl: Path):
    """Tests that chunks are loaded correctly from a JSONL file."""
    chunks = load_chunks_from_jsonl(mock_chunks_jsonl)
    assert len(chunks) == 4
    
    # Test the first chunk (CartService)
    cart_service_chunk = chunks[0]
    assert cart_service_chunk.id == "1"
    assert cart_service_chunk.module == "cart"
    assert cart_service_chunk.chunk_name == "CartService"
    assert cart_service_chunk.kind == "js_function"
    assert "$http" in cart_service_chunk.dependencies_di
    assert "API" in cart_service_chunk.dependencies_di
    assert cart_service_chunk.start_line == 10

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
    assert len(cart_card["files"]) == 3 # Service, Controller, Template

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
