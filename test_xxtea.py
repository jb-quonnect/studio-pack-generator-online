import os, struct, sys
sys.path.insert(0, '.')
from modules.lunii_converter import xxtea_decrypt

out = []
def p(s): out.append(str(s))

device = 'D:\\'
pi = open(os.path.join(device, '.pi'), 'rb').read()
uuids = []
for i in range(0, len(pi), 16):
    c = pi[i:i+16]
    if len(c)==16: uuids.append(c.hex())

last_hex = uuids[-1]
ref = last_hex[-8:].upper()
base = os.path.join(device, '.content', ref)
p('Last pack REF: ' + ref)
p('Dir exists: ' + str(os.path.exists(base)))

if not os.path.exists(base):
    p('Pack not found!')
    with open('diag3.txt','w') as f: f.write('\n'.join(out))
    print('Done'); exit()

# BT size check
bt_path = os.path.join(base, 'bt')
try:
    bt = open(bt_path, 'rb').read()
    p('BT: ' + str(len(bt)) + 'B hex=' + bt[:16].hex())
except Exception as e:
    p('BT error: ' + str(e))

# Compare our NI bytes 0-24 with working pack 52
ni = open(os.path.join(base, 'ni'), 'rb').read()
ni52 = open(os.path.join(device, '.content', '07C26EA8', 'ni'), 'rb').read()
p('')
p('=== NI Header comparison (first 25 bytes) ===')
p('Ours hex: ' + ni[:25].hex())
p('P52  hex: ' + ni52[:25].hex())

# Compare first node
p('')
p('=== First Node comparison (bytes 512-556) ===')
p('Ours hex: ' + ni[512:556].hex())
p('P52  hex: ' + ni52[512:556].hex())

# Check all our nodes
nc = struct.unpack_from('<i', ni, 12)[0]
p('')
p('=== All our nodes ===')
for idx in range(nc):
    o = 512 + idx*44
    p('Node' + str(idx) + ': ' + ni[o:o+44].hex())

# Check image[0] BMP header details after decryption
rf_dir = os.path.join(base, 'rf', '000')
rf_files = sorted(os.listdir(rf_dir))
if rf_files:
    im0 = open(os.path.join(rf_dir, rf_files[0]), 'rb').read()
    dec = xxtea_decrypt(im0[:min(512, len(im0))])
    rest = im0[512:]
    full = dec + rest
    # BMP header
    sig = full[:2].decode('ascii','replace')
    fsize = struct.unpack_from('<I', full, 2)[0]
    offset = struct.unpack_from('<I', full, 10)[0]
    w = struct.unpack_from('<i', full, 18)[0]
    h = struct.unpack_from('<i', full, 22)[0]
    bpp = struct.unpack_from('<H', full, 28)[0]
    comp = struct.unpack_from('<I', full, 30)[0]
    p('')
    p('=== Image[0] BMP header ===')
    p('sig=' + sig + ' fsize=' + str(fsize) + ' offset=' + str(offset))
    p('w=' + str(w) + ' h=' + str(h) + ' bpp=' + str(bpp) + ' comp=' + str(comp))
    p('file size actual: ' + str(len(im0)))

# Check working pack image for comparison
rf52 = os.path.join(device, '.content', '07C26EA8', 'rf', '000')
rf52_files = sorted(os.listdir(rf52))
if rf52_files:
    im52 = open(os.path.join(rf52, rf52_files[0]), 'rb').read()
    dec52 = xxtea_decrypt(im52[:min(512, len(im52))])
    rest52 = im52[512:]
    full52 = dec52 + rest52
    sig52 = full52[:2].decode('ascii','replace')
    fsize52 = struct.unpack_from('<I', full52, 2)[0]
    offset52 = struct.unpack_from('<I', full52, 10)[0]
    w52 = struct.unpack_from('<i', full52, 18)[0]
    h52 = struct.unpack_from('<i', full52, 22)[0]
    bpp52 = struct.unpack_from('<H', full52, 28)[0]
    comp52 = struct.unpack_from('<I', full52, 30)[0]
    p('')
    p('=== Working pack Image[0] BMP header ===')
    p('sig=' + sig52 + ' fsize=' + str(fsize52) + ' offset=' + str(offset52))
    p('w=' + str(w52) + ' h=' + str(h52) + ' bpp=' + str(bpp52) + ' comp=' + str(comp52))
    p('file size actual: ' + str(len(im52)))

# Check audio[0] MP3 frame header
sf_dir = os.path.join(base, 'sf', '000')
sf_files = sorted(os.listdir(sf_dir))
if sf_files:
    a0 = open(os.path.join(sf_dir, sf_files[0]), 'rb').read()
    dec_a = xxtea_decrypt(a0[:min(512, len(a0))])
    p('')
    p('=== Audio[0] first 16 bytes ===')
    p('Our: ' + dec_a[:16].hex())

sf52 = os.path.join(device, '.content', '07C26EA8', 'sf', '000')
sf52_files = sorted(os.listdir(sf52))
if sf52_files:
    a52 = open(os.path.join(sf52, sf52_files[0]), 'rb').read()
    dec_a52 = xxtea_decrypt(a52[:min(512, len(a52))])
    p('P52: ' + dec_a52[:16].hex())

with open('diag3.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Done')
