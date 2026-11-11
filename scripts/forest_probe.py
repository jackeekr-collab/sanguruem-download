#!/usr/bin/env python3
"""산림청 명산등산로 API 시험 호출. 결과: scripts/forest_probe.json (키는 기록하지 않음)"""
import json, os, urllib.parse, urllib.request, urllib.error
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
BASE = 'https://apis.data.go.kr/1400000/'
paths = ['cultureInfoService', 'cultureInfoService/', 'service/cultureInfoService',
         'cultureInfoService/mntInfoOpenAPI', 'service/cultureInfoService/mntInfoOpenAPI',
         'service/cultureInfoService/mntInfoOpenAPI2', 'cultureInfoService/mntInfoOpenAPI2',
         'cultureInfoService/cultureInfoList', 'cultureInfoService/getCultureInfoList',
         'service/cultureInfoService/gdTrailInfoOpenAPI', 'service/cultureInfoService/gdTrailInfoOpenAPI2']
def hit(url):
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:900]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:300]
    except Exception as e:
        return 0, str(e)[:200]
out = []
if not KEY: out.append({'error': 'no key'})
for p in paths:
    q = urllib.parse.urlencode({'serviceKey': KEY, 'pageNo': 1, 'numOfRows': 3, 'searchMtNm': '설악산'})
    st, body = hit(BASE + p + '?' + q)
    out.append({'path': p, 'status': st, 'body': body.replace(KEY, '***') if KEY else body})
json.dump(out, open('scripts/forest_probe.json', 'w'), ensure_ascii=False, indent=1)
