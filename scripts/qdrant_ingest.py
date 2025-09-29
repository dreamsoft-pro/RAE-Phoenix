# scripts/qdrant_ingest.py
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qdrant_client import QdrantClient

from feniks.config import Config
from feniks.embed import get_embedding_model, create_dense_embeddings, build_tfidf
from feniks.qdrant import ensure_collection, upsert_points
from feniks.types import Chunk

def _load_chunks(path: Path) -> list[Chunk]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Chunk(**row) for row in data]

def main() -> int:
    ap = argparse.ArgumentParser(description="Feniks → Qdrant ingest")
    ap.add_argument("--reset", action="store_true", help="Drop & recreate collection")
    ap.add_argument("--collection", type=str, default=None, help="Override collection name")
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--no-sparse", action="store_true", help="Disable sparse TF-IDF vectors")
    ap.add_argument("--chunks", type=str, default="runs/latest/chunks.json", help="Path to chunks.json")
    ap.add_argument("--out", type=str, default="runs/latest", help="Artifacts dir")
    args = ap.parse_args()

    cfg = Config.from_env()
    collection = args.collection or cfg.qdrant_collection
    batch_size = args.batch_size or cfg.qdrant_batch_size
    use_sparse = not args.no_sparse and cfg.qdrant_use_sparse

    chunks_path = Path(args.chunks)
    chunks = _load_chunks(chunks_path)

    # Embeddings
    model = get_embedding_model(cfg.embed_model)
    dense = create_dense_embeddings(model, chunks, max_chars=cfg.embed_max_chars, batch_size=cfg.embed_batch_size)

    tfidf_vec = None
    tfidf_mat = None
    if use_sparse:
        tfidf_vec, tfidf_mat = build_tfidf(chunks)

    # Qdrant client
    client = QdrantClient(
        url=cfg.qdrant_url,
        api_key=cfg.qdrant_api_key,
        timeout=cfg.qdrant_timeout_s,
    )
    ensure_collection(client, collection, dim=dense.shape[1], reset=args.reset, use_sparse=use_sparse)
    upsert_points(
        client, collection, chunks, dense,
        tfidf_vocab_to_index=(tfidf_vec.vocabulary_ if tfidf_vec else None),
        tfidf_matrix=tfidf_mat,
        batch_size=batch_size,
        use_sparse=use_sparse
    )

    # artifacts
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ingest_summary.json").write_text(json.dumps({
        "collection": collection,
        "count": len(chunks),
        "use_sparse": use_sparse
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Ingested {len(chunks)} chunks into '{collection}' (sparse={use_sparse})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
