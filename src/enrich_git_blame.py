# scripts/enrich_git_blame.py
#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from datetime import datetime

def blame_slice(repo_root: Path, file_path: str, start: int, end: int):
  fp = repo_root / file_path
  if not fp.exists():
    return None
  try:
    cmd = ["git", "-C", str(repo_root), "blame", "--line-porcelain", f"-L{start},{end}", "--", file_path]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", "ignore")
  except subprocess.CalledProcessError:
    return None
  last_commit = None
  current = {}
  for line in out.splitlines():
    if not line.strip():
      continue
    if line[0] != '\t' and line.split()[0].isalnum() and len(line.split()[0]) >= 7 and ' ' in line:
      current = {"hash": line.split()[0]}
    elif line.startswith("author "):
      current["author"] = line[len("author "):]
    elif line.startswith("author-mail "):
      current["author_mail"] = line[len("author-mail "):]
    elif line.startswith("author-time "):
      try:
        ts = int(line[len("author-time "):])
        current["date"] = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")
      except:
        pass
    elif line.startswith("summary "):
      current["message"] = line[len("summary "):]
    elif line[0] == '\t':
      if current:
        if not last_commit:
          last_commit = current.copy()
        else:
          try:
            d1 = datetime.fromisoformat(last_commit["date"].replace("Z",""))
            d2 = datetime.fromisoformat(current.get("date","1970-01-01T00:00:00").replace("Z",""))
            if d2 > d1:
              last_commit = current.copy()
          except Exception:
            pass
  return last_commit

def main():
  import argparse
  ap = argparse.ArgumentParser(description="Enrich chunks JSONL with git blame metadata")
  ap.add_argument("--repo", required=True, help="Path to repo root")
  ap.add_argument("--in", dest="inp", required=True, help="Input JSONL (from js_html_indexer.mjs)")
  ap.add_argument("--out", required=True, help="Output JSONL")
  args = ap.parse_args()

  repo = Path(args.repo).resolve()
  inp = Path(args.inp).resolve()
  outp = Path(args.out).resolve()
  outp.parent.mkdir(parents=True, exist_ok=True)

  with inp.open("r", encoding="utf-8") as f, outp.open("w", encoding="utf-8") as w:
    for line in f:
      line = line.strip()
      if not line:
        continue
      try:
        row = json.loads(line)
      except Exception:
        continue
      fp = row.get("filePath")
      start = int(row.get("start", 1))
      end = int(row.get("end", start))
      meta = row.setdefault("metadata", {})
      info = blame_slice(repo, fp, start, end)
      if info:
        meta["git_last_commit"] = info
      w.write(json.dumps(row, ensure_ascii=False) + "\n")
  print(f"[OK] wrote {outp}")

if __name__ == "__main__":
  sys.exit(main())
