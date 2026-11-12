#!/usr/bin/env python3
"""TourAPI 음식점 분류 코드 이름(lclsSystmCode2)과 코드별 개수·예시 이름 확인. 키는 기록하지 않음."""
import json, os, urllib.parse, urllib.request, time, collections
KEY = urllib.parse.unquote(os.environ.get('KTO_API_KEY', '').strip())
B = 'https://apis.data.go.kr/B551011/KorService2/'
def call(ep, **p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, MobileOS='ETC', MobileApp='sanguruem', _type='json', **p))
    err = ''
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(B + ep + '?' + q, headers={'Accept': 'application/json'}), timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            err = str(e).replace(KEY, '***'); time.sleep(2)
    return 'ERR ' + err
def body(t):
    try: return json.loads(t)['response']['body']
    except Exception: return {'raw': t[:300].replace(KEY, '***')}
def items(b):
    it = b.get('items')
    return it.get('item', []) if isinstance(it, dict) else []
out = {}
# 분류 코드 이름 (FD = 음식)
names = {}
for lv in ('lclsSystm1', 'lclsSystm2', 'lclsSystm3'):
    pass
b1 = body(call('lclsSystmCode2', lclsSystm1='FD', numOfRows=1000, pageNo=1, lclsSystmListYn='Y'))
out['code_raw_count'] = len(items(b1)); out['code_sample'] = items(b1)[:3] if items(b1) else b1
codes = {}
for i in items(b1):
    for k in ('lclsSystm3Cd', 'lclsSystm2Cd', 'lclsSystm1Cd'):
        if i.get(k): codes[i[k]] = i.get(k.replace('Cd', 'Nm'))
out['code_names'] = codes
# 전체 식당 내려받아 코드별 개수·예시
its = []; pg = 1
while True:
    b = body(call('areaBasedList2', contentTypeId=39, numOfRows=1000, pageNo=pg)); it = items(b); its += it
    if len(it) < 1000 or pg > 30: break
    pg += 1
out['downloaded'] = len(its)
C = collections.Counter(); ex = collections.defaultdict(list)
for i in its:
    k = i.get('lclsSystm3') or '(빈값)'; C[k] += 1
    if len(ex[k]) < 4: ex[k].append(i.get('title'))
out['lcls3'] = {k: {'n': n, 'name': codes.get(k), 'ex': ex[k]} for k, n in C.most_common()}
out['lcls1'] = dict(collections.Counter(i.get('lclsSystm1') or '(빈값)' for i in its))
json.dump(out, open('scripts/food_codes.json', 'w'), ensure_ascii=False, indent=1)
