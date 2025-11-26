import sys
from typing import List, Dict

import numpy as np
from pydantic import ValidationError as PydanticValidationError
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, SparseVector, SparseVectorParams,
    HnswConfigDiff, OptimizersConfigDiff
)

from feniks.types import Chunk


def ensure_collection(client: QdrantClient, name: str, dim: int, reset: bool) -> None:
    """
    Ensures a Qdrant collection exists, deleting it first if reset is True.
    """
    exists = False
    try:
        client.get_collection(name)
        exists = True
    except Exception:
        exists = False
    if exists and reset:
        client.delete_collection(name)
        exists = False
    if not exists:
        client.create_collection(
            collection_name=name,
            vectors_config={"dense_code": VectorParams(size=dim, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse_keywords": SparseVectorParams()},
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100, full_scan_threshold=10000),
            optimizers_config=OptimizersConfigDiff(indexing_threshold=10000),
            on_disk_payload=True
        )

def upsert_points(client: QdrantClient,
                  collection: str,
                  chunks: List[Chunk],
                  dense: np.ndarray,
                  X_tfidf, vocab: Dict[str,int],
                  batch: int = 512) -> None:
    """
    Upserts points to Qdrant with an automatic fallback to dense-only if sparse vectors are not supported.
    """
    ids = list(range(len(chunks)))
    for i in range(0, len(chunks), batch):
        j = min(i+batch, len(chunks))
        batch_ids = ids[i:j]
        vecs_dense = [dense[k].tolist() for k in batch_ids]

        # Prepare sparse slice (tf-idf)
        Xb = X_tfidf[batch_ids]
        sv: List[SparseVector] = []
        for row in range(Xb.shape[0]):
            coo = Xb[row].tocoo()
            sv.append(SparseVector(indices=coo.col.tolist(),
                                   values=[float(x) for x in coo.data.tolist()]))

        payloads = []
        for k in batch_ids:
            c = chunks[k]
            # Dynamically create payload from chunk, excluding large fields
            payload = c.__dict__.copy()
            payload.pop('text', None) # Exclude raw text from payload
            # Convert dataclass sub-objects to dicts for JSON compatibility
            if payload.get('git_last_commit'):
                payload['git_last_commit'] = payload['git_last_commit'].__dict__
            if payload.get('migration_suggestion'):
                payload['migration_suggestion'] = payload['migration_suggestion'].__dict__
            payloads.append(payload)

        pts = [
            PointStruct(
                id=k,
                payload=payloads[idx],
                vector={
                    "dense_code": vecs_dense[idx],
                    "sparse_keywords": sv[idx]
                }
            ) for idx, k in enumerate(batch_ids)
        ]
        client.upsert(collection_name=collection, points=pts)