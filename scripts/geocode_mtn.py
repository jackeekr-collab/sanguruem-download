#!/usr/bin/env python3
"""산 좌표 후보 찾기 (카카오 로컬 API). 결과: scripts/mtn_candidates.json
- kind=find : '지역+산이름'으로 검색해 후보(이름·주소·좌표)를 모두 기록 (사람이 확인 후 확정)
- kind=check: 이미 입력된 좌표가 '지역+산이름' 검색 결과와 가까운지(거리 km) 점검"""
import json, math, os, sys, time, urllib.parse, urllib.request

KEY = os.environ.get('KAKAO_REST_KEY', '').strip()

def call(q):
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json?%s' % urllib.parse.urlencode({'query': q, 'size': 10})
    req = urllib.request.Request(url, headers={'Authorization': 'KakaoAK ' + KEY})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r).get('documents', [])
        except urllib.error.HTTPError as e:
            if e.code in (401, 403): sys.exit('카카오 인증 실패(%s)' % e.code)
            if e.code == 429: time.sleep(2 + k * 3); continue
            return []
        except Exception:
            time.sleep(1 + k)
    return []

def km(a, b, c, d): return math.hypot((a - c) * 111.0, (b - d) * 111.0 * math.cos(math.radians(a)))

def clean(n):
    import re
    return re.sub(r'\(.*?\)', '', n)

def search(s):
    base = s.get('base') or clean(s['n'])
    area = ' '.join((s.get('area') or '').replace('ㆍ', ' ').split()[:2])
    seen, out = set(), []
    for q in ['%s %s' % (area, base), base]:
        for d in call(q):
            key = d['id']
            if key in seen: continue
            seen.add(key)
            if base not in d['place_name']: continue
            out.append({'name': d['place_name'], 'cat': d.get('category_name', ''), 'addr': d.get('address_name', ''),
                        'lat': round(float(d['y']), 6), 'lng': round(float(d['x']), 6)})
        time.sleep(0.15)
    return out

def main():
    if not KEY: sys.exit('KAKAO_REST_KEY 가 설정되지 않았습니다')
    res = []
    for s in json.load(open('scripts/mtn_source.json', encoding='utf-8')):
        c = search(s)
        r = {'n': s['n'], 'area': s.get('area'), 'kind': s['kind'], 'cands': c}
        if s['kind'] == 'check':
            r['lat'], r['lng'] = s['lat'], s['lng']
            ds = [round(km(s['lat'], s['lng'], x['lat'], x['lng']), 1) for x in c]
            r['nearest_km'] = min(ds) if ds else None
        res.append(r)
    json.dump({'updated': time.strftime('%F %T'), 'items': res}, open('scripts/mtn_candidates.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('완료', len(res))

if __name__ == '__main__': main()
