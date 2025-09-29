#!/usr/bin/env python3
from __future__ import annotations
import json, sys, argparse, re
from pathlib import Path
from datetime import datetime, timezone

HTTP_METHODS = ["GET","POST","PUT","DELETE","PATCH","HEAD","OPTIONS"]

def guess_method(calls_functions: list[str]) -> str:
    text = " ".join(calls_functions or [])
    m = re.search(r"\.([Gg][Ee][Tt]|[Pp][Oo][Ss][Tt]|[Pp][Uu][Tt]|[Dd][Ee][Ll][Ee][Tt][Ee]|[Pp][Aa][Tt][Cc][Hh]|[Hh][Ee][Aa][Dd]|[Oo][Pp][Tt][Ii][Oo][Nn][Ss])\b", text)
    if m:
        method = m.group(1).upper()
        if method in HTTP_METHODS:
            return method
    if "$http" in text or "this.$http" in text:
        return "UNKNOWN"
    return "UNKNOWN"

def complexity_norm(x: float) -> float:
    return max(0.0, min(1.0, float(x) / 20.0))

def recency_score(iso: str | None) -> float:
    if not iso:
        return 0.5
    try:
        dt = datetime.fromisoformat(iso.replace("Z","+00:00"))
        days = (datetime.now(timezone.utc) - dt).days
        if days <= 90: return 1.0
        if days <= 365: return 0.6
        return 0.3
    except Exception:
        return 0.5

def route_exposure(urls: list[str]) -> float:
    if not urls: return 0.0
    important = ["/checkout", "/cart", "/login", "/payment", "/order", "/account"]
    hits = sum(1 for u in urls for k in important if isinstance(u, str) and k in u)
    return 0.8 if hits else 0.5

def choose_migration_target(kind: str, has_api: bool) -> tuple[str, str]:
    k = (kind or "util").lower()
    if k in ("component","controller","directive","template"):
        return ("ReactComponent", f"AngularJS {k} → React component (functional).")
    if k in ("service","factory"):
        return ("ReactHook" if has_api else "Util",
                "Service using HTTP becomes data-fetching hook; otherwise a pure util/hook.")
    if k == "route":
        return ("Route", "AngularJS route → Next.js app router segment.")
    return ("Util", "Generic utility.")

def to_ir(row: dict) -> dict:
    file = row.get("filePath")
    module = row.get("module")
    name = row.get("name") or row.get("symbol") or "anonymous"
    kind = row.get("kind") or "util"
    start = int(row.get("start", 1))
    end = int(row.get("end", start))
    meta = row.get("metadata") or {}
    calls = list(meta.get("calls_functions") or [])
    endpoints = list(meta.get("api_endpoints") or [])
    routes = list(meta.get("ui_routes") or [])
    business = list(meta.get("business_tags") or [])
    summary = meta.get("summary_en")
    glc = meta.get("git_last_commit") or row.get("git_last_commit")
    cycl = float(meta.get("cyclomatic_complexity") or row.get("cyclomatic_complexity") or 1)

    method = guess_method(calls)
    api_calls = [{
        "method": method,
        "url": url,
        "confidence": 0.95 if isinstance(url, str) and url.startswith(('/api/','http://','https://')) else 0.7,
        "evidence": {"file": file, "start": start, "end": end, "rule": "ast:$http|$resource"}
    } for url in endpoints]

    c_norm = complexity_norm(cycl)
    r_score = route_exposure(routes)
    recency = recency_score(glc.get("date") if isinstance(glc, dict) else None)
    criticality = round(0.5*c_norm + 0.3*r_score + 0.2*recency, 4)

    mg_target, mg_reason = choose_migration_target(kind, has_api=bool(endpoints))
    evidence = [{"file": file, "start": start, "end": end, "rule": "ast:chunk-lines"}]

    return {
        "id": str(row.get("id") or f"{file}:{start}-{end}:{kind}:{name}"),
        "entity": {"type": kind, "name": name},
        "location": {"file": file, "module": module, "span": {"start": start, "end": end}},
        "relations": {"calls_functions": calls, "ui_routes": routes, "api_calls": api_calls},
        "contracts": {"io_contract": None, "api_contract_ref": None},
        "scores": {"cyclomatic_complexity": cycl, "criticality_score": criticality},
        "metadata": {
            "business_tags": business, "summary_en": summary,
            "git_last_commit": glc if isinstance(glc, dict) else None,
            "evidence": evidence, "confidence": 1.0
        },
        "migration": {"target": mg_target, "rationale": mg_reason}
    }

def main():
    ap = argparse.ArgumentParser(description="Convert enriched JSONL (indexer+blame) to Feniks IR JSONL")
    ap.add_argument("--in", dest="inp", required=True, help="Input JSONL: runs/latest/chunks.enriched.jsonl")
    ap.add_argument("--out", required=True, help="Output IR JSONL path")
    args = ap.parse_args()

    inp = Path(args.inp); outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    n_in = n_out = 0
    with inp.open("r", encoding="utf-8") as f, outp.open("w", encoding="utf-8") as w:
        for line in f:
            line = line.strip()
            if not line: 
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict) and "error" in row:
                continue
            ir = to_ir(row)
            w.write(json.dumps(ir, ensure_ascii=False) + "\n")
            n_in += 1; n_out += 1
    print(f"[OK] Converted {n_in} → {n_out} rows to {outp}")

if __name__ == "__main__":
    raise SystemExit(main())
