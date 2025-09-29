# src/feniks/qdrant.py
from __future__ import annotations

import sys
import time
from typing import List, Dict, Optional, Tuple

import numpy as np
from pydantic import ValidationError as PydanticValidationError
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, SparseVector, SparseVectorParams,
    HnswConfigDiff, OptimizersConfigDiff
)

from feniks.types import Chunk
from feniks.errors import VectorStoreError

def ensure_collection(
    client: QdrantClient,
    name: str,
    dim: int,
    reset: bool,
    use_sparse: bool
) -> None:
    """
    Twórz/odśwież kolekcję. Jeśli reset=True — usuń i twórz od nowa.
    """
    try:
        if reset:
            try:
                client.delete_collection(name)
            except Exception:
                pass
        vectors_config = {"dense_code": VectorParams(size=dim, distance=Distance.COSINE)}
        sparse_cfg = {"sparse_code": SparseVectorParams(index=bool(use_sparse))}
        client.recreate_collection(
            collection_name=name,
            vectors_config=vectors_config,
            sparse_vectors_config=sparse_cfg if use_sparse else None,
            hnsw_config=HnswConfigDiff(m=32, ef_construct=128),
            optimizers_config=OptimizersConfigDiff(
                default_segment_number=2, indexing_threshold=20000
            )
        )
    except Exception as e:
        raise VectorStoreError(f"ensure_collection failed: {e}") from e

def _batch(items: List[int], size: int) -> List[List[int]]:
    return [items[i:i+size] for i in range(0, len(items), size)]

def upsert_points(
    client: QdrantClient,
    collection: str,
    chunks: List[Chunk],
    dense: np.ndarray,
    tfidf_vocab_to_index: Optional[Dict[str, int]] = None,
    tfidf_matrix=None,
    batch_size: int = 256,
    use_sparse: bool = True,
    retries: int = 3,
    retry_backoff: float = 0.75
) -> None:
    """
    Upsert dense (+ opcjonalnie sparse) z bezpiecznym fallbackiem,
    w partiach, z delikatnym backoffem na błędy.
    """
    ids = list(range(1, len(chunks) + 1))
    for group in _batch(ids, batch_size):
        idx0, idx1 = group[0]-1, group[-1]
        vecs_dense = dense[idx0:idx1]
        payloads = []
        for i in range(idx0, idx1):
            ch = chunks[i]
            payloads.append({
                "id": ch.id,
                "file_path": ch.file_path,
                "module": ch.module,
                "chunk_name": ch.chunk_name,
                "kind": ch.kind,
                "ast_node_type": ch.ast_node_type,
                "dependencies_di": ch.dependencies_di,
                "anti_patterns": ch.anti_patterns,
                "route": ch.route,
                "symbol": ch.symbol,
                "metadata": ch.metadata or {},
            })

        attempt = 0
        while True:
            try:
                # dense + sparse w pierwszym podejściu
                points: List[PointStruct] = []
                for local_idx, k in enumerate(group):
                    vectors: Dict[str, np.ndarray] = {"dense_code": vecs_dense[local_idx]}
                    sparse_vector = None
                    if use_sparse and tfidf_matrix is not None:
                        row = tfidf_matrix[idx0 + local_idx]
                        # CSR -> indices & data
                        indices = row.indices.tolist()
                        values = row.data.astype(float).tolist()
                        sparse_vector = SparseVector(indices=indices, values=values)
                    points.append(PointStruct(id=k, vector=vectors, payload=payloads[local_idx], sparse_vectors={"sparse_code": sparse_vector} if sparse_vector else None))
                client.upsert(collection_name=collection, points=points)
                break
            except Exception as e:
                attempt += 1
                # fallback: jeśli nie wspiera sparse, albo Pydantic krzyczy
                can_fallback = isinstance(e, PydanticValidationError) or "sparse" in str(e).lower()
                if can_fallback:
                    try:
                        pts_dense = [
                            PointStruct(id=group[j], vector={"dense_code": vecs_dense[j]}, payload=payloads[j])
                            for j in range(len(group))
                        ]
                        client.upsert(collection_name=collection, points=pts_dense)
                        break
                    except Exception as e2:
                        if attempt >= retries:
                            raise VectorStoreError(f"Dense-only upsert failed after fallback: {e2}") from e2
                        time.sleep(retry_backoff * attempt)
                        continue
                if attempt >= retries:
                    raise VectorStoreError(f"Upsert failed after {retries} attempts: {e}") from e
                time.sleep(retry_backoff * attempt)

