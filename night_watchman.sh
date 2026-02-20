#!/bin/bash
REPORT="/home/operator/factory/RAE-Feniks/MORNING_REPORT.md"
SERVICES=("CartService.js" "AuthService.js" "CategoryService.js" "ProductService.js" "CalculationService.js" "OrderService.js")
INDEX=0

echo "# Raport Nocnej Warty - $(date)" > $REPORT
echo "Startuje automatyczna migracja co 10 minut." >> $REPORT

while true; do
    echo "## Kontrola $(date +%H:%M)" >> $REPORT
    
    # 1. Sprawdz stan Dockerow
    DOCKER_STATUS=$(docker ps | grep rae-api-dev | wc -l)
    if [ $DOCKER_STATUS -eq 1 ]; then
        echo "- ✅ RAE-Core: Dziala" >> $REPORT
    else
        echo "- ❌ RAE-Core: PADL! Probuje podniesc..." >> $REPORT
        cd ~/RAE-agentic-memory-agnostic-core && docker compose up -d rae-api-dev
    fi

    # 2. Sprawdz postep plikow
    FILES_COUNT=$(find ~/dreamsoft_factory/next-frontend/src/services -name "*.ts" | wc -l)
    echo "- 📄 Wygenerowane serwisy: $FILES_COUNT" >> $REPORT

    # 3. Dodaj nowe zadanie jesli poprzednie "powinno" byc gotowe (uproszczona logika kolejki)
    if [ $INDEX -lt ${#SERVICES[@]} ]; then
        CURRENT_SERVICE=${SERVICES[$INDEX]}
        echo "- 🚀 Wysylam do Roju: $CURRENT_SERVICE" >> $REPORT
        curl -s -X POST http://localhost:8001/v2/memories/ \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"Refactor task: $CURRENT_SERVICE\", \"metadata\": {\"project\": \"RAE-Feniks\", \"source\": \"watchman\"}, \"layer\": \"semantic\", \"tags\": [\"hive_objective\", \"pending\"]}" >> /dev/null
        
        INDEX=$((INDEX + 1))
    fi

    echo "------------------------------" >> $REPORT
    sleep 600 # 10 minut
done
