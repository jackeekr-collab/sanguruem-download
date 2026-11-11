#!/usr/bin/env python3
"""산림청 명산등산로 100개 전체 조회. 결과: scripts/forest_all.json (키는 기록하지 않음)"""
import json, os, urllib.parse, urllib.request, urllib.error
import xml.etree.ElementTree as ET
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
BASE = 'https://apis.data.go.kr/1400000/cultureInfoService/'
def hit(op, **p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, **p))
    try:
        with urllib.request.urlopen(BASE + op + '?' + q, timeout=40) as r:
            return r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8', 'replace')
items, total, log = [], None, []
for page in range(1, 8):
    x = hit('gdTrailInfoOpenAPI', pageNo=page, numOfRows=30)
    try: root = ET.fromstring(x)
    except Exception: log.append('parse fail p%d: %s' % (page, x[:200].replace(KEY, '***'))); break
    log.append('p%d %s' % (page, (root.findtext('.//resultMsg') or '')))
    tc = root.findtext('.//totalCount'); total = tc or total
    got = root.findall('.//item')
    for it in got: items.append({c.tag: (c.text or '') for c in it})
    if not got: break
# 상세 조회 1건 (대중교통 항목 확인용)
detail = ''
if items:
    code = items[0].get('mntncd', '')
    detail = hit('gdTrailInfoImgOpenAPI', searchWrd=code, pageNo=1, numOfRows=5)[:3000].replace(KEY, '***')
json.dump({'total': total, 'count': len(items), 'log': log, 'items': items, 'detail_sample': detail},
          open('scripts/forest_all.json', 'w'), ensure_ascii=False, indent=1)
