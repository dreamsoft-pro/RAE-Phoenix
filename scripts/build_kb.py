#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feniks – Knowledge Base Builder for AngularJS 1.x Frontend (all-in-one)
This script is the main entry point for the CLI.
The core logic is now in the `feniks` package.
"""

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

# --- 3rd party ---
from deep_translator import GoogleTranslator
from langdetect import detect as ld_detect
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny
from sentence_transformers import SentenceTransformer

# --- Feniks modules ---
from feniks.core import (
    build_module_cards_from_chunks,
    ensure_dir,
    load_chunks_from_jsonl,
    run_ast_indexer,
    write_module_cards,
)
from feniks.embed import build_tfidf, create_dense_embeddings, get_embedding_model
from feniks.qdrant import ensure_collection, upsert_points

# ----------------------------- Constants & Config -----------------------------

DEFAULT_IGNORE = [
    "**/node_modules/**", "**/bower_components/**", "**/dist/**", "**/build/**",
    "**/vendor/**", "**/.cache/**", "**/tmp/**", "**/.git/**",
    "**/*.min.js", "**/*.map", "**/*.spec.js", "**/*.test.js", "**/*.d.ts"
]

MULTILINGUAL_MODEL = "intfloat/multilingual-e5-base"

AST_TYPES_DEFAULT = [
    "CallExpression", "FunctionDeclaration", "VariableDeclarator",
    "AssignmentExpression", "MethodDefinition"
]

AUTH_DI_DEFAULT = [
    "AuthService", "UserService", "auth", "login", "session", "token",
    "JwtService", "SessionService", "AclService", "PermissionsService"
]

HTML_KEYWORDS = [
    "template", "html", "view", "form", "input", "label", "button",
    "ng-if", "ng-show", "ng-hide", "ng-model", "ng-bind", "ng-submit",
    "ng-repeat", "placeholder", "validation", "error", "message",
    "register", "login", "password", "email"
]
JS_KEYWORDS = [
    "auth", "authentication", "login", "logout", "user", "users", "password",
    "token", "jwt", "session", "permissions", "roles", "service", "provider",
    "factory", "guard", "interceptor", "credential", "oauth", "csrf"
]

@dataclass
class KBConfig:
    root: Path
    out_dir: Path
    collection: str
    qdrant_host: str = "127.0.0.1"
    qdrant_port: int = 6333
    model_name: str = MULTILINGUAL_MODEL
    reset: bool = False
    write_ignores: bool = False

# ----------------------------- CLI Command Handlers -----------------------------

def detect_lang(s: str) -> str:
    try:
        return ld_detect(s)
    except Exception:
        if re.search(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", s):
            return "pl"
        return "en"

def translate_pl_to_en(q: str) -> str:
    lang = detect_lang(q)
    if lang.startswith("en"):
        return q
    try:
        return GoogleTranslator(source="auto", target="en").translate(q)
    except Exception:
        repl = {
            "refaktoryzuj":"refactor","serwis":"service","autentykacji":"authentication",
            "autentykacja":"authentication","logowanie":"login","wylogowanie":"logout",
            "użytkownika":"user","hasło":"password","token":"token","sesja":"session",
            "uprawnienia":"permissions","rola":"role","rejestracja":"registration"
        }
        t = q.lower()
        for k,v in repl.items():
            t = re.sub(rf"\b{re.escape(k)}\b", v, t)
        return t + " auth authentication login user service refactor token session password"

def normalize_scores(values: List[float]) -> List[float]:
    if not values:
        return values
    vmin, vmax = min(values), max(values)
    if vmax <= vmin:
        return [0.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]

def keyword_overlap_score(text: str, keywords: List[str]) -> float:
    if not keywords:
        return 0.0
    t = text.lower()
    hits = sum(1 for k in keywords if k.lower() in t)
    return hits / float(len(keywords))

def cmd_index(args: argparse.Namespace) -> None:
    cfg = KBConfig(
        root=Path(args.root).resolve(),
        out_dir=Path(args.out).resolve(),
        collection=args.collection,
        qdrant_host=args.host,
        qdrant_port=args.port,
        model_name=args.model,
        reset=args.reset,
        write_ignores=args.write_ignores
    )
    t0 = time.time()
    ensure_dir(cfg.out_dir)
    if cfg.write_ignores:
        (cfg.out_dir / ".feniksignore").write_text("\n".join(DEFAULT_IGNORE) + "\n", encoding="utf-8")

    chunks_path = run_ast_indexer(cfg.root, cfg.out_dir)
    chunks = load_chunks_from_jsonl(chunks_path)
    print(f"[KB] Loaded {len(chunks)} chunks from AST indexer.")

    modules_card = build_module_cards_from_chunks(chunks)

    print("[KB] Building TF-IDF...")
    vec, X = build_tfidf(chunks)

    print(f"[KB] Loading embedder: {cfg.model_name}")
    model = get_embedding_model(cfg.model_name)
    print("[KB] Embedding (dense)...")
    D = create_dense_embeddings(model, chunks)
    dim = D.shape[1]

    client = QdrantClient(host=cfg.qdrant_host, port=cfg.qdrant_port, prefer_grpc=True)
    print(f"[KB] Ensuring collection: {cfg.collection}")
    ensure_collection(client, cfg.collection, dim, cfg.reset)

    print("[KB] Upserting to Qdrant...")
    upsert_points(client, cfg.collection, chunks, D, X, vec.vocabulary_)

    print("[KB] Writing module cards...")
    write_module_cards(cfg.out_dir, modules_card)

    dt = time.time() - t0
    print(f"[KB] DONE in {dt:0.1f}s | collection={cfg.collection} | points={len(chunks)}")
    print(f"[KB] Modules: {len(modules_card)} | cards at {cfg.out_dir/'kb/modules'}")

def cmd_search(args: argparse.Namespace) -> None:
    query_orig = args.query.strip()
    query_en = query_orig if args.no_translate else translate_pl_to_en(query_orig)

    kw = list(set(HTML_KEYWORDS + JS_KEYWORDS)) if args.mode != 'js' else JS_KEYWORDS

    client = QdrantClient(host=args.host, port=args.port, prefer_grpc=True)
    ci = client.get_collection(args.collection)
    vec_size = ci.config.params.vectors["dense_code"].size

    model = SentenceTransformer(args.model)
    if model.get_sentence_embedding_dimension() != vec_size:
        print(f"[WARN] model dim != collection dim ({model.get_sentence_embedding_dimension()} != {vec_size})", file=sys.stderr)
    q_vec = model.encode([query_en], normalize_embeddings=True)[0]

    must = []
    if args.mode == "js":
        if args.deps:
            must.append(FieldCondition(key="dependencies_di", match=MatchAny(any=args.deps)))
        if args.ast_types:
            must.append(FieldCondition(key="ast_node_type", match=MatchAny(any=args.ast_types)))
    q_filter = Filter(must=must) if must else None

    fetch_k = max(args.topk * 3, args.topk)
    res = client.search(
        collection_name=args.collection,
        query_vector=("dense_code", q_vec),
        query_filter=q_filter,
        limit=fetch_k,
        with_payload=True,
        with_vectors=False
    )
    if not res:
        print("Brak wyników."); return

    def module_ok(fp: str) -> bool:
        if args.modules in ("all", "*"): return True
        m = re.search(r"(?:^|/)app/src/([^/]+)/", fp.replace("\\", "/"))
        return (m.group(1) if m else "-") in [x.strip() for x in args.modules.split(",") if x.strip()]

    filtered = [r for r in res if module_ok(str(r.payload.get("file_path", ""))) and (not args.paths_include or any(sub in str(r.payload.get("file_path", "")) for sub in args.paths_include))]
    if not filtered:
        print("Brak wyników po filtrach client-side."); return

    dense_norm = normalize_scores([r.score for r in filtered])
    reranked = []
    for r, dn in zip(filtered, dense_norm):
        p = r.payload or {}
        fp = str(p.get("file_path", ""))
        ast = str(p.get("ast_node_type", ""))
        deps = p.get("dependencies_di", [])
        kind = p.get("kind", "")

        ext_bonus = 0.06 if args.mode == "js" and fp.endswith(".js") else 0.08 if args.mode == "html" and fp.endswith(".html") else 0.0
        path_bonus = 0.04 if args.mode == "html" and re.search(r"(templates|views|partials)/", fp.replace("\\", "/")) else 0.0
        kw_score = keyword_overlap_score(f"{fp} {ast} {' '.join(deps)} {kind}", kw)

        final = args.alpha * dn + (1.0 - args.alpha) * kw_score + ext_bonus + path_bonus
        modm = re.search(r"(?:^|/)app/src/([^/]+)/", fp.replace("\\", "/"))
        reranked.append((final, r, modm.group(1) if modm else "-"))

    reranked.sort(key=lambda t: t[0], reverse=True)

    print(f'[Feniks] Query (orig): "{query_orig}"\n[Feniks] Query (en)  : "{query_en}"')
    print(f"[Feniks] Collection  : {args.collection} | vec_size={vec_size} | model={args.model}")
    print(f"[Feniks] Mode        : {args.mode}\n[Feniks] Paths inc   : {args.paths_include}\n[Feniks] Modules     : {args.modules}")
    if args.mode == "js": print(f"[Feniks] Filters     : deps={args.deps} ast={args.ast_types}")
    print("")
    for score, r, mod in reranked[:args.topk]:
        p = r.payload or {}
        print(f"[{score:0.4f}] [{mod}] {p.get('file_path','')} :: {p.get('ast_node_type','—')} :: deps={p.get('dependencies_di', [])}")
        if p.get('chunk_name'): print(f"    {p.get('chunk_name')}")

# ------------------------------ CLI Parser ------------------------------

def make_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Feniks KB Builder (AngularJS 1.x)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_idx = sub.add_parser("index", help="Scan -> Chunk -> Embed -> Upsert")
    p_idx.add_argument("--root", required=True, help="Frontend root (e.g., /home/.../frontend)")
    p_idx.add_argument("--out", default=".", help="Output dir for data/kb (default: .)")
    p_idx.add_argument("--collection", default="frontend_feniks", help="Qdrant collection name")
    p_idx.add_argument("--host", default="127.0.0.1")
    p_idx.add_argument("--port", type=int, default=6333)
    p_idx.add_argument("--model", default=MULTILINGUAL_MODEL)
    p_idx.add_argument("--reset", action="store_true", help="Drop & recreate collection")
    p_idx.add_argument("--write-ignores", action="store_true", help="Emit .feniksignore with sane defaults")

    p_s = sub.add_parser("search", help="Hybrid search (for quick checks / agents)")
    p_s.add_argument("query")
    p_s.add_argument("--collection", default="frontend_feniks")
    p_s.add_argument("--host", default="127.0.0.1")
    p_s.add_argument("--port", type=int, default=6333)
    p_s.add_argument("--model", default=MULTILINGUAL_MODEL)
    p_s.add_argument("--topk", type=int, default=10)
    p_s.add_argument("--alpha", type=float, default=0.7)
    p_s.add_argument("--mode", choices=["js", "html", "any"], default="js")
    p_s.add_argument("--deps", nargs="*", default=AUTH_DI_DEFAULT)
    p_s.add_argument("--paths-include", nargs="*", default=["app/src/"])
    p_s.add_argument("--ast-types", nargs="*", default=AST_TYPES_DEFAULT)
    p_s.add_argument("--modules", default="all", help="e.g., cart,client-zone,index or 'all'")
    p_s.add_argument("--no-translate", action="store_true")
    return ap

def main():
    ap = make_parser()
    args = ap.parse_args()
    if args.cmd == "index":
        cmd_index(args)
    elif args.cmd == "search":
        cmd_search(args)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()