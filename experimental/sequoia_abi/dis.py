#!/usr/bin/env python3
"""dis.py <symbols.txt> <mangled symbol | 0xaddr> [maxbytes]  — дизассемблирует функцию из BootKernelExtensions.kc
(LC_SEGMENT_64 → vm→file, потом llvm-objdump по временному Mach-O, адреса вызовов подменяются именами из symbols.txt)"""
import struct, sys, re, subprocess, bisect, os, tempfile
KC = "/System/Library/KernelCollections/BootKernelExtensions.kc"
OBJDUMP = "/Library/Developer/CommandLineTools/usr/bin/llvm-objdump"
symfile, target = sys.argv[1], sys.argv[2]
maxb = int(sys.argv[3]) if len(sys.argv) > 3 else 0x1800
data = open(KC, "rb").read()
ncmds = struct.unpack_from("<I", data, 16)[0]
off = 32; segs = []
for _ in range(ncmds):
    cmd, size = struct.unpack_from("<II", data, off)
    if cmd == 0x19:
        vm, vs, fo, fs = struct.unpack_from("<QQQQ", data, off + 24)
        segs.append((vm, vs, fo, fs))
    off += size
sym = {}; byname = {}
for line in open(symfile):
    p = line.split()
    if len(p) == 3 and re.fullmatch(r"[0-9a-f]{16}", p[0]):
        a = int(p[0], 16); sym.setdefault(a, p[2]); byname.setdefault(p[2], a)
addrs = sorted(sym)
addr = int(target, 16) if target.startswith("0x") else byname[target]
i = bisect.bisect_right(addrs, addr)
end = addrs[i] if i < len(addrs) else addr + maxb
n = min(end - addr, maxb)
if n < 16 or os.environ.get('DIS_RANGE'): n = maxb
for vm, vs, fo, fs in segs:
    if vm <= addr < vm + fs:
        code = data[fo + addr - vm: fo + addr - vm + n]; break
else:
    sys.exit("addr not mapped")
# minimal Mach-O: header + LC_SEGMENT_64 with __text section + symtab(one symbol for function start)
sect = struct.pack("<16s16sQQIIIIIIII", b"__text", b"__TEXT", addr, len(code), 0x200 + 0, 0, 0, 0, 0x80000400, 0, 0, 0)
seg = struct.pack("<II16sQQQQiiII", 0x19, 72 + 80, b"__TEXT", addr, len(code), 0x200, len(code), 7, 5, 1, 0) + sect
hdr = struct.pack("<IiiIIIII", 0xfeedfacf, 0x01000007, 3, 1, 1, len(seg), 0, 0)
macho = hdr + seg
macho += b"\0" * (0x200 - len(macho)) + code
tf = tempfile.NamedTemporaryFile(delete=False, suffix=".o"); tf.write(macho); tf.close()
out = subprocess.run([OBJDUMP, "-d", "--no-show-raw-insn", "--macho", tf.name], capture_output=True, text=True).stdout
os.unlink(tf.name)
_names = [sym[a] for a in addrs]
_dm = subprocess.run(["c++filt"], input="\n".join(n for n in _names), capture_output=True, text=True).stdout.split("\n")
dem = dict(zip(addrs, _dm))
def sub(m):
    a = int(m.group(0), 16)
    if a in dem: return "%s <%s>" % (m.group(0), dem[a])
    return m.group(0)
print("; %s @ %#x len %d" % (target, addr, len(code)))
for l in out.split("\n"):
    if l.startswith("0x") or re.match(r"^\s+", l) or True:
        print(re.sub(r"0xffffff80[0-9a-f]{8}", sub, l))
