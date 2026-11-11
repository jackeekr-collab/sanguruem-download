#!/usr/bin/env python3
"""산림청 등산로정보(trailInfoService) 시험 호출. 키는 기록하지 않음."""
import json, os, urllib.parse, urllib.request, urllib.error
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
BASES = ['https://apis.data.go.kr/1400000/trailInfoService/', 'https://apis.data.go.kr/1400000/trailInfoService']
OPS = ['', 'getTrailInfoList', 'trailInfoList', 'getTrailInfo', 'trailInfo', 'getForestTrailInfoList', 'getTrailList', 'gdTrailInfoOpenAPI', 'trailInfoOpenAPI', 'getMntnTrailInfo', 'getForestTrailInfo']
res = []
def hit(url, **p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, **p))
    try:
        with urllib.request.urlopen(url + '?' + q, timeout=40) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, str(e)
for op in OPS:
    url = BASES[0] + op
    st, body = hit(url, mntnNm='강천산', pageNo=1, numOfRows=3)
    res.append({'op': op, 'status': st, 'body': body[:1200].replace(KEY, '***')})
json.dump(res, open('scripts/trail_probe.json', 'w'), ensure_ascii=False, indent=1)
