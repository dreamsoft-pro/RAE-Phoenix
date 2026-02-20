#!/bin/bash
echo "[NOCNA WARTA] Startuje..." >> night_shift.log
# Przetwarzaj kolejkę zadan (symulacja 4 zadan)
for i in {1..4}
do
   echo "Przetwarzam zadanie $i..." >> night_shift.log
   # Tutaj wywolujemy poprawiony dyspozytor
   # python3 scripts/dispatch_to_hive.py --mission=recipes/task_$i.json >> night_shift.log 2>&1
   sleep 5
done
echo "[NOCNA WARTA] Zakonczona." >> night_shift.log

