#!/bin/bash
# Сохраняет кольцевые логи драйвера (MtkBoot/MtkLog/MtkHB) в mtklogs/ — запускать СРАЗУ при зависании Wi-Fi, до перезагрузки.
#   bash save_mtklog.sh
D="$(cd "$(dirname "$0")" && pwd)/mtklogs"; mkdir -p "$D"; T=$(date +%Y%m%d-%H%M%S)
ioreg -l -w0 > "$D/ioreg_$T.txt" 2>&1
python3 -I - "$D/ioreg_$T.txt" "$D" "$T" <<'PY'
import sys
s=open(sys.argv[1],errors='ignore').read()
for n in ("MtkBoot","MtkLog","MtkHB"):
    i=s.find('"%s" = "'%n)
    if i<0: print(n,"нет"); continue
    j=s.find('"\n',i); open("%s/%s_%s.txt"%(sys.argv[2],n,sys.argv[3]),"w").write(s[i:j].replace('\\n','\n')); print("сохранено",n)
PY
echo "готово: $D  ($T)"
