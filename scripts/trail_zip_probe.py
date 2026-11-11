#!/usr/bin/env python3
"""등산로정보: 산 1~3곳의 zip(shapefile)을 내려받아 속성(필드) 구조를 확인. 키는 기록하지 않음."""
import json, os, io, zipfile, urllib.parse, urllib.request, re
import xml.etree.ElementTree as ET
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
URL = 'https://apis.data.go.kr/1400000/trailInfoService/getforestspatialdataservice'
out = {}
def api(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, **p))
    with urllib.request.urlopen(URL + '?' + q, timeout=60) as r: return r.read().decode('utf-8', 'replace')
# 전체 목록(432곳) 이름 저장
names = []
for pg in range(1, 6):
    root = ET.fromstring(api(pageNo=pg, numOfRows=100))
    names += [i.findtext('mntnnm') for i in root.findall('.//item')]
out['_all_names'] = names
for nm in ['강천산', '가리산', '계룡산']:
    o = {}
    try:
        root = ET.fromstring(api(pageNo=1, numOfRows=5, mntnNm=nm))
        its = root.findall('.//item'); o['hits'] = [i.findtext('mntnnm') for i in its]
        if its:
            u = its[0].findtext('mntnfile'); o['zip'] = u
            data = urllib.request.urlopen(u, timeout=90).read(); o['zip_bytes'] = len(data)
            z = zipfile.ZipFile(io.BytesIO(data)); o['files'] = z.namelist()
            import shapefile
            o['shps'] = {}
            for n in z.namelist():
                if n.lower().endswith('.shp'):
                    base = n[:-4]
                    sf = shapefile.Reader(shp=io.BytesIO(z.read(n)), dbf=io.BytesIO(z.read(base + '.dbf')), encoding='cp949')
                    flds = [f[0] for f in sf.fields[1:]]
                    o['shps'][base.split('/')[0][:12]] = {'type': sf.shapeTypeName, 'fields': flds, 'n': len(sf),
                        'sample': [dict(zip(flds, [str(v) for v in r.record])) for r in sf.shapeRecords()[:6]]}
    except Exception as e:
        o['error'] = str(e).replace(KEY, '***')[:300]
    out[nm] = o
json.dump(out, open('scripts/trail_zip_probe.json', 'w'), ensure_ascii=False, indent=1)
