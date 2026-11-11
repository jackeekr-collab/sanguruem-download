#!/usr/bin/env python3
"""산림청 명산등산로 API 시험 호출. 결과: scripts/forest_probe.json (키는 기록하지 않음)"""
import json, os, re, urllib.parse, urllib.request, urllib.error
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
BASE = 'https://apis.data.go.kr/1400000/cultureInfoService/'
def hit(op, **p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, pageNo=1, numOfRows=5, **p))
    try:
        with urllib.request.urlopen(BASE + op + '?' + q, timeout=25) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, str(e)
out = []
for nm in ['설악산', '북한산', '강천산']:
    st, body = hit('gdTrailInfoOpenAPI', searchMtNm=nm)
    out.append({'op': 'search', 'q': nm, 'status': st, 'body': body[:2500].replace(KEY, '***')})
    if nm == '설악산':
        m = re.search(r'<(?:mntnid|mntnId|mntiListNo|mntilistno)>(\w+)<', body, re.I)
        out.append({'found_code': m.group(1) if m else None})
        if m:
            st2, b2 = hit('gdTrailInfoImgOpenAPI', searchWrd=m.group(1))
            out.append({'op': 'detail', 'status': st2, 'body': b2[:4000].replace(KEY, '***')})
json.dump(out, open('scripts/forest_probe.json', 'w'), ensure_ascii=False, indent=1)
