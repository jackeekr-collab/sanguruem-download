#!/usr/bin/env python3
"""새 산 주차장 후보 찾기 (카카오 로컬 API). 결과: scripts/parking_candidates.json
'산이름 주차장' 키워드 + 정상 좌표 반경 검색(PK6) 후보를 정상까지 직선거리와 함께 기록 (사람이 확인 후 확정)"""
import json, math, os, re, sys, time, urllib.parse, urllib.request
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
src = json.load(open('scripts/parking_source.json'))
out = []
for s in src:
    base = re.sub(r'\(.*?\)', '', s['n']); lat, lng = s['lat'], s['lng']
    seen, c = set(), []
    def add(d, how):
        if d['id'] in seen: return
        dist = km(lat, lng, float(d['y']), float(d['x']))
        if dist > 12: return
        seen.add(d['id'])
        c.append({'name': d['place_name'], 'cat': d.get('category_name', ''), 'addr': d.get('road_address_name') or d.get('address_name', ''),
                  'lat': float(d['y']), 'lng': float(d['x']), 'km': round(dist, 1), 'how': how, 'url': d.get('place_url', '')})
    for d in call('keyword', query='%s %s 주차장' % (s['reg'].split()[0] if False else ' '.join(s['reg'].split()[:2]), base), x=lng, y=lat, radius=20000, size=15): add(d, 'kw')
    for d in call('keyword', query='%s 주차장' % base, x=lng, y=lat, radius=20000, size=15): add(d, 'kw2')
    for d in call('category', category_group_code='PK6', x=lng, y=lat, radius=5000, size=15, sort='distance'): add(d, 'near')
    c = [x for x in c if '주차' in x['name'] or '주차' in x['cat']]
    c.sort(key=lambda x: (0 if base in x['name'] else 1, x['km']))
    out.append({'n': s['n'], 'reg': s['reg'], 'kind': s['kind'], 'lat': lat, 'lng': lng, 'cands': c[:8]})
    time.sleep(0.15)
json.dump(out, open('scripts/parking_candidates.json', 'w'), ensure_ascii=False, indent=1)
