import os, sys, struct
sys.path.insert(0, '.')
from modules.lunii_converter import xxtea_decrypt

ref = '03F2849E'
base = os.path.join('D:\\', '.content', ref)
out = []
def p(s): out.append(str(s))

ri = open(os.path.join(base, 'ri'), 'rb').read()
dec_ri = xxtea_decrypt(ri[:min(512,len(ri))])
p('RI: size=' + str(len(ri)) + ' dec=' + repr(dec_ri[:48].decode('ascii','replace')))

si = open(os.path.join(base, 'si'), 'rb').read()
dec_si = xxtea_decrypt(si[:min(512,len(si))])
p('SI: size=' + str(len(si)) + ' dec=' + repr(dec_si[:48].decode('ascii','replace')))

sf_dir = os.path.join(base, 'sf', '000')
sf_files = sorted(os.listdir(sf_dir))
p('Audio files: ' + str(len(sf_files)) + ' names: ' + str(sf_files))
for name in sf_files[:2]:
    a = open(os.path.join(sf_dir, name), 'rb').read()
    dec_a = xxtea_decrypt(a[:min(512,len(a))])
    mp3 = len(dec_a)>=2 and dec_a[0]==0xFF and (dec_a[1]&0xE0)==0xE0
    p('  ' + name + ': size=' + str(len(a)) + ' first4=' + dec_a[:4].hex() + ' mp3=' + str(mp3))

rf_dir = os.path.join(base, 'rf', '000')
rf_files = sorted(os.listdir(rf_dir))
p('Image files: ' + str(len(rf_files)) + ' names: ' + str(rf_files))
for name in rf_files[:2]:
    im = open(os.path.join(rf_dir, name), 'rb').read()
    dec_i = xxtea_decrypt(im[:min(512,len(im))])
    bmp = dec_i[:2]==b'BM'
    p('  ' + name + ': size=' + str(len(im)) + ' first4=' + dec_i[:4].hex() + ' bmp=' + str(bmp))

ni = open(os.path.join(base, 'ni'), 'rb').read()
p('NI: ver=' + str(struct.unpack_from('<H',ni,0)[0])
  + ' pv=' + str(struct.unpack_from('<h',ni,2)[0])
  + ' off=' + str(struct.unpack_from('<i',ni,4)[0])
  + ' ns=' + str(struct.unpack_from('<i',ni,8)[0])
  + ' nc=' + str(struct.unpack_from('<i',ni,12)[0])
  + ' ic=' + str(struct.unpack_from('<i',ni,16)[0])
  + ' sc=' + str(struct.unpack_from('<i',ni,20)[0])
  + ' fac=' + str(ni[24]))
# All nodes
for idx in range(struct.unpack_from('<i',ni,12)[0]):
    o = 512 + idx*44
    p('  Node' + str(idx) + ': img=' + str(struct.unpack_from('<i',ni,o)[0])
      + ' aud=' + str(struct.unpack_from('<i',ni,o+4)[0])
      + ' okP=' + str(struct.unpack_from('<i',ni,o+8)[0])
      + ' okC=' + str(struct.unpack_from('<i',ni,o+12)[0])
      + ' okO=' + str(struct.unpack_from('<i',ni,o+16)[0])
      + ' hmP=' + str(struct.unpack_from('<i',ni,o+20)[0])
      + ' hmC=' + str(struct.unpack_from('<i',ni,o+24)[0])
      + ' hmO=' + str(struct.unpack_from('<i',ni,o+28)[0])
      + ' whl=' + str(struct.unpack_from('<h',ni,o+32)[0])
      + ' ok=' + str(struct.unpack_from('<h',ni,o+34)[0])
      + ' hm=' + str(struct.unpack_from('<h',ni,o+36)[0])
      + ' pse=' + str(struct.unpack_from('<h',ni,o+38)[0])
      + ' auto=' + str(struct.unpack_from('<h',ni,o+40)[0]))

li = open(os.path.join(base, 'li'), 'rb').read()
p('LI: size=' + str(len(li)))
dec_li = xxtea_decrypt(li[:min(512,len(li))])
p('LI dec hex: ' + dec_li.hex())
for i in range(0, len(dec_li), 4):
    p('  li[' + str(i//4) + '] = ' + str(struct.unpack_from('<I', dec_li, i)[0]))

bt = open(os.path.join(base, 'bt'), 'rb').read()
p('BT: size=' + str(len(bt)) + ' hex=' + bt[:16].hex())

md = open(os.path.join(base, 'md'), 'r', encoding='utf-8', errors='replace').read()
p('MD: ' + repr(md))

# Compare with working pack 52
p('')
p('=== WORKING PACK 52 for comparison ===')
ref2 = '07C26EA8'
base2 = os.path.join('D:\\', '.content', ref2)
ni2 = open(os.path.join(base2, 'ni'), 'rb').read()
p('NI: ver=' + str(struct.unpack_from('<H',ni2,0)[0])
  + ' pv=' + str(struct.unpack_from('<h',ni2,2)[0])
  + ' off=' + str(struct.unpack_from('<i',ni2,4)[0])
  + ' ns=' + str(struct.unpack_from('<i',ni2,8)[0])
  + ' nc=' + str(struct.unpack_from('<i',ni2,12)[0])
  + ' ic=' + str(struct.unpack_from('<i',ni2,16)[0])
  + ' sc=' + str(struct.unpack_from('<i',ni2,20)[0])
  + ' fac=' + str(ni2[24]))
for idx in range(min(3, struct.unpack_from('<i',ni2,12)[0])):
    o = 512 + idx*44
    p('  Node' + str(idx) + ': img=' + str(struct.unpack_from('<i',ni2,o)[0])
      + ' aud=' + str(struct.unpack_from('<i',ni2,o+4)[0])
      + ' okP=' + str(struct.unpack_from('<i',ni2,o+8)[0])
      + ' okC=' + str(struct.unpack_from('<i',ni2,o+12)[0])
      + ' okO=' + str(struct.unpack_from('<i',ni2,o+16)[0])
      + ' hmP=' + str(struct.unpack_from('<i',ni2,o+20)[0])
      + ' hmC=' + str(struct.unpack_from('<i',ni2,o+24)[0])
      + ' hmO=' + str(struct.unpack_from('<i',ni2,o+28)[0])
      + ' whl=' + str(struct.unpack_from('<h',ni2,o+32)[0])
      + ' ok=' + str(struct.unpack_from('<h',ni2,o+34)[0])
      + ' hm=' + str(struct.unpack_from('<h',ni2,o+36)[0]))

li2 = open(os.path.join(base2, 'li'), 'rb').read()
dec_li2 = xxtea_decrypt(li2[:min(512,len(li2))])
p('LI dec hex: ' + dec_li2.hex())
for i in range(0, min(20, len(dec_li2)), 4):
    p('  li[' + str(i//4) + '] = ' + str(struct.unpack_from('<I', dec_li2, i)[0]))

bt2 = open(os.path.join(base2, 'bt'), 'rb').read()
p('BT: size=' + str(len(bt2)))

with open('verify_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Done')
