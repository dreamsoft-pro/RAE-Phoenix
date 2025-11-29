# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Dict, List

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    HnswConfigDiff,
    OptimizersConfigDiff,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from feniks.core.models.types import Chunk


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
            on_disk_payload=True,
        )


def upsert_points(
    client: QdrantClient,
    collection: str,
    chunks: List[Chunk],
    dense: np.ndarray,
    tfidf_matrix,
    vocab: Dict[str, int],
    batch: int = 512,
) -> None:
    """
    Upserts points to Qdrant with an automatic fallback to dense-only if sparse vectors are not supported.
    """
    ids = list(range(len(chunks)))
    for i in range(0, len(chunks), batch):
        j = min(i + batch, len(chunks))
        batch_ids = ids[i:j]
        vecs_dense = [dense[k].tolist() for k in batch_ids]

        # Prepare sparse slice (tf-idf)
        batch_tfidf = tfidf_matrix[batch_ids]
        sv: List[SparseVector] = []
        for row in range(batch_tfidf.shape[0]):
            coo = batch_tfidf[row].tocoo()
            sv.append(SparseVector(indices=coo.col.tolist(), values=[float(x) for x in coo.data.tolist()]))

        payloads = []
        for k in batch_ids:
            c = chunks[k]
            # Dynamically create payload from chunk, excluding large fields
            payload = c.__dict__.copy()
            payload.pop("text", None)  # Exclude raw text from payload
            # Convert dataclass sub-objects to dicts for JSON compatibility
            if payload.get("git_last_commit"):
                payload["git_last_commit"] = payload["git_last_commit"].__dict__
            if payload.get("migration_suggestion"):
                payload["migration_suggestion"] = payload["migration_suggestion"].__dict__
            payloads.append(payload)

        pts = [
            PointStruct(id=k, payload=payloads[idx], vector={"dense_code": vecs_dense[idx], "sparse_keywords": sv[idx]})
            for idx, k in enumerate(batch_ids)
        ]
        client.upsert(collection_name=collection, points=pts)
