#!/usr/bin/env python3
"""전국 길 정보(전국길관광정보표준데이터) 시작 지점 주소 → 좌표 변환 (카카오 로컬 API). 결과: trails.json.
이미 좌표가 있는 길은 다시 조회하지 않고, 실패한 길은 lat/lng 없이 남깁니다."""
import json, os, sys, time, urllib.parse, urllib.request

KEY = os.environ.get('KAKAO_REST_KEY', '').strip()
SRC, OUT = 'scripts/trails_source.json', 'trails.json'
LAT, LNG = (32.5, 39.0), (124.0, 132.5)
SIDO = {'서울': '서울', '부산': '부산', '대구': '대구', '인천': '인천', '광주': '광주', '대전': '대전', '울산': '울산', '세종': '세종',
        '경기': '경기', '강원': '강원', '충북': '충청북', '충남': '충청남', '전북': '전북', '전남': '전라남', '경북': '경상북', '경남': '경상남', '제주': '제주',
        '충청북': '충청북', '충청남': '충청남', '전라북': '전북', '전라남': '전라남', '경상북': '경상북', '경상남': '경상남'}

def call(path, q):
    url = 'https://dapi.kakao.com/v2/local/search/%s.json?%s' % (path, urllib.parse.urlencode({'query': q, 'size': 3}))
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

def ok(lat, lng): return LAT[0] <= lat <= LAT[1] and LNG[0] <= lng <= LNG[1]

def short(a):
    a = (a or '').strip()
    for full, sh in (('충청북', '충북'), ('충청남', '충남'), ('전라북', '전북'), ('전북특별', '전북'), ('전라남', '전남'), ('전남광주', '전남'),
                     ('경상북', '경북'), ('경상남', '경남')):
        if a.startswith(full): return sh
    return a[:2]

def same_sido(doc_addr, ad):
    a, d = short(ad), short(doc_addr)
    if not a: return True
    if a in ('전남', '광주') and d in ('전남', '광주'): return True
    return a == d

def geocode(t):
    ad = (t.get('sa') or '').strip()
    base = ad.split('(')[0].strip()
    cands = [ad, base] + ([base.rsplit(' ', 1)[0]] if base.count(' ') >= 3 else [])
    for q in dict.fromkeys(c for c in cands if c):
        for d in call('address', q):
            lat, lng = float(d['y']), float(d['x'])
            if ok(lat, lng) and same_sido(d.get('address_name'), ad): return lat, lng, 'addr'
    region = ' '.join(ad.split(' ')[:2])
    for q in ('%s %s' % (region, t.get('sn', '')), t.get('sn', '')):
        if not q.strip(): continue
        for d in call('keyword', q):
            lat, lng = float(d['y']), float(d['x'])
            if ok(lat, lng) and same_sido(d.get('address_name'), ad): return lat, lng, 'name'
    return None

def main():
    if not KEY: sys.exit('KAKAO_REST_KEY 가 설정되지 않았습니다')
    src = json.load(open(SRC, encoding='utf-8'))
    old = {}
    if os.path.exists(OUT):
        for x in json.load(open(OUT, encoding='utf-8')).get('items', []):
            if x.get('lat'): old[(x['n'], x['org'], x['sa'])] = x
    items, fail = [], []
    for t in src:
        o = old.get((t['n'], t['org'], t['sa']))
        if o:
            o = dict(t, lat=o['lat'], lng=o['lng'], geo=o.get('geo', 'addr')); items.append(o); continue
        g = geocode(t); time.sleep(0.2)
        r = dict(t)
        if g: r['lat'], r['lng'], r['geo'] = round(g[0], 6), round(g[1], 6), g[2]
        else: fail.append('%s | %s | %s' % (t['n'], t['org'], t['sa']))
        items.append(r)
    good = sum(1 for x in items if x.get('lat'))
    json.dump({'updated': time.strftime('%Y-%m-%d'), 'count': len(items), 'geocoded': good, 'items': items}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('완료: 전체 %d건, 좌표 %d건, 실패 %d건' % (len(items), good, len(fail)))
    for f in fail: print('실패:', f)

if __name__ == '__main__': main()
