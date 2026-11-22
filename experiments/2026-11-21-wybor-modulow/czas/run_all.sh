#!/bin/sh
# Kolejność (koordynator 07:15/07:xx): T1, T2, T3, T6, a T4 na końcu (limit API wraca ok. 07:40); T5 liczone z wyników.
cd "$(dirname "$0")"
PY=../../../.venv-exp/bin/python
$PY wait_for_quiet.py 60 > wyniki/wait.log 2>&1
for t in t1_ocr t2_pdf t3_http t6_mem t4_llm; do
  echo "$(date +%H:%M:%S) start $t" >> wyniki/run_all.log
  case $t in t1_ocr|t2_pdf|t6_mem) A="--reps 3";; t3_http) A="--reps 2";; *) A="";; esac
  $PY $t.py --max-wait 60 $A > wyniki/$t.log 2>&1
  echo "$(date +%H:%M:%S) end $t rc=$?" >> wyniki/run_all.log
done
$PY t5_model.py > wyniki/t5.log 2>&1; echo "$(date +%H:%M:%S) end t5 rc=$?" >> wyniki/run_all.log
