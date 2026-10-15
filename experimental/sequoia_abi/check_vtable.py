#!/usr/bin/env python3
"""check_vtable.py <clang -fdump-vtable-layouts output> <Probe class> <ключ vtable ядра>
Сравнивает слот-в-слот vtable, которую clang построил из наших заголовков, с реальной vtable Sequoia."""
import re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
def load(path):
    out, cur = {}, None
    for l in open(path):
        if l.startswith("==="): cur = l.split()[1]; out[cur] = {}; continue
        m = re.match(r"\s*(\d+) 0x[0-9a-f]+ (.*)", l)
        if m and cur is not None: out[cur][int(m.group(1))] = m.group(2).strip()
    return out
vt = load(os.path.join(HERE, "vtables_IO80211_IOSkywalk_Sequoia15.8.1.txt")); vt.update(load(os.path.join(HERE, "vtables_protocols_bcm.txt")))
dump, probe, key = sys.argv[1:4]
ours = {}; on = False
for l in open(dump, errors="ignore"):
    m = re.match(r"Vtable for '(.*)' \((\d+) entries\)", l)
    if m: on = (m.group(1) == probe); continue
    if on:
        m = re.match(r"\s+(\d+) \| (.*)", l)
        if m:
            i = int(m.group(1)) - 2
            if i >= 0 and "offset_to_top" not in m.group(2) and "RTTI" not in m.group(2): ours[i] = m.group(2)
        elif l.strip() == "": 
            if ours: break
real = dict(vt[key])
for i, d in list(real.items()):
    if "__cxa_pure_virtual" in d:
        for k2 in (("16AppleBCMWLANCore",) if "Controller" in key else ("25AppleBCMWLANInfraProtocol",)):
            if "__cxa_pure_virtual" not in vt[k2].get(i, "__cxa_pure_virtual"):
                real[i] = vt[k2][i]; break
def strip(d):
    d = re.sub(r"\[(complete|deleting)\]", "", d).strip()
    m = re.search(r"([A-Za-z_][\w:]*)::(~?\w+)\(", d)
    return (m.group(1), m.group(2)) if m else (None, d)
bad = 0; n = 0
for i in sorted(real):
    if i not in ours: continue
    n += 1
    ro, rn = strip(real[i]); oo, on_ = strip(ours[i])
    if rn.startswith("~"): continue
    # слоты, реализованные нашим Probe-классом: сверяем только имя
    if oo == probe or (oo or "").startswith("Probe"):
        if rn != on_ and not on_.startswith("_slot"):
            bad += 1; print("ИМЯ  слот %d: ядро=%s  наш=%s" % (i, real[i][:90], ours[i][:90]))
        continue
    if (ro, rn) != (oo, on_):
        bad += 1; print("СЛОТ %d: ядро=%s  наш=%s" % (i, real[i][:100], ours[i][:100]))
print("проверено слотов: %d, расхождений: %d (в ядре %d, у нас %d)" % (n, bad, len(real) - 1, len(ours)))
