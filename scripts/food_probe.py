#!/usr/bin/env python3
"""TourAPI 음식점(contentTypeId=39) 위치기반 시험 조회 2차 (들머리 좌표, 좌표·사진 포함). 키는 기록하지 않음."""
import json, os, urllib.parse, urllib.request, time
KEY = urllib.parse.unquote(os.environ.get('KTO_API_KEY', '').strip())
BASE = 'https://apis.data.go.kr/B551011/KorService2/locationBasedList2'
pts = {'설악산(오색공영주차장)': (38.077823, 128.452505), '치악산(황골탐방지원센터)': (37.36023, 128.022202)}
out = {}
def call(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, MobileOS='ETC', MobileApp='sanguruem', _type='json', **p))
    err = ''
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + '?' + q, headers={'Accept': 'application/json'}), timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            err = str(e).replace(KEY, '***'); time.sleep(2)
    return 'ERR ' + err
for n, (lat, lng) in pts.items():
    res = {}
    for rad in (10000, 20000):
        txt = call(mapX=lng, mapY=lat, radius=rad, contentTypeId=39, arrange='E', numOfRows=60, pageNo=1)
        try:
            b = json.loads(txt)['response']['body']; items = b.get('items', {}); items = items.get('item', []) if isinstance(items, dict) else []
            res[str(rad)] = {'total': b.get('totalCount'), 'items': [{k: it.get(k) for k in ('title', 'addr1', 'dist', 'cat3', 'tel', 'firstimage', 'firstimage2', 'mapx', 'mapy', 'contentid')} for it in items]}
        except Exception:
            res[str(rad)] = {'raw': txt[:300].replace(KEY, '***')}
    out[n] = res
json.dump(out, open('scripts/food_probe2.json', 'w'), ensure_ascii=False, indent=1)
