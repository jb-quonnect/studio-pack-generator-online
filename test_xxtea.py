import os, struct, sys
sys.path.insert(0, '.')
from modules.lunii_converter import xxtea_decrypt

pi = open(r'D:\.pi', 'rb').read()
uuids = []
for i in range(0, len(pi), 16):
    c = pi[i:i+16]
    if len(c) == 16:
        uuids.append(c.hex())
ref = uuids[-1][-8:].upper()
base = os.path.join(r'D:\\.content', ref)

out = []
ni = open(os.path.join(base, 'ni'), 'rb').read()
pv = struct.unpack_from('<h', ni, 2)[0]
nc = struct.unpack_from('<i', ni, 12)[0]
ic = struct.unpack_from('<i', ni, 16)[0]
sc = struct.unpack_from('<i', ni, 20)[0]
out.append('REF=%s pv=%d nodes=%d imgs=%d sounds=%d' % (ref, pv, nc, ic, sc))
for idx in range(nc):
    o = 512 + idx * 44
    vals = struct.unpack_from('<iiiiiiiihhhhhh', ni, o)
    out.append('  N%d: img=%d aud=%d okP=%d okC=%d okO=%d hmP=%d hmC=%d hmO=%d whl=%d ok=%d hm=%d pse=%d auto=%d' % (idx, *vals[:13]))

li = open(os.path.join(base, 'li'), 'rb').read()
dec_li = xxtea_decrypt(li[:min(512, len(li))])
out.append('LI:')
for i in range(0, len(dec_li), 4):
    out.append('  li[%d]=%d' % (i // 4, struct.unpack_from('<I', dec_li, i)[0]))

out.append('sf count=%d  rf count=%d' % (
    len(os.listdir(os.path.join(base, 'sf', '000'))),
    len(os.listdir(os.path.join(base, 'rf', '000')))))

with open('diag5.txt', 'w') as f:
    f.write('\n'.join(out))
print('Done')
