import struct, sys, subprocess, re
KC = "/System/Library/KernelCollections/BootKernelExtensions.kc"
f = open(KC, "rb"); data = f.read()
magic, cputype, cpusub, ftype, ncmds, sizeofcmds, flags, res = struct.unpack_from("<IiiIIIII", data, 0)
off = 32; segs = []
for _ in range(ncmds):
    cmd, size = struct.unpack_from("<II", data, off)
    if cmd == 0x19:
        name = data[off+8:off+24].rstrip(b"\0").decode()
        vmaddr, vmsize, fileoff, filesize = struct.unpack_from("<QQQQ", data, off+24)
        segs.append((name, vmaddr, vmsize, fileoff, filesize))
    off += size
def rd(addr, n=8):
    for name, va, vs, fo, fs in segs:
        if va <= addr < va + vs and addr - va < fs:
            return data[fo + addr - va: fo + addr - va + n]
    return None
sym = {}
for line in open(sys.argv[1]):
    p = line.split()
    if len(p) == 3 and re.fullmatch(r"[0-9a-f]{16}", p[0]):
        sym.setdefault(int(p[0], 16), p[2])
def demangle(names):
    out = subprocess.run(["c++filt"], input="\n".join(n for n in names), capture_output=True, text=True).stdout.split("\n")
    return out
for cls in sys.argv[2:]:
    base = [a for a, n in sym.items() if n == "__ZTV" + cls][0]
    # read until a qword that is 0 after position >2 or another vtable symbol
    ents = []
    a = base + 16
    nxt = min(x for x in sym if x > base)
    kcbase = min(s[1] for s in segs)
    while a < nxt:
        v = struct.unpack("<Q", rd(a))[0]
        t = (v & 0x3fffffff) + kcbase if v else 0
        ents.append(t); a += 8
    names = [sym.get(v, "?%x" % v) for v in ents]
    dm = demangle(names)
    print("=== %s base=%x entries=%d" % (cls, base, len(ents)))
    for i, (v, d) in enumerate(zip(ents, dm)):
        print("%3d %#06x %s" % (i, 16 + i*8, d))
