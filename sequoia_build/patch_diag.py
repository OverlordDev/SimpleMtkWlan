#!/usr/bin/env python3
import sys

src = sys.argv[1]

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

def func_span(s, signature):
    i = s.index(signature)
    j = s.index("{", i)
    depth, k = 0, j
    while True:
        c = s[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j, k
        k += 1

# 1) mtk_ringlog(): дублируем строки в журнал ядра ещё ДО того, как создан замок кольцевого буфера
#    (иначе теряются сообщения probe/начала start) и не отбрасываем их, если буфер ещё не готов.
p = src + "/mtk80211/compat.cpp"
s = read(p)
early = "    if (!mtk_ring_lock)\n        return;\n    /* drop high-volume"
assert early in s, "compat.cpp: не нашёл начало mtk_ringlog"
s = s.replace(early, "    /* drop high-volume", 1)
tail = "    /* separate rolling buffer for the 1 Hz heartbeat and hardware dumps */"
assert tail in s, "compat.cpp: не нашёл конец форматирования в mtk_ringlog"
s = s.replace(tail,
    "    if (!mtk_has(line, \" HB \") && !mtk_has(line, \" HW \"))\n"
    "        IOLog(\"MTKDBG %s\", line);\n"
    "    if (!mtk_ring_lock)\n"
    "        return;\n\n" + tail, 1)
write(p, s)

import os
if os.path.exists(src + "/SimpleMtkWlan/SimpleMtkWlan.cpp"):
    # 2) probe()/start(): метки входа и номер строки у каждого раннего выхода
    p = src + "/SimpleMtkWlan/SimpleMtkWlan.cpp"
    s = read(p)

    def instrument(s, signature, name):
        j, k = func_span(s, signature)
        body = s[j:k + 1]
        body = body.replace("return false;", '{ IOLog("MTKDBG %s: return false at line %%d\\n", __LINE__); return false; }' % name)
        body = body.replace("return NULL;", '{ IOLog("MTKDBG %s: return NULL at line %%d\\n", __LINE__); return NULL; }' % name)
        body = body.replace("return true;", '{ IOLog("MTKDBG %s: OK\\n"); return true; }' % name)
        body = body.replace("{", '{\n    IOLog("MTKDBG %s: entered\\n");' % name, 1)
        return s[:j] + body + s[k + 1:]

    s = instrument(s, "IOService* SimpleMtkWlan::probe(IOService *provider, SInt32 *score)", "probe")
    s = instrument(s, "bool SimpleMtkWlan::start(IOService *provider)", "start")

    # 3) кольцевой лог публикуем свойством MtkLog НЕ на самом драйвере, а на PCI-узле (WL00): драйвер при
    #    неудачном start() исчезает из IORegistry вместе со своим логом, а узел WL00 остаётся.
    #    Читать: ioreg -w0 -rn WL00 -l | grep MtkLog    (sudo не нужен)
    anchor = "    mtk_ringlog_start(this);"
    assert anchor in s, "SimpleMtkWlan.cpp: не нашёл mtk_ringlog_start(this)"
    s = s.replace(anchor, "    mtk_ringlog_start(provider);", 1)
    write(p, s)


# 4) при остановке/освобождении драйвера один раз синхронно выложить свежий лог (иначе пропадают последние <0.5 с)
p = src + "/mtk80211/compat.cpp"
s = read(p)
anchor = "        mtk_ring_call = NULL;\n    }\n    mtk_ring_svc = NULL;\n}"
assert anchor in s, "compat.cpp: не нашёл конец mtk_ringlog_stop"
s = s.replace(anchor, "        mtk_ring_call = NULL;\n    }\n    if (mtk_ring_svc && mtk_ring_lock)\n        mtk_ring_publish(NULL, NULL);\n    mtk_ring_svc = NULL;\n}", 1)
write(p, s)
print("diag-патч применён")
