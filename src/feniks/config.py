# src/feniks/config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_BOOL_TRUE = {"1", "true", "yes", "on", "y", "t"}

def _as_bool(v: Optional[str], default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in _BOOL_TRUE

def _as_int(v: Optional[str], default: int) -> int:
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default

@dataclass(frozen=True)
class Config:
    # ścieżki
    repo_root: Path
    frontend_root: Path
    out_dir: Path

    # Qdrant
    qdrant_url: str
    qdrant_api_key: Optional[str]
    qdrant_collection: str
    qdrant_dim: int
    qdrant_use_sparse: bool = True
    qdrant_batch_size: int = 256
    qdrant_concurrency: int = 4
    qdrant_timeout_s: int = 30

    # Embedding
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_batch_size: int = 64
    embed_max_chars: int = 5000  # safety for memory

    # Indexer/AST output
    ast_jsonl_path: Optional[Path] = None  # e.g. runs/<ts>/chunks.mjs.jsonl

    @staticmethod
    def from_env() -> "Config":
        cwd = Path(os.getenv("FENIKS_REPO_ROOT", os.getcwd()))
        frontend = Path(os.getenv("FENIKS_FRONTEND_ROOT", cwd / "frontend-master"))
        out_dir = Path(os.getenv("FENIKS_OUT_DIR", cwd / "runs"))

        qurl = os.getenv("QDRANT_URL", "http://localhost:6333")
        qkey = os.getenv("QDRANT_API_KEY")
        qcoll = os.getenv("QDRANT_COLLECTION", "code_chunks")
        qdim = _as_int(os.getenv("QDRANT_DIM"), 384)  # MiniLM-L6
        qsparse = _as_bool(os.getenv("QDRANT_USE_SPARSE"), True)
        qbatch = _as_int(os.getenv("QDRANT_BATCH_SIZE"), 256)
        qconc = _as_int(os.getenv("QDRANT_CONCURRENCY"), 4)
        qtimeout = _as_int(os.getenv("QDRANT_TIMEOUT_S"), 30)

        emodel = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        ebatch = _as_int(os.getenv("EMBED_BATCH_SIZE"), 64)
        emax = _as_int(os.getenv("EMBED_MAX_CHARS"), 5000)

        ast_path = os.getenv("AST_JSONL_PATH")
        return Config(
            repo_root=cwd,
            frontend_root=frontend,
            out_dir=out_dir,
            qdrant_url=qurl,
            qdrant_api_key=qkey,
            qdrant_collection=qcoll,
            qdrant_dim=qdim,
            qdrant_use_sparse=qsparse,
            qdrant_batch_size=qbatch,
            qdrant_concurrency=qconc,
            qdrant_timeout_s=qtimeout,
            embed_model=emodel,
            embed_batch_size=ebatch,
            embed_max_chars=emax,
            ast_jsonl_path=Path(ast_path) if ast_path else None,
        )
