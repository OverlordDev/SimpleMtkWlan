#!/usr/bin/env python3
"""Пост-загрузочная самопроверка AirportMtkWlan: один прогон -> PASS/FAIL по каждому пункту.
Запуск: python3 check_wifi.py   (после каждой перезагрузки)"""
import re, subprocess, time, os, glob

def sh(cmd, timeout=40):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as e:
        return ""

res = []
def check(name, ok, detail=""):
    res.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))

def info(name, detail):
    print(f"[ .. ] {name}  — {detail}")

# 1. кекст
ks = sh("kextstat 2>/dev/null | grep -i AirportMtkWlan")
m = re.search(r"\(([\d.]+)\)\s+([0-9A-F-]{36})", ks)
check("kext loaded", bool(m), m.group(2) if m else "не загружен")
boot = sh("sysctl -n kern.boottime")
bm = re.search(r"sec = (\d+)", boot); boot_sec = int(bm.group(1)) if bm else 0
info("uptime", f"{int((time.time()-boot_sec)/60)} min")

# 2. таймлайн драйвера из MtkBoot / MtkLog
def prop(name):
    out = sh("ioreg -l -w0")
    i = out.find(f'"{name}" = "')
    if i < 0: return ""
    j = out.find('"\n', i)
    return out[i:j if j > 0 else None]
boot_log = prop("MtkBoot"); ring = prop("MtkLog")
lines = [l for l in (boot_log + "\n" + ring).split("\n") if re.match(r"\[\d+\.\d+\]", l)]
def ts(l): return float(re.match(r"\[(\d+\.\d+)\]", l).group(1))
def first(pat):
    for l in lines:
        if re.search(pat, l): return ts(l)
    return None
t0 = first(r"start: before super::start")
t_ready = first(r"bringup: ready")
attempts = len({l for l in lines if "bringup: attempt" in l})
check("start() returned quickly", first(r"controller prepared|hardware attached") is not None and t0 is not None and (first(r"controller prepared|hardware attached") - t0) < 1.0,
      f"{(first(r'controller prepared|hardware attached') or 0) - (t0 or 0):.3f} s" if t0 else "нет лога")
check("bring-up ready", t_ready is not None, f"попыток: {attempts}, через {t_ready - t0:.1f} s после start" if t_ready and t0 else "нет 'bringup: ready'")
tmo_all = [l for l in lines if re.search(r"mcu cmd .* timeout|mcu tx queue stuck", l)]
tmo = [l for l in tmo_all if t_ready is None or ts(l) > t_ready]
if tmo_all and not tmo:
    info("MCU timeouts during bring-up (recovered by retry)", str(len(tmo_all)))
check("no MCU timeouts after bring-up", not tmo, f"{len(tmo)}")
fails = [l for l in lines if re.search(r"re-init failed|hal attach failed|giving up|setup failed", l)]
check("no bring-up/re-init failures", not fails, f"{len(fails)}")
setmac = [l for l in lines if "set mac" in l]
bad = [l for l in setmac if "rv=0" not in l]
info("set mac calls", f"{len(setmac)} (ошибок: {len(bad)})")
check("set mac ok", not bad)
enables = [l for l in lines if "HAL enable begin" in l]
info("HAL enable cycles", str(len(enables)))

# 3. интерфейс
ifc = sh("ifconfig en3 2>/dev/null")
check("en3 active", "status: active" in ifc, "active" if "status: active" in ifc else "inactive/нет")
ip = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", ifc)
check("has IPv4", bool(ip), ip.group(1) if ip else "")
if ip:
    p = sh("ping -c2 -t3 1.1.1.1 | tail -2")
    check("internet ping", "0.0% packet loss" in p, p.strip().split("\n")[-1] if p else "")

# 4. скан через CoreWLAN
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t")
exe = os.path.join(src, "scan")
if not os.path.exists(exe) and os.path.exists(os.path.join(src, "scan.m")):
    sh(f"clang -fobjc-arc -framework CoreWLAN -framework Foundation {src}/scan.m -o {exe}")
if os.path.exists(exe):
    o = sh(exe, 60)
    n = re.search(r"scan: (\d+) networks in ([\d.]+)s", o)
    check("CoreWLAN scan returns networks", bool(n) and int(n.group(1)) > 0, f"{n.group(1)} за {n.group(2)} s" if n else o[:80])

# 5. ошибки Family/WCL за последние 15 минут
lg = sh("/usr/bin/log show --last 15m --style compact --predicate 'process == \"kernel\" AND (eventMessage CONTAINS \"unable to set mac\" OR eventMessage CONTAINS \"Exit-setASSOCIATE\")' 2>/dev/null", 90)
unable = [l for l in lg.split("\n") if "unable to set mac" in l]
assoc_bad = [l for l in lg.split("\n") if re.search(r"Exit-setASSOCIATE:\d+ ret:-", l)]
check("no 'unable to set mac'", not unable, f"{len(unable)}")
info("setASSOCIATE failures", str(len(assoc_bad)))

# 6. паники после загрузки
newp = []
for d in ("/Library/Logs/DiagnosticReports", "/Library/Logs/DiagnosticReports/Retired"):
    for f in glob.glob(d + "/*.panic"):
        if os.path.getmtime(f) > boot_sec - 3600: newp.append(f)
check("no fresh kernel panic reports", not newp, ", ".join(os.path.basename(x) for x in newp))

bad = [n for n, ok in res if not ok]
print(f"\nИТОГ: {len(res)-len(bad)}/{len(res)} PASS" + (f"; FAIL: {', '.join(bad)}" if bad else ""))
