#!/usr/bin/env python3
"""읍면동 좌표 자료 후보 확인: vuski/admdongkor 저장소 목록."""
import json, os, urllib.request
def get(u):
    req = urllib.request.Request(u, headers={'User-Agent': 'sanguruem', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
out = {}
try:
    top = get('https://api.github.com/repos/vuski/admdongkor/contents')
    out['top'] = [(x['name'], x['type'], x.get('size')) for x in top]
    for x in top:
        if x['type'] == 'dir':
            try: out[x['name']] = [(y['name'], y.get('size')) for y in get(x['url'])]
            except Exception as e: out[x['name']] = str(e)[:80]
except Exception as e: out['err'] = str(e)[:200]
json.dump(out, open('scripts/dong_probe.json', 'w'), ensure_ascii=False, indent=1)
