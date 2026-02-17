import os, struct, sys
sys.path.insert(0, '.')
from modules.lunii_converter import xxtea_decrypt

pi = open('D:\\.pi', 'rb').read()
uuids = []
for i in range(0, len(pi), 16):
    c = pi[i:i+16]
    if len(c) == 16:
        uuids.append(c.hex())
ref = uuids[-1][-8:].upper()
base = os.path.join('D:\\', '.content', ref)

ni = open(os.path.join(base, 'ni'), 'rb').read()
pv = struct.unpack_from('<h', ni, 2)[0]
nc = struct.unpack_from('<i', ni, 12)[0]
ic = struct.unpack_from('<i', ni, 16)[0]
sc = struct.unpack_from('<i', ni, 20)[0]
print('REF=%s pv=%d nodes=%d imgs=%d sounds=%d' % (ref, pv, nc, ic, sc))
for idx in range(nc):
    o = 512 + idx * 44
    vals = struct.unpack_from('<iiiiiiiihhhhhh', ni, o)
    print('  N%d: img=%d aud=%d okP=%d okC=%d okO=%d hmP=%d hmC=%d hmO=%d whl=%d ok=%d hm=%d pse=%d auto=%d' % (idx, *vals[:13]))

# LI
li = open(os.path.join(base, 'li'), 'rb').read()
dec_li = xxtea_decrypt(li[:min(512, len(li))])
print('LI entries:')
for i in range(0, len(dec_li), 4):
    print('  li[%d] = %d' % (i // 4, struct.unpack_from('<I', dec_li, i)[0]))

ri_size = os.path.getsize(os.path.join(base, 'ri'))
si_size = os.path.getsize(os.path.join(base, 'si'))
bt_size = os.path.getsize(os.path.join(base, 'bt'))
rf_count = len(os.listdir(os.path.join(base, 'rf', '000')))
sf_count = len(os.listdir(os.path.join(base, 'sf', '000')))
print('RI=%dB SI=%dB BT=%dB rf_count=%d sf_count=%d' % (ri_size, si_size, bt_size, rf_count, sf_count))
