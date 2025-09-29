
import pytest
from pathlib import Path
from src.feniks.types import Chunk
from src.feniks.core import extract_module_from_path, build_module_cards_from_chunks

# --- Test data for `extract_module_from_path` ---
@pytest.mark.parametrize("path_str, expected_module", [
    ("app/src/cart/services/CartService.js", "cart"),
    ("/home/user/project/app/src/client-zone/controllers/ProfileCtrl.js", "client-zone"),
    ("app/src/index/index.module.js", "index"),
    ("app/src/shared/directives/someDirective.js", "shared"), # This is a valid module
    ("random/path/without/module.js", None),
    ("", None)
])
def test_extract_module_from_path(path_str, expected_module):
    """
    Tests that `extract_module_from_path` correctly identifies the module name
    from various file path formats.
    """
    path = Path(path_str)
    assert extract_module_from_path(path) == expected_module

# --- Test data for `build_module_cards_from_chunks` ---
def test_build_module_cards_from_chunks():
    """
    Tests that `build_module_cards_from_chunks` correctly aggregates chunk information
    into structured module cards.
    """
    # Create a list of mock Chunk objects
    mock_chunks = [
        Chunk(id="1", file_path="app/src/cart/services/CartService.js", module="cart", chunk_name="CartService",
              kind="js_function", ast_node_type="CallExpression", dependencies_di=[], anti_patterns=[],
              text="...", start_line=1, end_line=10),
        Chunk(id="2", file_path="app/src/cart/controllers/CartCtrl.js", module="cart", chunk_name="CartCtrl",
              kind="js_function", ast_node_type="CallExpression", dependencies_di=[], anti_patterns=[],
              text="...", start_line=5, end_line=25),
        Chunk(id="3", file_path="app/src/cart/views/cart.html", module="cart", chunk_name="cart_template",
              kind="html_section", ast_node_type="NgTemplate", dependencies_di=[], anti_patterns=[],
              text="...", start_line=1, end_line=50),
        Chunk(id="4", file_path="app/src/index/index.module.js", module="index", chunk_name="SomeFactory",
              kind="js_function", ast_node_type="CallExpression", dependencies_di=[], anti_patterns=[],
              text="...", start_line=1, end_line=15),
        Chunk(id="5", file_path="app/src/no_module/service.js", module="-", chunk_name="NoModuleService",
              kind="js_function", ast_node_type="CallExpression", dependencies_di=[], anti_patterns=[],
              text="...", start_line=1, end_line=10),
    ]

    # Execute the function
    module_cards = build_module_cards_from_chunks(mock_chunks)

    # --- Assertions ---
    # Check if all modules are present
    assert "cart" in module_cards
    assert "index" in module_cards
    assert "-" in module_cards
    assert len(module_cards) == 3

    # Check the 'cart' module card
    cart_card = module_cards["cart"]
    assert cart_card["module"] == "cart"
    assert sorted(cart_card["services"]) == ["CartService"]
    assert sorted(cart_card["controllers"]) == ["CartCtrl"]
    assert sorted(cart_card["templates"]) == ["cart.html"]
    assert len(cart_card["files"]) == 3

    # Check the 'index' module card
    index_card = module_cards["index"]
    assert index_card["module"] == "index"
    assert sorted(index_card["factories"]) == ["SomeFactory"] # Based on 'in name' logic
    assert len(index_card["files"]) == 1

    # Check the 'no_module' card (represented by '-')
    no_module_card = module_cards["-"]
    assert no_module_card["module"] == "-"
    assert sorted(no_module_card["services"]) == ["NoModuleService"]
    assert len(no_module_card["files"]) == 1
