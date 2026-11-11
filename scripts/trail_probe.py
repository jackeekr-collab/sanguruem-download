#!/usr/bin/env python3
"""산림청 등산로정보(trailInfoService/getforestspatialdataservice) 시험 호출. 키는 기록하지 않음."""
import json, os, urllib.parse, urllib.request, urllib.error
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
URL = 'https://apis.data.go.kr/1400000/trailInfoService/getforestspatialdataservice'
res = []
def hit(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, **p))
    try:
        with urllib.request.urlopen(URL + '?' + q, timeout=60) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, str(e)
for p in [dict(pageNo=1, numOfRows=3), dict(pageNo=1, numOfRows=3, mntnNm='강천산'), dict(pageNo=1, numOfRows=3, mntnNm='강천산', resultType='json'), dict(pageNo=1, numOfRows=3, MNTN_NM='강천산')]:
    st, body = hit(**p)
    res.append({'params': p, 'status': st, 'len': len(body), 'body': body[:3500].replace(KEY, '***')})
json.dump(res, open('scripts/trail_probe.json', 'w'), ensure_ascii=False, indent=1)
