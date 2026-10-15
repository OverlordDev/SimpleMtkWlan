import struct,sys,re,subprocess
KC="/System/Library/KernelCollections/BootKernelExtensions.kc"
data=open(KC,"rb").read()
ncmds=struct.unpack_from("<I",data,16)[0]; off=32; segs=[]
for _ in range(ncmds):
    cmd,size=struct.unpack_from("<II",data,off)
    if cmd==0x19:
        vm,vs,fo,fs=struct.unpack_from("<QQQQ",data,off+24); segs.append((vm,vs,fo,fs))
    off+=size
base=min(s[0] for s in segs)
def rd(a,n=8):
    for vm,vs,fo,fs in segs:
        if vm<=a<vm+fs: return data[fo+a-vm:fo+a-vm+n]
sym={}
for l in open(sys.argv[1]):
    p=l.split()
    if len(p)==3 and re.fullmatch(r"[0-9a-f]{16}",p[0]): sym.setdefault(int(p[0],16),p[2])
start=int(sys.argv[2],16); n=int(sys.argv[3])
names=[]; vals=[]
for i in range(n):
    v=struct.unpack("<Q",rd(start+8*i))[0]
    t=(v&0x3fffffff)+base if v else 0
    vals.append(t); names.append(sym.get(t,"?%x"%t if t else "NULL"))
dm=subprocess.run(["c++filt"],input="\n".join(x for x in names),capture_output=True,text=True).stdout.split("\n")
for i,(t,d) in enumerate(zip(vals,dm)): print("%3d %s"%(i+1,d))
