# src/feniks/core.py
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from feniks.config import Config
from feniks.errors import ParseError, ChunkError
from feniks.types import Chunk

# ---------- Utils ----------

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()

# ---------- Chunks I/O ----------

def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

def load_chunks_from_ast(ast_jsonl_path: Path) -> List[Chunk]:
    """
    Odczytaj przygotowane przez parser AST (Node) rekordy JSONL i przemapuj do Chunk.
    Zakładane pola: id|filePath|module|name|kind|nodeType|dependenciesDI|antiPatterns|text|start|end|route|symbol|metadata
    (jeśli różnią się nazwy, zrób mapowanie defensywne).
    """
    data = _read_jsonl(ast_jsonl_path)
    chunks: List[Chunk] = []
    for row in data:
        try:
            chunks.append(
                Chunk(
                    id=str(row.get("id") or sha1(f'{row.get("filePath","")}:{row.get("start",0)}:{row.get("end",0)}')),
                    file_path=row.get("filePath", ""),
                    module=row.get("module"),
                    chunk_name=row.get("name") or row.get("chunk_name") or "",
                    kind=row.get("kind") or "util",
                    ast_node_type=row.get("nodeType") or row.get("ast_node_type") or "Unknown",
                    dependencies_di=list(row.get("dependenciesDI") or row.get("dependencies_di") or []),
                    anti_patterns=list(row.get("antiPatterns") or row.get("anti_patterns") or []),
                    text=row.get("text") or "",
                    start_line=int(row.get("start") or 0),
                    end_line=int(row.get("end") or 0),
                    route=row.get("route"),
                    symbol=row.get("symbol"),
                    metadata=row.get("metadata") or {},
                )
            )
        except Exception as e:
            raise ParseError(f"Bad AST row: {e} :: {row}") from e
    return chunks

# ---------- Module Cards ----------

def build_module_registry(chunks: List[Chunk]) -> Dict[str, Dict[str, Any]]:
    """
    Zbierz moduły -> {components, services, directives, routes, filters, templates, utils}
    """
    reg: Dict[str, Dict[str, Any]] = {}
    for c in chunks:
        mod = c.module or "unknown"
        bucket = c.kind or "util"
        di_set = set(c.dependencies_di or [])
        rec = reg.setdefault(mod, {
            "components": set(),
            "services": set(),
            "directives": set(),
            "routes": set(),
            "filters": set(),
            "templates": set(),
            "utils": set(),
            "dependencies_di": set(),  # zagregowane zależności
        })
        key = (c.symbol or c.chunk_name or c.file_path)
        if bucket in rec:
            rec[bucket].add(key)
        else:
            rec["utils"].add(key)
        rec["dependencies_di"].update(di_set)
    return reg

def to_module_cards(reg: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for m, data in reg.items():
        out[m] = {k: sorted(list(v)) if isinstance(v, set) else v for k, v in data.items()}
        out[m]["module"] = m
    return out

def write_module_cards(out_dir: Path, modules_card: Dict[str, Any]) -> None:
    base = out_dir / "kb" / "modules"
    ensure_dir(base)
    for mod, data in modules_card.items():
        (base / f"{mod}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path = out_dir / "kb" / "modules_manifest.json"
    manifest = {"modules": list(modules_card.keys())}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Orkiestracja ----------

def run_node_indexer(frontend_root: Path, out_jsonl: Path) -> None:
    """
    Uruchom indeksator AST (Node). Wymaga scripts/js_html_indexer.mjs w repo.
    """
    ensure_dir(out_jsonl.parent)
    cmd = ["node", "scripts/js_html_indexer.mjs", "--root", str(frontend_root), "--out", str(out_jsonl)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise ParseError(f"Node indexer failed: {e.stderr.decode('utf-8', 'ignore')}")

def generate_kb(config: Config) -> Dict[str, Any]:
    """
    Główny entrypoint rdzenia: przygotuj chunks, karty modułów i zapisz KB.
    Zwraca krótkie podsumowanie (liczby).
    """
    out_ts = (config.out_dir / "latest").resolve()
    ensure_dir(out_ts)

    # 1) AST → chunks
    ast_jsonl = config.ast_jsonl_path or (out_ts / "chunks.mjs.jsonl")
    if not ast_jsonl.exists():
        run_node_indexer(config.frontend_root, ast_jsonl)
    chunks = load_chunks_from_ast(ast_jsonl)
    if not chunks:
        raise ChunkError("No chunks parsed from AST. Aborting.")

    # 2) Karty modułów
    reg = build_module_registry(chunks)
    cards = to_module_cards(reg)
    write_module_cards(out_ts, cards)

    # 3) Zapis surowych chunków dla kolejnych etapów (embedding/Qdrant)
    (out_ts / "chunks.json").write_text(
        json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {
        "chunks": len(chunks),
        "modules": len(cards),
        "out_dir": str(out_ts),
        "ast_jsonl": str(ast_jsonl),
    }
