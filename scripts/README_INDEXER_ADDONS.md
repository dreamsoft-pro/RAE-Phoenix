# Feniks Indexer Add-ons

This folder contains drop-in tools to enrich your knowledge base:

- `scripts/js_html_indexer.mjs` — Node ESM indexer for AngularJS 1.x code:
  - extracts controllers/services/directives/factories/filters/components/config blocks
  - collects call graph hints (`calls_functions`)
  - detects API endpoints used via `$http.*(...)` and `$resource(...)`
  - maps UI routes from `$stateProvider.state(...)` / `$routeProvider.when(...)`
  - computes a simple cyclomatic complexity measure
  - emits JSONL records compatible with your `Chunk` mapper

- `scripts/enrich_git_blame.py` — enriches JSONL with `git blame` metadata for the chunk's line range.

## Install Node deps
```bash
npm i -D fast-glob @babel/parser @babel/traverse
```

## Run
```bash
# 1) Create chunks JSONL
node scripts/js_html_indexer.mjs --root ./frontend-master --out runs/latest/chunks.mjs.jsonl

# 2) Enrich with git blame
python3 scripts/enrich_git_blame.py --repo . --in runs/latest/chunks.mjs.jsonl --out runs/latest/chunks.enriched.jsonl
```

Now you can feed `runs/latest/chunks.enriched.jsonl` to your Python pipeline to build embeddings & ingest to Qdrant.
