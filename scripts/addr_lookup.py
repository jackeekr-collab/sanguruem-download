#!/usr/bin/env python3
"""주소 → 좌표 (카카오 로컬 API). 입력: scripts/addr_source.json [{"id","q"}] · 결과: scripts/addr_result.json
주소 검색으로 안 나오면 키워드 검색으로 한 번 더 찾는다(후보를 모두 기록해 사람이 확인)."""
import json, os, sys, time, urllib.parse, urllib.request
KEY = os.environ.get('KAKAO_REST_KEY', '').strip()

def call(path, q):
    url = 'https://dapi.kakao.com/v2/local/search/%s.json?%s' % (path, urllib.parse.urlencode({'query': q, 'size': 5}))
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

def main():
    if not KEY: sys.exit('KAKAO_REST_KEY 가 설정되지 않았습니다')
    out = []
    for s in json.load(open('scripts/addr_source.json', encoding='utf-8')):
        c = []
        for d in call('address', s['q']):
            ad = d.get('road_address') or d.get('address') or {}
            c.append({'via': 'address', 'name': d.get('address_name', ''), 'road': (d.get('road_address') or {}).get('address_name', ''), 'lat': round(float(d['y']), 6), 'lng': round(float(d['x']), 6)})
        if not c:
            for d in call('keyword', s['q']):
                c.append({'via': 'keyword', 'name': d.get('place_name', ''), 'road': d.get('road_address_name', ''), 'addr': d.get('address_name', ''), 'lat': round(float(d['y']), 6), 'lng': round(float(d['x']), 6)})
        out.append({'id': s.get('id'), 'q': s['q'], 'cands': c})
        time.sleep(0.15)
    json.dump({'updated': time.strftime('%F %T'), 'items': out}, open('scripts/addr_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('완료', len(out))

if __name__ == '__main__': main()
