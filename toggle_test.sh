#!/bin/bash
# Матрица переподключений: выкл/вкл Wi-Fi N раз; для каждого цикла время до active+IP+ping. Лог: toggle_test.log
N=${1:-3}; OUT=/Users/illia/Desktop/desk/AirportMtkWlan_port/toggle_test.log
: > "$OUT"
echo "start $(date) N=$N" >> "$OUT"
for i in $(seq 1 $N); do
  networksetup -setairportpower en3 off; sleep 4
  t0=$(date +%s); networksetup -setairportpower en3 on
  ok=0
  for s in $(seq 1 90); do
    if ifconfig en3 | grep -q "status: active" && ifconfig en3 | grep -q "inet 192"; then
      if ping -c1 -t2 1.1.1.1 >/dev/null 2>&1; then ok=1; break; fi
    fi
    sleep 1
  done
  echo "cycle $i: $( [ $ok = 1 ] && echo OK || echo FAIL ) recover=$(( $(date +%s) - t0 ))s" >> "$OUT"
  [ $ok = 1 ] || break
  sleep 5
done
echo "done $(date)" >> "$OUT"
