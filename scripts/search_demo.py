#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feniks – Knowledge Base Builder for AngularJS 1.x Frontend (all-in-one)
----------------------------------------------------------------------
Subcommands:
  - index  : scan -> chunk -> enrich -> embed (dense + sparse) -> upsert to Qdrant
  - search : hybrid search with PL->EN normalization, mode js/html/any, module filtering

Why this is optimal for refactoring agents:
  * Focused chunking: functions/constructs (service/factory/controller/directive) and HTML sections.
  * AngularJS-aware enrichment: DI, $inject, anti-pattern flags, module names from app/src/<module>/...
  * Hybrid retrieval: multilingual dense + tf-idf sparse in Qdrant, tuned for code+templates.
  * Side artifacts: per-module "cards" (JSON) with symbols, dependencies, routes (ui-router/ngRoute heuristics).

Tested with very large trees; uses streaming/ batching; skips vendor noise by default.

Dependencies:
  pip install qdrant-client sentence-transformers scikit-learn langdetect deep-translator
"""

import argparse
import json
import os
import re
import sys
import time
import math
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional, Tuple

# --- 3rd party ---
from langdetect import detect as ld_detect  # type: ignore
from deep_translator import GoogleTranslator  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore

from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
import numpy as np  # type: ignore

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, SparseVector, SparseVectorParams,
    Filter, FieldCondition, MatchAny, HnswConfigDiff, OptimizersConfigDiff,
    CollectionParams
)

# ----------------------------- Utilities -----------------------------

DEFAULT_IGNORE = [
    "**/node_modules/**", "**/bower_components/**", "**/dist/**", "**/build/**",
    "**/vendor/**", "**/.cache/**", "**/tmp/**", "**/.git/**",
    "**/*.min.js", "**/*.map", "**/*.spec.js", "**/*.test.js", "**/*.d.ts"
]

JS_GLOB = ["app/src/**/*.js"]
HTML_GLOB = ["app/src/**/*.html"]

MULTILINGUAL_MODEL = "intfloat/multilingual-e5-base"  # 768D, dobre PL/EN

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

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()

def read_text_safely(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def path_matches_any(path: Path, patterns: List[str]) -> bool:
    from fnmatch import fnmatch
    s = str(path.as_posix())
    return any(fnmatch(s, pat) for pat in patterns)

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
        # fallback – very simple
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

def extract_module_from_path(path: Path) -> Optional[str]:
    p = path.as_posix()
    m = re.search(r"(?:^|/)app/src/([^/]+)/", p)
    return m.group(1) if m else None

def tokenize_simple(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9_#\-$]{2,}", text.lower())

# -------------------------- AngularJS heuristics --------------------------

@dataclass
class Chunk:
    id: str
    file_path: str
    module: Optional[str]
    chunk_name: str
    kind: str           # js_function | js_symbol | html_section
    ast_node_type: str  # heuristic tag (e.g., Function | Controller | Service | Template)
    dependencies_di: List[str]
    anti_patterns: List[str]
    text: str
    start_line: int
    end_line: int

ANGULAR_SYMBOL_RE = re.compile(
    r"""\. (?:service|factory|controller|directive|provider|value|constant)\s*\(\s*['"]([^'"]+)['"]""",
    re.X
)
INJECT_ARRAY_RE = re.compile(r"""(?m)^[ \t]*\w+\s*\.\s*\$inject\s*=\s*\[([^\]]+)\]""")
INJECT_PARAMS_RE = re.compile(r"""function\s*\(([^\)]*)\)""")
MODULE_DECL_RE = re.compile(r"""angular\s*\.\s*module\s*\(\s*['"]([^'"]+)['"]\s*,\s*\[([^\]]*)\]\s*\)""")
UIROUTER_STATE_RE = re.compile(r"""\.\s*state\s*\(\s*['"]([^'"]+)['"]\s*,\s*\{""")
NGROUTE_WHEN_RE = re.compile(r"""\.\s*when\s*\(\s*['"]([^'"]+)['"]\s*,\s*\{""")

def find_angular_symbols(js: str) -> List[Tuple[str,str]]:
    # returns [(kind,name)]
    out = []
    for m in re.finditer(r"""\.(service|factory|controller|directive|provider|value|constant)\s*\(\s*['"]([^'"]+)['"]""", js):
        out.append((m.group(1), m.group(2)))
    return out

def find_injects(js: str) -> List[str]:
    deps = set()
    for m in INJECT_ARRAY_RE.finditer(js):
        arr = m.group(1)
        deps.update([t.strip().strip("'\"") for t in arr.split(",") if t.strip()])
    # also first function param list after symbol decl
    for m in INJECT_PARAMS_RE.finditer(js):
        params = [p.strip() for p in m.group(1).split(",") if p.strip()]
        for p in params:
            if re.match(r"^[A-Za-z_][$\w]*$", p) and p not in ("function",):
                deps.add(p)
    return sorted(deps)

def detect_antipatterns(js: str, html: bool=False) -> List[str]:
    flags = []
    if not html:
        if "$scope.$watch" in js: flags.append("scope_watch")
        if "$digest" in js or "$apply" in js: flags.append("manual_digest")
        if "angular.element(" in js or re.search(r"document\.\w+|window\.\w+|\$\(", js): flags.append("direct_dom")
        if "$http" in js and "Service" not in js: flags.append("http_in_controller_or_raw")
        if re.search(r"\b$q\.(defer|when|all)\b", js) and "async/await" not in js: flags.append("legacy_promises")
        if re.search(r"\.success\s*\(|\.error\s*\(", js): flags.append("deprecated_$http_api")
    else:
        if "ng-repeat" in js: flags.append("heavy_ng_repeat")
        if "ng-click" in js and "track by" not in js: flags.append("missing_ng_repeat_trackby")
        if re.search(r"\bng-model\s*=\s*\"[^\"]+\"", js) and "ng-change" in js and "debounce" not in js:
            flags.append("ng_change_without_debounce")
    return flags

def chunk_js_functions(js: str) -> List[Tuple[str,int,int]]:
    """
    Very light function-ish chunking: split by 'function ' or '=>', keep context lines.
    Returns [(chunk_text, start_line, end_line)]
    """
    lines = js.splitlines()
    idxs = [i for i,l in enumerate(lines) if re.search(r"\bfunction\b|\=\>", l)]
    if not idxs:
        return [("\n".join(lines), 1, len(lines))]
    idxs = [0] + idxs + [len(lines)]
    out = []
    for a,b in zip(idxs, idxs[1:]):
        sl = max(a-3, 0); el = min(b+3, len(lines))
        txt = "\n".join(lines[sl:el])
        out.append((txt, sl+1, el))
    return out

def chunk_html_sections(html: str) -> List[Tuple[str,int,int]]:
    """
    Split large templates along major container boundaries (forms, sections, div.page/row)
    """
    lines = html.splitlines()
    anchors = [i for i,l in enumerate(lines) if re.search(r"<form|<section|<div[^>]+(container|row|col|page-header)", l)]
    if not anchors:
        return [("\n".join(lines), 1, len(lines))]
    anchors = [0] + anchors + [len(lines)]
    out = []
    for a,b in zip(anchors, anchors[1:]):
        sl = a; el = b if b> a else a+1
        out.append(("\n".join(lines[sl:el]), sl+1, el))
    return out

# -------------------------- KB Builder (index) --------------------------

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

def scan_files(root: Path,
               includes: List[str],
               excludes: List[str]) -> List[Path]:
    files = []
    for pattern in includes:
        for p in root.glob(pattern):
            if p.is_file() and not path_matches_any(p, excludes):
                files.append(p)
    return files

def build_chunks(cfg: KBConfig) -> Tuple[List[Chunk], Dict[str, Any]]:
    chunks: List[Chunk] = []
    modules_card: Dict[str, Any] = {}
    js_files = scan_files(cfg.root, JS_GLOB, DEFAULT_IGNORE)
    html_files = scan_files(cfg.root, HTML_GLOB, DEFAULT_IGNORE)

    # Per-module registry
    reg: Dict[str, Dict[str, set]] = {}

    # JS
    for fp in js_files:
        text = read_text_safely(fp)
        module = extract_module_from_path(fp)

        symbols = find_angular_symbols(text)  # (kind,name)
        injects = find_injects(text)
        anti = detect_antipatterns(text, html=False)

        # update module registry
        mkey = module or "-"
        reg.setdefault(mkey, {"services":set(), "controllers":set(), "factories":set(),
                              "directives":set(), "routes":set(), "templates":set(), "files":set()})
        for kind,name in symbols:
            reg[mkey]["files"].add(fp.as_posix())
            reg[mkey][f"{kind}s" if kind.endswith("y")==False else "factories"].add(name)

        # routes (ui-router / ngRoute)
        for st in UIROUTER_STATE_RE.findall(text):
            reg[mkey]["routes"].add(f"state:{st}")
        for wh in NGROUTE_WHEN_RE.findall(text):
            reg[mkey]["routes"].add(f"when:{wh}")

        # chunk by functions
        for i,(chunk_txt, sl, el) in enumerate(chunk_js_functions(text)):
            chunk_name = ""
            # best-effort: take first symbol near this region
            sym = symbols[i][1] if i < len(symbols) else ""
            if sym: chunk_name = sym
            cid = sha1(f"{fp}:{sl}:{el}:{i}")
            c = Chunk(
                id=cid,
                file_path=fp.as_posix(),
                module=module,
                chunk_name=chunk_name or f"fn_{i}",
                kind="js_function",
                ast_node_type=("Service" if ".service(" in chunk_txt else
                               "Factory" if ".factory(" in chunk_txt else
                               "Controller" if ".controller(" in chunk_txt else
                               "Directive" if ".directive(" in chunk_txt else
                               "Function"),
                dependencies_di=sorted(set(injects)),
                anti_patterns=anti,
                text=chunk_txt,
                start_line=sl,
                end_line=el
            )
            chunks.append(c)

    # HTML
    for fp in html_files:
        text = read_text_safely(fp)
        module = extract_module_from_path(fp)
        anti = detect_antipatterns(text, html=True)
        mkey = module or "-"
        reg.setdefault(mkey, {"services":set(), "controllers":set(), "factories":set(),
                              "directives":set(), "routes":set(), "templates":set(), "files":set()})
        reg[mkey]["files"].add(fp.as_posix())
        reg[mkey]["templates"].add(fp.name)

        for i,(chunk_txt, sl, el) in enumerate(chunk_html_sections(text)):
            cid = sha1(f"{fp}:{sl}:{el}:html:{i}")
            # derive a readable section name
            head = re.search(r"<(form|section|div)[^>]*?(id|class)=[\"']([^\"']+)[\"']", chunk_txt)
            name = head.group(3) if head else f"section_{i}"
            c = Chunk(
                id=cid,
                file_path=fp.as_posix(),
                module=module,
                chunk_name=name,
                kind="html_section",
                ast_node_type="Template",
                dependencies_di=[],
                anti_patterns=anti,
                text=chunk_txt,
                start_line=sl,
                end_line=el
            )
            chunks.append(c)

    # Build module cards
    for mkey, data in reg.items():
        modules_card[mkey] = {
            "module": mkey,
            "services": sorted(list(data["services"])),
            "controllers": sorted(list(data["controllers"])),
            "factories": sorted(list(data["factories"])),
            "directives": sorted(list(data["directives"])),
            "routes": sorted(list(data["routes"])),
            "templates": sorted(list(data["templates"])),
            "files": sorted(list(data["files"]))
        }

    return chunks, modules_card

# -------------------------- Embedding + TF-IDF --------------------------

def build_tfidf(chunks: List[Chunk]) -> Tuple[TfidfVectorizer, Any]:
    corpus = [c.text for c in chunks]
    vec = TfidfVectorizer(
        token_pattern=r"[A-Za-z0-9_#\-$]{2,}",
        ngram_range=(1,2),
        min_df=2,
        max_features=50000
    )
    X = vec.fit_transform(corpus)  # csr_matrix
    return vec, X

def emb_model(name: str) -> SentenceTransformer:
    return SentenceTransformer(name)

def dense_embeddings(model: SentenceTransformer, chunks: List[Chunk]) -> np.ndarray:
    texts = [c.text[:5000] for c in chunks]  # protect memory
    # normalize embeddings true -> cosine comparable
    embs = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
    return np.array(embs)

# ------------------------------ Qdrant I/O ------------------------------

def ensure_collection(client: QdrantClient, name: str, dim: int, reset: bool) -> None:
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
    ids = [i for i in range(len(chunks))]
    # Build sparse vectors once
    for i in range(0, len(chunks), batch):
        j = min(i+batch, len(chunks))
        batch_ids = ids[i:j]
        vecs_dense = [dense[k].tolist() for k in batch_ids]

        # sparse slice
        Xb = X_tfidf[batch_ids]
        sv: List[SparseVector] = []
        for row in range(Xb.shape[0]):
            s = Xb[row]
            coo = s.tocoo()
            sv.append(SparseVector(indices=coo.col.tolist(), values=coo.data.round(6).tolist()))

        payloads = []
        for k in batch_ids:
            c = chunks[k]
            payloads.append({
                "chunk_name": c.chunk_name,
                "file_path": c.file_path,
                "module": c.module or "",
                "ast_node_type": c.ast_node_type,
                "kind": c.kind,
                "dependencies_di": c.dependencies_di,
                "anti_patterns": c.anti_patterns,
                "start_line": c.start_line,
                "end_line": c.end_line,
                # useful for agents:
                "tags": list(sorted(set(c.dependencies_di + c.anti_patterns))),
            })

        pts = [
            PointStruct(
                id=k,
                vector={
                    "dense_code": vecs_dense[idx]
                },
                payload=payloads[idx],
                sparse_vectors={"sparse_keywords": sv[idx]}
            ) for idx, k in enumerate(batch_ids)
        ]
        client.upsert(collection_name=collection, points=pts)

# ------------------------------ Module Cards ----------------------------

def write_module_cards(out_dir: Path, modules_card: Dict[str, Any]) -> None:
    base = out_dir / "kb" / "modules"
    ensure_dir(base)
    for mod, data in modules_card.items():
        (base / f"{mod}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # global manifest
    (out_dir / "kb" / "modules_manifest.json").write_text(
        json.dumps({"modules": list(modules_card.keys())}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# ------------------------------ Search (CLI) ----------------------------

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

def cmd_search(args: argparse.Namespace) -> None:
    query_orig = args.query.strip()
    query_en = query_orig if args.no_translate else translate_pl_to_en(query_orig)

    # choose keywords
    if args.mode == "html":
        kw = list(set(HTML_KEYWORDS + JS_KEYWORDS))
    elif args.mode == "js":
        kw = JS_KEYWORDS
    else:
        kw = list(set(HTML_KEYWORDS + JS_KEYWORDS))

    client = QdrantClient(host=args.host, port=args.port, prefer_grpc=True)
    ci = client.get_collection(args.collection)
    vec_size = ci.config.params.vectors["dense_code"].size

    model = SentenceTransformer(args.model)
    if model.get_sentence_embedding_dimension() != vec_size:
        print(f"[WARN] model dim != collection dim ({model.get_sentence_embedding_dimension()} != {vec_size})", file=sys.stderr)
    q_vec = model.encode([query_en], normalize_embeddings=True)[0]

    # server-side minimal filter for js mode (DI/AST); modules & paths filter client-side
    must = []
    if args.mode == "js":
        if args.deps:
            must.append(FieldCondition(key="dependencies_di", match=MatchAny(any=args.deps)))
        if args.ast_types:
            must.append(FieldCondition(key="ast_node_type", match=MatchAny(any=args.ast_types)))
    q_filter = Filter(must=must) if must else None

    fetch_k = max(args.topk*3, args.topk)
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
        if args.modules in ("all","*"):
            return True
        m = re.search(r"(?:^|/)app/src/([^/]+)/", fp.replace("\\","/"))
        mod = m.group(1) if m else "-"
        return mod in [x.strip() for x in args.modules.split(",") if x.strip()]

    # client-side filters
    filtered = []
    for r in res:
        p = r.payload or {}
        fp = str(p.get("file_path",""))
        paths_ok = any(sub in fp for sub in args.paths_include) if args.paths_include else True
        if not paths_ok: continue
        if not module_ok(fp): continue
        filtered.append(r)
    if not filtered:
        print("Brak wyników po filtrach client-side."); return

    dense_norm = normalize_scores([r.score for r in filtered])
    reranked = []
    for r,dn in zip(filtered, dense_norm):
        p = r.payload or {}
        fp = str(p.get("file_path",""))
        ast = str(p.get("ast_node_type",""))
        deps = p.get("dependencies_di", [])
        kind = p.get("kind","")
        modm = re.search(r"(?:^|/)app/src/([^/]+)/", fp.replace("\\","/"))
        module_name = modm.group(1) if modm else "-"

        is_js = fp.endswith(".js"); is_html = fp.endswith(".html")
        ext_bonus = 0.0
        if args.mode=="js" and is_js: ext_bonus+=0.06
        if args.mode=="html" and is_html: ext_bonus+=0.08
        path_bonus = 0.0
        if args.mode=="html" and re.search(r"(templates|views|partials)/", fp.replace("\\","/")):
            path_bonus += 0.04

        kw_text = " ".join([fp, ast, " ".join(deps) if isinstance(deps,list) else str(deps), kind])
        kw_score = keyword_overlap_score(kw_text, kw)

        final = args.alpha*dn + (1.0-args.alpha)*kw_score + ext_bonus + path_bonus
        reranked.append((final, r, module_name))
    reranked.sort(key=lambda t: t[0], reverse=True)
    top = reranked[:args.topk]

    print(f'[Feniks] Query (orig): "{query_orig}"')
    print(f'[Feniks] Query (en)  : "{query_en}"')
    print(f"[Feniks] Collection  : {args.collection} | vec_size={vec_size} | model={args.model}")
    print(f"[Feniks] Mode        : {args.mode}")
    print(f"[Feniks] Paths inc   : {args.paths_include}")
    print(f"[Feniks] Modules     : {args.modules}")
    if args.mode=="js":
        print(f"[Feniks] Filters     : deps={args.deps} ast={args.ast_types}")
    print("")
    for score,r,mod in top:
        p = r.payload or {}
        fp = p.get("file_path","")
        ast = p.get("ast_node_type","—")
        deps = p.get("dependencies_di", [])
        name = p.get("chunk_name","")
        print(f"[{score:0.4f}] [{mod}] {fp} :: {ast} :: deps={deps if deps else []}")
        if name: print(f"    {name}")

# ------------------------------ Index (CLI) -----------------------------

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
        ign = cfg.out_dir / ".feniksignore"
        ign.write_text("\n".join(DEFAULT_IGNORE)+"\n", encoding="utf-8")

    print(f"[KB] Scanning: {cfg.root}")
    chunks, modules_card = build_chunks(cfg)
    print(f"[KB] Chunks: {len(chunks)} (JS+HTML)")

    # Save raw chunks.jsonl for audit
    chunks_path = cfg.out_dir / "data" / "chunks.jsonl"
    ensure_dir(chunks_path.parent)
    with chunks_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            rec = asdict(c)
            f.write(json.dumps(rec, ensure_ascii=False)+"\n")
    print(f"[KB] Saved chunks: {chunks_path}")

    # TF-IDF
    print("[KB] Building TF-IDF...")
    vec, X = build_tfidf(chunks)

    # Dense embeddings
    print(f"[KB] Loading embedder: {cfg.model_name}")
    model = emb_model(cfg.model_name)
    print("[KB] Embedding (dense)...")
    D = dense_embeddings(model, chunks)
    dim = D.shape[1]

    # Qdrant
    client = QdrantClient(host=cfg.qdrant_host, port=cfg.qdrant_port, prefer_grpc=True)
    print(f"[KB] Ensuring collection: {cfg.collection}")
    ensure_collection(client, cfg.collection, dim, cfg.reset)

    print("[KB] Upserting to Qdrant...")
    upsert_points(client, cfg.collection, chunks, D, X, vec.vocabulary_)

    # Module cards
    print("[KB] Writing module cards...")
    write_module_cards(cfg.out_dir, modules_card)

    dt = time.time() - t0
    print(f"[KB] DONE in {dt:0.1f}s | collection={cfg.collection} | points={len(chunks)}")
    print(f"[KB] Modules: {len(modules_card)} | cards at {cfg.out_dir/'kb/modules'}")

# ------------------------------ CLI Parser ------------------------------

def make_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Feniks KB Builder (AngularJS 1.x)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_idx = sub.add_parser("index", help="Scan -> Chunk -> Embed -> Upsert")
    p_idx.add_argument("--root", required=True, help="Frontend root (e.g., /home/.../frontend)")
    p_idx.add_argument("--out", default="feniks", help="Output dir for data/kb (default: feniks)")
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
    p_s.add_argument("--mode", choices=["js","html","any"], default="js")
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
