#!/bin/sh
# Po przerwaniu T1 i zmianie metody (CPU-sekundy): T2, T3, T6, potem powtórka T1 z czasem CPU (T1cpu). T4 idzie osobno (sieć).
cd "$(dirname "$0")"
PY=../../../.venv-exp/bin/python
for t in t2_pdf t3_http t6_mem t1_ocr; do
  echo "$(date +%H:%M:%S) start $t" >> wyniki/run_all.log
  case $t in t2_pdf|t6_mem|t3_http) A="--reps 2";; t1_ocr) A="--reps 3 --out T1cpu.json";; esac
  $PY $t.py --max-wait 30 $A > wyniki/$t.log 2>&1
  echo "$(date +%H:%M:%S) end $t rc=$?" >> wyniki/run_all.log
done
