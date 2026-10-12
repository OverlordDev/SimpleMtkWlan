#!/usr/bin/env python3
"""gen_headers.py — генерирует C++-заголовок IO80211/IOSkywalk для Sequoia прямо из vtable ядра.
Для каждого класса объявляются ТОЛЬКО новые виртуальные слоты (индекс >= длина vtable родителя),
в точном порядке, с реальными сигнатурами из mangled-имён. Размеры классов добавляются падом."""
import re, sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
REF  = os.path.join(HERE, "..", "include", "Sequoia")

def load(path):
    out, cur = {}, None
    for l in open(path):
        if l.startswith("==="):
            cur = l.split()[1]; out[cur] = {}; continue
        m = re.match(r"\s*(\d+) 0x[0-9a-f]+ (.*)", l)
        if m and cur is not None: out[cur][int(m.group(1))] = m.group(2).strip()
    return out
vt = load(os.path.join(HERE, "vtables_IO80211_IOSkywalk_Sequoia15.8.1.txt"))
vt.update(load(os.path.join(HERE, "vtables_protocols_bcm.txt")))

# возвращаемые типы из референса (по имени метода)
ret = {}
for fn in os.listdir(REF):
    if not fn.endswith(".h"): continue
    t = re.sub(r"//.*", "", open(os.path.join(REF, fn), errors="ignore").read())
    for m in re.finditer(r"virtual\s+([\w:\s\*&<>]+?)\s*\**\s*\b(\w+)\s*\(", t):
        r = m.group(1).strip()
        if m.group(0).count("*") and "*" not in r:
            r = r + " *"
        ret.setdefault(m.group(2), r)

sdk_ret = {}
SDK = os.environ.get("MACKERNELSDK_IOKIT", os.path.join(HERE, "..", "..", "sequoia_build", "MacKernelSDK", "Headers", "IOKit"))
for rel in ("IOService.h", "IORegistryEntry.h", "network/IONetworkController.h", "network/IOEthernetController.h", "IOUserClient.h"):
    t = re.sub(r"//.*", "", re.sub(r"/\*.*?\*/", "", open(os.path.join(SDK, rel), errors="ignore").read(), flags=re.S))
    for m in re.finditer(r"virtual\s+([\w:\s\*&<>]+?)\s*\**\s*\b(\w+)\s*\(", t):
        r = m.group(1).strip()
        sdk_ret.setdefault(m.group(2), r + (" *" if m.group(0).split("(")[0].count("*") and "*" not in r else ""))

BUILTIN = {"void","bool","char","int","short","long","unsigned","signed","float","double","const","unsigned char","unsigned short","unsigned int","unsigned long","unsigned long long","long long"}

def split_sig(d):
    """'IO80211Foo::bar(a, b) const' -> (cls, name, params(list), const)"""
    const = d.endswith(" const")
    if const: d = d[:-6]
    m = re.match(r"(.*?)::(~?\w+)\((.*)\)$", d)
    if not m: return None
    cls, name, ps = m.group(1), m.group(2), m.group(3)
    params, depth, cur = [], 0, ""
    for ch in ps:
        if ch == "<": depth += 1
        if ch == ">": depth -= 1
        if ch == "," and depth == 0: params.append(cur.strip()); cur = ""
        else: cur += ch
    if cur.strip(): params.append(cur.strip())
    if params == ["void"]: params = []
    return cls, name, params, const

# (класс, родитель, размер в байтах, длина vtable родителя, ключ в vt, имя источника имён для pure)
CHAIN = [
  ("IOSkywalkInterface",         "IOService",                  0xb0,  266, "18IOSkywalkInterface"),
  ("IOSkywalkNetworkInterface",  "IOSkywalkInterface",         0xd0,  282, "25IOSkywalkNetworkInterface"),
  ("IOSkywalkEthernetInterface", "IOSkywalkNetworkInterface",  0x110, 332, "26IOSkywalkEthernetInterface"),
  ("IO80211SkywalkInterface",    "IOSkywalkEthernetInterface", 0x118, 352, "23IO80211SkywalkInterface"),
  ("IO80211InfraInterface",      "IO80211SkywalkInterface",    0x120, 460, "21IO80211InfraInterface"),
  ("IO80211InfraProtocol",       "IO80211InfraInterface",      0x120, 465, "20IO80211InfraProtocol"),
  ("IO80211Controller",          "IOEthernetController",       0x128, 394, "17IO80211Controller"),
]
used_types = set()
def conv_param(p):
    p = p.replace("__va_list_tag*", "va_list")
    # типы из demangle: 'unsigned int', 'apple80211_channel*', 'ether_addr const*', ...
    p = p.replace("unsigned long long", "UInt64").replace("unsigned long", "unsigned long").replace("unsigned int", "UInt")
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", p):
        w = m.group(0)
        if w not in BUILTIN and w not in ("UInt","UInt64","const","struct","long"): used_types.add(w)
    return p


OUTDIR = os.path.join(HERE, "gen")
os.makedirs(OUTDIR, exist_ok=True)
FINAL = {c[0]: ("17IO80211Controller" if c[0] == "IO80211Controller" else "20IO80211InfraProtocol") for c in CHAIN}
PURE_SRC = {"20IO80211InfraProtocol": "25AppleBCMWLANInfraProtocol", "17IO80211Controller": "16AppleBCMWLANCore"}
stubs = []          # (класс, возвращаемый, имя, параметры, const)
for cls, parent, size, plen, key in CHAIN:
    slots = vt[key]
    n = len(slots) - 1
    lines = []
    PARENT_KEY = {"IOSkywalkInterface": "9IOService", "IOSkywalkNetworkInterface": "18IOSkywalkInterface",
                  "IOSkywalkEthernetInterface": "25IOSkywalkNetworkInterface", "IO80211SkywalkInterface": "26IOSkywalkEthernetInterface",
                  "IO80211InfraInterface": "23IO80211SkywalkInterface", "IO80211InfraProtocol": "21IO80211InfraInterface",
                  "IO80211Controller": "20IOEthernetController"}[cls]
    pslots = vt[PARENT_KEY]
    ovr = []
    for i in range(0, plen):
        d = slots.get(i)
        if d is None or d == pslots.get(i): continue
        sg = split_sig(d)
        if sg is None: continue
        c, name, params, const = sg
        if c != cls or name.startswith("~") or name == "getMetaClass" or name.startswith("_RESERVED"): continue
        r = (sdk_ret.get(name) if cls in ("IOSkywalkInterface","IO80211Controller") else None) or ret.get(name, "IOReturn")
        ovr.append("    virtual %s %s(%s)%s APPLE_KEXT_OVERRIDE;   // override slot %d" % (r, name, ", ".join(conv_param(p) for p in params), " const" if const else "", i))
    lines.extend(ovr)
    for i in range(plen, n):
        d = slots[i]
        pure = "__cxa_pure_virtual" in d
        if pure and key in PURE_SRC:
            d = vt[PURE_SRC[key]][i]
        sg = split_sig(d)
        ok = sg is not None and (pure or sg[0] == cls)
        if pure and key in PURE_SRC:
            ok = sg is not None
        if pure and not (key in PURE_SRC):
            # реальное имя - из первого потомка, где слот реализован
            order = [c[4] for c in CHAIN]
            for k2 in order[order.index(key)+1:] + ["25AppleBCMWLANInfraProtocol", "28AppleBCMWLANSkywalkInterface"]:
                dd = vt[k2].get(i, "")
                if "__cxa_pure_virtual" not in dd and dd:
                    sg2 = split_sig(dd)
                    if sg2: d, sg, ok = dd, sg2, True
                    break
        if not ok:
            nm = "_slot%d_%s" % (i, cls)
            lines.append("    virtual IOReturn %s() = 0;   // slot %d : %s" % (nm, i, d))
            if "__cxa_pure_virtual" in vt[FINAL[cls]].get(i, ""):
                stubs.append((cls, "IOReturn", nm, [], False))
            continue
        c, name, params, const = sg
        if name.startswith("_RESERVED"):
            lines.append("    virtual void %s();" % name); continue
        r = ret.get(name, "IOReturn")
        plist = ", ".join(conv_param(p) for p in params)
        isp = pure
        lines.append("    virtual %s %s(%s)%s%s;   // slot %d" % (r, name, plist, " const" if const else "", " = 0" if isp else "", i))
        if isp and "__cxa_pure_virtual" in vt[FINAL[cls]].get(i, ""):
            stubs.append((cls, r, name, params, const))
    open(os.path.join(OUTDIR, cls + ".inc"), "w").write("// slots %d..%d из vtable Sequoia\n" % (plen, n - 1) + "\n".join(lines) + "\n")

# заглушки для всех pure-слотов всех классов цепочки (для конкретного наследника)
decl, defn = [], []
for cls, r, name, params, const in stubs:
    pl = ", ".join(conv_param(p) for p in params)
    decl.append("    virtual %s %s(%s)%s APPLE_KEXT_OVERRIDE;" % (r, name, pl, " const" if const else ""))
    args = ", ".join("%s a%d" % (conv_param(p), k) for k, p in enumerate(params))
    ret_stmt = "return kIOReturnUnsupported;" if r in ("IOReturn", "SInt32", "int", "UInt32") else ("return 0;" if r != "void" else "")
    defn.append("#ifndef MTK_HAVE_%s_%s\n%s %%s::%s(%s)%s { MTK_STUB_LOG(%s); %s }\n#endif" % (cls, name, r, name, args, " const" if const else "", name, ret_stmt))
for grp, test in (("infra", lambda c: c != "IO80211Controller"), ("controller", lambda c: c == "IO80211Controller")):
    d = [x for x, st in zip(decl, stubs) if test(st[0])]
    f = [x for x, st in zip(defn, stubs) if test(st[0])]
    open(os.path.join(OUTDIR, "pure_decl_%s.inc" % grp), "w").write("\n".join(d) + "\n")
    open(os.path.join(OUTDIR, "pure_def_%s.inc" % grp), "w").write("\n".join(f) + "\n")
# forward declarations для типов, которых нет ни в одном референсном заголовке
import glob
corpus = ""
for fn in glob.glob(os.path.join(REF, "*.h")):
    corpus += open(fn, errors="ignore").read()
fw = []
for t in sorted(used_types):
    if t in ("__ifnet","__mbuf","__va_list_tag","task","ifdrv","ether_addr","ether_header","OSObject","OSString","OSSymbol","IOService","IOMemoryDescriptor"): continue
    if not re.search(r"\b%s\b" % re.escape(t), corpus):
        fw.append("struct %s;" % t)
open(os.path.join(OUTDIR, "forward_decls.inc"), "w").write("\n".join(fw) + "\n")
sys.stderr.write("used types: %s\n" % " ".join(sorted(used_types)))
print("ok", len(stubs), "pure/placeholder slots")
