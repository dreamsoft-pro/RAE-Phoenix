import pytest
from unittest.mock import MagicMock, patch
from feniks.core.evaluation.pipeline import AnalysisPipeline
from feniks.core.models.types import Chunk, SystemModel
from feniks.exceptions import FeniksStoreError

@pytest.fixture
def pipeline():
    return AnalysisPipeline(qdrant_host="mock_host", qdrant_port=6333)

@patch("feniks.core.evaluation.pipeline.QdrantClient")
def test_load_chunks_success(mock_qdrant_cls, pipeline):
    # Setup mock client
    mock_client = MagicMock()
    mock_qdrant_cls.return_value = mock_client
    
    # Mock collection info
    mock_client.get_collection.return_value.points_count = 2
    
    # Mock scroll results
    # First call returns 2 points, second call returns empty (end of scroll)
    p1 = MagicMock(id="1", payload={"id": "1", "text": "code1", "file_path": "f1"})
    p2 = MagicMock(id="2", payload={"id": "2", "text": "code2", "file_path": "f2"})
    
    mock_client.scroll.side_effect = [
        ([p1, p2], "next_offset"), # First batch
        ([], None)                 # End
    ]
    
    chunks = pipeline._load_chunks_from_qdrant("test_collection")
    
    assert len(chunks) == 2
    assert chunks[0].id == "1"
    assert chunks[1].file_path == "f2"

@patch("feniks.core.evaluation.pipeline.QdrantClient")
def test_load_chunks_empty(mock_qdrant_cls, pipeline):
    mock_client = MagicMock()
    mock_qdrant_cls.return_value = mock_client
    mock_client.get_collection.return_value.points_count = 0
    mock_client.scroll.return_value = ([], None)
    
    chunks = pipeline._load_chunks_from_qdrant("empty_collection")
    assert len(chunks) == 0

@patch("feniks.core.evaluation.pipeline.QdrantClient")
def test_load_chunks_error(mock_qdrant_cls, pipeline):
    mock_qdrant_cls.side_effect = Exception("Connection failed")
    
    with pytest.raises(FeniksStoreError):
        pipeline._load_chunks_from_qdrant("bad_collection")

@patch("feniks.core.evaluation.pipeline.create_rae_client")
def test_sync_with_rae_success(mock_create_client, pipeline):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    model = SystemModel(project_id="p1", timestamp="now")
    reflections = [MagicMock()]
    
    result = pipeline._sync_with_rae(model, reflections)
    
    assert result is True
    mock_client.store_meta_reflection.assert_called()
    mock_client.store_system_model.assert_called()

@patch("feniks.core.evaluation.pipeline.create_rae_client")
def test_sync_with_rae_disabled(mock_create_client, pipeline):
    mock_create_client.return_value = None # RAE disabled
    
    result = pipeline._sync_with_rae(SystemModel(project_id="p1", timestamp="now"), [])
    
    assert result is False
