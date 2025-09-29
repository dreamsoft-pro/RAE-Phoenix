# scripts/build_kb.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

from feniks.config import Config
from feniks.core import generate_kb
from feniks.embed import get_embedding_model, create_dense_embeddings, build_tfidf
from feniks.qdrant import ensure_collection, upsert_points
from qdrant_client import QdrantClient

def _json_out(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def cmd_dry_run(cfg: Config) -> None:
    t0 = perf_counter()
    summary = generate_kb(cfg)
    _json_out(Path(summary["out_dir"]) / "dry_run_summary.json", summary)
    print(f"[DRY-RUN] chunks={summary['chunks']} modules={summary['modules']} in {perf_counter()-t0:.2f}s")

def cmd_ingest(cfg: Config, reset: bool) -> None:
    t0 = perf_counter()
    summary = generate_kb(cfg)

    model = get_embedding_model(cfg.embed_model)
    chunks = json.loads((Path(summary["out_dir"]) / "chunks.json").read_text(encoding="utf-8"))
    from feniks.types import Chunk
    chunks_obj = [Chunk(**row) for row in chunks]
    dense = create_dense_embeddings(model, chunks_obj, max_chars=cfg.embed_max_chars, batch_size=cfg.embed_batch_size)

    tfidf_vec, tfidf_mat = build_tfidf(chunks_obj)

    client = QdrantClient(url=cfg.qdrant_url, api_key=cfg.qdrant_api_key, timeout=cfg.qdrant_timeout_s)
    ensure_collection(client, cfg.qdrant_collection, dim=dense.shape[1], reset=reset, use_sparse=cfg.qdrant_use_sparse)
    upsert_points(client, cfg.qdrant_collection, chunks_obj, dense, tfidf_vec.vocabulary_, tfidf_mat, batch_size=cfg.qdrant_batch_size, use_sparse=cfg.qdrant_use_sparse)

    _json_out(Path(summary["out_dir"]) / "ingest_summary.json", {"count": len(chunks), "collection": cfg.qdrant_collection})
    print(f"[INGEST] {len(chunks)} chunks. total {perf_counter()-t0:.2f}s")

def cmd_rebuild_schemas(cfg: Config, reset: bool) -> None:
    client = QdrantClient(url=cfg.qdrant_url, api_key=cfg.qdrant_api_key, timeout=cfg.qdrant_timeout_s)
    ensure_collection(client, cfg.qdrant_collection, dim=cfg.qdrant_dim, reset=reset, use_sparse=cfg.qdrant_use_sparse)
    print(f"[SCHEMAS] ensured '{cfg.qdrant_collection}' (dim={cfg.qdrant_dim}, sparse={cfg.qdrant_use_sparse})")

def main() -> int:
    ap = argparse.ArgumentParser(prog="feniks", description="Feniks KB builder / Qdrant ingest")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("dry-run", help="Zbuduj KB (chunks + module cards), bez Qdrant")
    s2 = sub.add_parser("ingest", help="Pełny przebieg z upsertem do Qdrant")
    s2.add_argument("--reset", action="store_true", help="Drop & recreate collection")
    s3 = sub.add_parser("rebuild-schemas", help="Tylko kolekcje Qdrant (bez ingestu)")
    s3.add_argument("--reset", action="store_true")

    args = ap.parse_args()
    cfg = Config.from_env()

    if args.cmd == "dry-run":
        cmd_dry_run(cfg)
    elif args.cmd == "ingest":
        cmd_ingest(cfg, reset=args.reset)
    elif args.cmd == "rebuild-schemas":
        cmd_rebuild_schemas(cfg, reset=args.reset)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
