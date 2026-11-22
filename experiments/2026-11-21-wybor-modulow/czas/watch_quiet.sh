#!/bin/sh
# Dziennik ciszy: co 30 s zapisuje load avg i liczbę obcych procesów .venv-exp. Plik: wyniki/cisza-dziennik.tsv (dowód, ile trzeba było czekać).
cd "$(dirname "$0")"
while :; do
  printf '%s\t%s\t%s\n' "$(date +%H:%M:%S)" "$(cut -d' ' -f1-3 /proc/loadavg)" "$(pgrep -f '.venv-exp/bin/python' | wc -l)" >> wyniki/cisza-dziennik.tsv
  sleep 30
done
