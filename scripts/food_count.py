#!/usr/bin/env python3
"""TourAPI 음식점: 전국 개수 차이 원인 + 사진 저작권 유형 분포 확인. 키는 기록하지 않음."""
import json, os, urllib.parse, urllib.request, time, collections
KEY = urllib.parse.unquote(os.environ.get('KTO_API_KEY', '').strip())
BASE = 'https://apis.data.go.kr/B551011/KorService2/areaBasedList2'
def call(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, MobileOS='ETC', MobileApp='sanguruem', _type='json', **p))
    err = ''
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + '?' + q, headers={'Accept': 'application/json'}), timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            err = str(e).replace(KEY, '***'); time.sleep(2)
    return 'ERR ' + err
def body(t):
    try: return json.loads(t)['response']['body']
    except Exception: return {'raw': t[:200].replace(KEY, '***')}
out = {}
out['total_all'] = body(call(contentTypeId=39, numOfRows=1, pageNo=1)).get('totalCount')
# 전체를 끝까지 내려받아 분포 확인 (페이지당 1000)
items = []; pg = 1
while True:
    b = body(call(contentTypeId=39, numOfRows=1000, pageNo=pg))
    it = (b.get('items') or {}).get('item', []) if isinstance(b.get('items'), dict) else []
    items += it
    if len(it) < 1000 or pg > 30: break
    pg += 1
out['downloaded'] = len(items)
out['unique_contentid'] = len({i['contentid'] for i in items})
C = collections.Counter
out['areacode'] = dict(C(i.get('areacode') or '(빈값)' for i in items).most_common())
out['lDongRegnCd'] = dict(C(i.get('lDongRegnCd') or '(빈값)' for i in items).most_common())
out['cpyrhtDivCd'] = dict(C(i.get('cpyrhtDivCd') or '(빈값)' for i in items).most_common())
out['img_by_cpyrht'] = dict(C((i.get('cpyrhtDivCd') or '(빈값)') + (' +사진' if i.get('firstimage') else ' 사진없음') for i in items).most_common())
out['cat3_top'] = dict(C(i.get('cat3') or '(빈값)' for i in items).most_common(12))
out['lclsSystm3_top'] = dict(C(i.get('lclsSystm3') or '(빈값)' for i in items).most_common(15))
out['no_coord'] = sum(1 for i in items if not i.get('mapx') or not i.get('mapy') or float(i['mapx'] or 0) == 0)
out['modified_year'] = dict(C((i.get('modifiedtime') or '')[:4] for i in items).most_common(10))
json.dump(out, open('scripts/food_count.json', 'w'), ensure_ascii=False, indent=1)
