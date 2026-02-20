#!/bin/bash
API_URL="http://localhost:8001/v2/memories/"
OLLAMA_URL="http://localhost:11434/api/generate"
TARGET_DIR="/home/operator/dreamsoft_factory/next-frontend/src/services/"
while true; do
    TASK=$(curl -s "$API_URL?tag=hive_mission_v2&tag=pending&limit=1")
    ID=$(echo $TASK | jq -r .results[0].id)
    CONTENT=$(echo $TASK | jq -r .results[0].content)
    if [ "$ID" != "null" ] && [ "$ID" != "" ]; then
        echo "[HIVE V2] Modernizuje: $ID"
        # Qwen 14B Generation
        TS_CODE=$(curl -s -X POST $OLLAMA_URL -d "{\"model\": \"qwen2.5-coder:14b\", \"prompt\": \"Convert this AngularJS source to modern TypeScript class: $CONTENT\", \"stream\": false}" | jq -r .response)
        echo "$TS_CODE" > "$TARGET_DIR/hive_v2_${ID:0:8}.ts"
        # Complete
        curl -s -X PATCH "$API_URL$ID/" -H "Content-Type: application/json" -d {tags: [hive_mission_v2, completed]}
        echo "[HIVE V2] Gotowe: $ID"
    fi
    sleep 10
done
