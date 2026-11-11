#!/usr/bin/env python3
"""GPT가 준 주차장 이름·주소를 카카오로 확인. 결과: scripts/parking_verify.json"""
import json, math, os, sys, time, urllib.parse, urllib.request
KEY = os.environ.get('KAKAO_REST_KEY', '').strip()
def call(path, **p):
    url = 'https://dapi.kakao.com/v2/local/search/%s.json?%s' % (path, urllib.parse.urlencode(p))
    req = urllib.request.Request(url, headers={'Authorization': 'KakaoAK ' + KEY})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r: return json.load(r).get('documents', [])
        except urllib.error.HTTPError as e:
            if e.code in (401, 403): sys.exit('카카오 인증 실패(%s)' % e.code)
            if e.code == 429: time.sleep(2 + k * 3); continue
            return []
        except Exception: time.sleep(1 + k)
    return []
def km(a, b, c, d): return math.hypot((a - c) * 111.0, (b - d) * 111.0 * math.cos(math.radians(a)))
res = []
for s in json.load(open('scripts/parking_verify_source.json')):
    lat, lng = s['lat'], s['lng']; hits = []
    reg2 = ' '.join(s['reg'].split()[:2])
    for q in ('%s %s' % (reg2, s['name']), s['name']):
        for d in call('keyword', query=q, x=lng, y=lat, radius=20000, size=10):
            hits.append(('place', d['place_name'], d.get('road_address_name') or d.get('address_name', ''), float(d['y']), float(d['x'])))
        if hits: break
    for a in s['addr'][:2]:
        for d in call('address', query=a.split('(')[0].split('일원')[0].strip(), size=1):
            hits.append(('addr', a, d.get('address_name', ''), float(d['y']), float(d['x'])))
    ok = [dict(kind=h[0], name=h[1], addr=h[2], lat=h[3], lng=h[4], km=round(km(lat, lng, h[3], h[4]), 1)) for h in hits]
    ok.sort(key=lambda x: (0 if s['name'].replace(' ', '') in x['name'].replace(' ', '') else 1, x['km']))
    res.append(dict(n=s['n'], name=s['name'], addr=s['addr'], found=ok[:3]))
    time.sleep(0.12)
json.dump(res, open('scripts/parking_verify.json', 'w'), ensure_ascii=False, indent=1)
