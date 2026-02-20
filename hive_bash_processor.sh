#!/bin/bash
API_URL="http://localhost:8001/v2/memories/"
OLLAMA_URL="http://localhost:11434/api/generate"
TARGET_DIR="/home/operator/dreamsoft_factory/next-frontend/src/services/"

while true; do
    # 1. Pobierz pierwsze zadanie pending (ale TYLKO typ objective)
    TASK=$(curl -s "$API_URL?tag=pending&limit=1")
    ID=$(echo $TASK | jq -r .results[0].id)
    CONTENT=$(echo $TASK | jq -r .results[0].content)
    
    if [ "$ID" != "null" ] && [ "$ID" != "" ]; then
        echo "[HIVE] Start: $ID"
        # 2. Popros Ollama o kod (Qwen 14B)
        TS_CODE=$(curl -s -X POST $OLLAMA_URL -d "{\"model\": \"qwen2.5-coder:14b\", \"prompt\": \"Convert this AngularJS source to modern TypeScript class. Logic only. Source: $CONTENT\", \"stream\": false}" | jq -r .response)
        
        if [ "${#TS_CODE}" -gt 100 ]; then
            FILE_NAME="hive_${ID:0:8}.ts"
            echo "$TS_CODE" > "$TARGET_DIR/$FILE_NAME"
            echo "[HIVE] Zapisano: $FILE_NAME"
            
            # 3. Oznacz jako completed (USUWAMY PENDING)
            curl -s -X PATCH "$API_URL$ID/" -H "Content-Type: application/json" -d {tags: [hive_objective, completed]}
        else
            echo "[HIVE] Ollama zwrocil za krotki kod. Pomijam."
            # Oznacz jako error, zeby nie blokowalo
            curl -s -X PATCH "$API_URL$ID/" -H "Content-Type: application/json" -d {tags: [hive_objective, error]}
        fi
    fi
    sleep 10
done
