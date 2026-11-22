#!/bin/sh
# Ostatnie okno (do 08:30): T3 tylko zbiór text, T6, krótka powtórka T1 z CPU (3 konfiguracje, 2 powtórzenia).
cd "$(dirname "$0")"
PY=../../../.venv-exp/bin/python
echo "$(date +%H:%M:%S) start t3 text" >> wyniki/run_all.log
$PY t3_http.py --only text --reps 3 --max-wait 30 > wyniki/t3_http.log 2>&1
echo "$(date +%H:%M:%S) start t6" >> wyniki/run_all.log
$PY t6_mem.py --reps 2 --max-wait 30 > wyniki/t6_mem.log 2>&1
echo "$(date +%H:%M:%S) start t1cpu" >> wyniki/run_all.log
$PY t1_ocr.py --quick --reps 2 --out T1cpu.json --max-wait 30 > wyniki/t1cpu.log 2>&1
echo "$(date +%H:%M:%S) end all" >> wyniki/run_all.log
