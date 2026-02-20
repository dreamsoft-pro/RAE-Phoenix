#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="/home/grzegorz/cloud/Dockerized/feniks"
FILE="${1:?Użycie: scripts/refactor_and_commit.sh <ścieżka-do-pliku> [komunikat]}"
MSG="${2:-refactor(factory): export function declarations ($(basename "$FILE"))}"

cd "$ROOT"

ts=$(date +%Y%m%d-%H%M%S)
backup="runs/latest/$(basename "$FILE").pre-codemod.$ts.orig"
mkdir -p runs/latest
cp "$FILE" "$backup"

restore() {
  echo "[ERROR] Przywracam oryginał: $FILE"
  cp "$backup" "$FILE"
  git restore --staged -- "$FILE" 2>/dev/null || true
}
trap restore ERR

# zastosuj codemod
node scripts/codemods/angular-factory-export.cjs --file "$FILE"

# smoke-parse JS
node - <<'NODE' "$FILE"
const fs = require('fs'); const p = require('@babel/parser');
const f = process.argv[1]; const src = fs.readFileSync(f,'utf8');
p.parse(src, { sourceType:'script', allowReturnOutsideFunction:true });
console.log('[JS] parse OK:', f);
NODE

# testy Pythona (jeśli dostępne)
if [ -x .venv/bin/pytest ] || command -v pytest >/dev/null; then
  (.venv/bin/pytest -q || pytest -q)
fi

git add "$FILE" runs/latest/* || true
git commit -m "$MSG"

echo "[DONE] committed: $MSG"
