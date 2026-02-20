#!/bin/bash
SOURCE_DIR="/home/operator/dreamsoft_factory/frontend/app/services"
TARGET_DIR="/home/operator/dreamsoft_factory/next-frontend/src/services"
OLLAMA_URL="http://localhost:11434/api/generate"

mkdir -p "$TARGET_DIR"

for f in "$SOURCE_DIR"/*.js; do
    NAME=$(basename "$f" .js)
    if [ ! -f "$TARGET_DIR/${NAME}.ts" ]; then
        echo "[DIRECT] Modernizuje: $NAME"
        CONTENT=$(cat "$f")
        # Generuj kod (Qwen 14B)
        curl -s -X POST "$OLLAMA_URL" -d "{\"model\": \"qwen2.5-coder:14b\", \"prompt\": \"Convert this AngularJS source to modern TypeScript class: $CONTENT\", \"stream\": false}" | jq -r .response > "$TARGET_DIR/${NAME}.ts"
        echo "[DIRECT] Gotowe: $NAME"
        sleep 5
    fi
done
