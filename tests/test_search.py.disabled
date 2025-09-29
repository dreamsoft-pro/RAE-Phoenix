import argparse
from unittest.mock import MagicMock, patch
import pytest
from qdrant_client.models import ScoredPoint, Filter

from scripts.build_kb import cmd_search

@pytest.fixture
def mock_qdrant_client():
    """Mocks the QdrantClient."""
    client = MagicMock()
    
    # Mock the nested attribute access needed by the test
    mock_collection_info = MagicMock()
    mock_collection_info.config.params.vectors = {
        "dense_code": MagicMock(size=384)
    }
    client.get_collection.return_value = mock_collection_info

    # Mock search response
    search_results = [
        ScoredPoint(id=2, version=1, score=0.8, payload={'file_path': 'app/src/cart/CartService.js', 'ast_node_type': 'service', 'dependencies_di': ['AuthService']}),
    ]
    client.search.return_value = search_results
    
    return client

@pytest.fixture
def mock_sentence_transformer():
    """Mocks the SentenceTransformer model."""
    model = MagicMock()
    model.get_sentence_embedding_dimension.return_value = 384
    model.encode.return_value = [[0.1] * 384]
    return model

def test_cmd_search_flow(capsys, mock_qdrant_client, mock_sentence_transformer):
    """
    Tests the main flow of the cmd_search function, including client calls and output.
    """
    with patch('scripts.build_kb.QdrantClient', return_value=mock_qdrant_client), \
         patch('scripts.build_kb.SentenceTransformer', return_value=mock_sentence_transformer):

        args = argparse.Namespace(
            query="find auth service",
            collection="test_collection",
            host="localhost",
            port=6333,
            model="mock_model",
            topk=3,
            alpha=0.7,
            mode="js",
            deps=["AuthService"],
            paths_include=["app/src/"],
            ast_types=["service"],
            modules="all",
            no_translate=False
        )

        cmd_search(args)

        # 1. Verify Qdrant client was called correctly
        mock_qdrant_client.get_collection.assert_called_with("test_collection")
        
        # Check that search was called
        mock_qdrant_client.search.assert_called_once()
        call_args, call_kwargs = mock_qdrant_client.search.call_args
        
        # Check the query filter
        query_filter = call_kwargs.get('query_filter')
        assert isinstance(query_filter, Filter)
        assert 'AuthService' in query_filter.must[0].match.any
        assert 'service' in query_filter.must[1].match.any

        # 2. Verify SentenceTransformer was used
        mock_sentence_transformer.encode.assert_called_once()

        # 3. Verify the output
        captured = capsys.readouterr()
        output = captured.out
        
        assert "[Feniks] Query (en)  : \"find auth service\"" in output
        assert "app/src/cart/CartService.js" in output # This one has 'AuthService' as a dependency
        assert "app/src/auth/AuthService.js" not in output # Should be filtered out by mock
        
        # This one should be filtered out by the client-side module check or deps filter
        assert "app/src/index/HomeCtrl.js" not in output
