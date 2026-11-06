#!/usr/bin/env python3
"""온천·찜질방 주소 → 좌표 변환 (카카오 로컬 API). 결과: spas.json (앱이 읽음).
이미 좌표가 있는 곳은 다시 조회하지 않고, 실패한 곳은 lat/lng 없이 남깁니다."""
import json, os, sys, time, urllib.parse, urllib.request

KEY = os.environ.get('KAKAO_REST_KEY', '').strip()
SRC, OUT = 'scripts/spas_source.json', 'spas.json'
LAT, LNG = (32.5, 39.0), (124.0, 132.5)   # 대한민국 범위 밖이면 오류로 본다
SIDO = {'서울': '서울', '부산': '부산', '대구': '대구', '인천': '인천', '광주': '광주', '대전': '대전', '울산': '울산', '세종': '세종',
        '경기': '경기', '강원': '강원', '충북': '충청북', '충남': '충청남', '전북': '전북', '전남': '전라남', '경북': '경상북', '경남': '경상남', '제주': '제주'}

def call(path, q):
    url = 'https://dapi.kakao.com/v2/local/search/%s.json?%s' % (path, urllib.parse.urlencode({'query': q, 'size': 3}))
    req = urllib.request.Request(url, headers={'Authorization': 'KakaoAK ' + KEY})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r).get('documents', [])
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                sys.exit('카카오 인증 실패(%s): 키 또는 카카오맵 사용 설정을 확인하세요' % e.code)
            if e.code == 429: time.sleep(2 + k * 3); continue
            return []
        except Exception:
            time.sleep(1 + k)
    return []

def ok(lat, lng): return LAT[0] <= lat <= LAT[1] and LNG[0] <= lng <= LNG[1]

def same_sido(doc_addr, ad):
    a = (ad or '')[:2]
    key = SIDO.get(a)
    d = doc_addr or ''
    return True if not key else (d[:2] == a or key in d)

def geocode(s):
    ad = (s.get('ad') or '').strip()
    base = ad.split('(')[0]
    cands = [ad, base] + ([base.rsplit(' ', 1)[0]] if base.count(' ') >= 3 else [])
    for q in dict.fromkeys(c for c in cands if c):
        for d in call('address', q):
            lat, lng = float(d['y']), float(d['x'])
            if ok(lat, lng) and same_sido(d.get('address_name'), ad): return lat, lng, 'addr'
    for d in call('keyword', '%s %s' % (s.get('cty', ''), s['n'])):
        lat, lng = float(d['y']), float(d['x'])
        if ok(lat, lng) and same_sido(d.get('address_name'), ad): return lat, lng, 'name'
    return None

def main():
    if not KEY: sys.exit('KAKAO_REST_KEY 가 설정되지 않았습니다')
    src = json.load(open(SRC, encoding='utf-8'))
    old = {}
    if os.path.exists(OUT):
        for x in json.load(open(OUT, encoding='utf-8')).get('items', []):
            if x.get('lat'): old[(x['n'], x['ad'])] = x
    items, fail = [], []
    for s in src:
        o = old.get((s['n'], s.get('ad')))
        if o: items.append(o); continue
        g = geocode(s); time.sleep(0.15)
        r = dict(s)
        if g: r['lat'], r['lng'], r['geo'] = round(g[0], 6), round(g[1], 6), g[2]
        else: fail.append('%s (%s)' % (s['n'], s.get('ad')))
        items.append(r)
    good = sum(1 for x in items if x.get('lat'))
    json.dump({'updated': time.strftime('%Y-%m-%d'), 'count': len(items), 'geocoded': good, 'items': items}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('완료: 전체 %d곳, 좌표 %d곳, 실패 %d곳' % (len(items), good, len(fail)))
    for f in fail: print('실패:', f)

if __name__ == '__main__': main()
