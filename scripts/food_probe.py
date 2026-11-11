#!/usr/bin/env python3
"""TourAPI 음식점(contentTypeId=39) 위치기반 시험 조회. 키는 기록하지 않음."""
import json, os, urllib.parse, urllib.request, time
KEY = urllib.parse.unquote(os.environ.get('KTO_API_KEY', '').strip())
BASE = 'https://apis.data.go.kr/B551011/KorService2/locationBasedList2'
src = {x['n']: x for x in json.load(open('scripts/trail_verify_source.json')) if x.get('lat')}
pick = ['강천산', '광교산', '갑장산', '검단산', '두타산', '무학산', '불암산', '축령산']
out = {}
def call(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, MobileOS='ETC', MobileApp='sanguruem', _type='json', **p))
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + '?' + q, headers={'Accept': 'application/json'}), timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            err = str(e).replace(KEY, '***')
            time.sleep(2)
    return 'ERR ' + err
for n in pick:
    s = src.get(n)
    if not s: out[n] = 'no coords'; continue
    res = {}
    for rad in (3000, 8000):
        txt = call(mapX=s['lng'], mapY=s['lat'], radius=rad, contentTypeId=39, arrange='E', numOfRows=15, pageNo=1)
        try:
            j = json.loads(txt); b = j['response']['body']
            items = b.get('items', {}); items = items.get('item', []) if isinstance(items, dict) else []
            res[str(rad)] = {'total': b.get('totalCount'), 'items': [{k: it.get(k) for k in ('title', 'addr1', 'dist', 'cat3', 'tel', 'firstimage', 'contentid')} for it in items]}
        except Exception:
            res[str(rad)] = {'raw': txt[:400].replace(KEY, '***')}
    out[n] = res
json.dump(out, open('scripts/food_probe.json', 'w'), ensure_ascii=False, indent=1)
