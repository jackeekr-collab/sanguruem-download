#!/usr/bin/env python3
"""행정동 경계 자료(vuski/admdongkor 최신판) -> dong.json (시도 > 시군구 > [동, 위도, 경도]). 앱의 '내 등록지' 선택용."""
import json, os, urllib.request, collections, datetime
def get(u, raw=False):
    req = urllib.request.Request(u, headers={'User-Agent': 'sanguruem', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        b = r.read()
    return b if raw else json.loads(b)
vers = sorted(x['name'] for x in get('https://api.github.com/repos/vuski/admdongkor/contents') if x['name'].startswith('ver20'))
rep = {'versions_tail': vers[-4:]}
lic = get('https://raw.githubusercontent.com/vuski/admdongkor/master/LICENSE-DATA', raw=True).decode('utf-8', 'replace')
rep['license_data'] = lic[:1500]
# 가장 최신 판 중 geojson이 있는 것
src = None
for v in reversed(vers):
    fl = get('https://api.github.com/repos/vuski/admdongkor/contents/' + v)
    gj = [f for f in fl if f['name'].lower().endswith('.geojson') and 'HangJeongDong' in f['name']]
    if gj: src = gj[0]; rep['source'] = v + '/' + gj[0]['name']; break
data = json.loads(get(src['download_url'], raw=True))
feats = data['features']
rep['features'] = len(feats); rep['props_sample'] = feats[0]['properties']
def ring_centroid(r):
    a = cx = cy = 0.0
    for i in range(len(r) - 1):
        x0, y0 = r[i][0], r[i][1]; x1, y1 = r[i + 1][0], r[i + 1][1]
        c = x0 * y1 - x1 * y0; a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    if abs(a) < 1e-12: return None
    return cx / (3 * a), cy / (3 * a), abs(a) / 2
def centroid(g):
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    best = None; sx = sy = sa = 0.0
    for p in polys:
        c = ring_centroid(p[0])
        if not c: continue
        sx += c[0] * c[2]; sy += c[1] * c[2]; sa += c[2]
        if best is None or c[2] > best[2]: best = c
    if sa == 0: return None
    # 여러 조각이면 가장 큰 조각의 중심을 사용(섬·비지 때문에 바다 한가운데가 되는 것 방지)
    return (best[0], best[1]) if len(polys) > 1 else (sx / sa, sy / sa)
out = collections.OrderedDict(); n = 0; skip = 0
for f in feats:
    pr = f['properties']; nm = pr.get('adm_nm') or ''
    parts = nm.split()
    if len(parts) < 3: skip += 1; continue
    sido = pr.get('sidonm') or parts[0]; dong = parts[-1]; sgg = ' '.join(parts[1:-1])
    import re as _re
    sgg = _re.sub(r'^(.+?시)(.+구)$', r'\1 \2', sgg)   # 안양시만안구 -> 안양시 만안구
    c = centroid(f['geometry'])
    if not c: skip += 1; continue
    lng, lat = c
    if not (33 <= lat <= 39 and 124 <= lng <= 132): skip += 1; continue
    out.setdefault(sido, collections.OrderedDict()).setdefault(sgg, []).append([dong, round(lat, 5), round(lng, 5)]); n += 1
doc = {'updated': datetime.date.today().isoformat(), 'src': rep.get('source'), 'count': n, 'd': out}
txt = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
open('dong.json', 'w', encoding='utf-8').write(txt)
rep['kept'] = n; rep['skipped'] = skip; rep['bytes'] = len(txt.encode()); rep['sido'] = {k: sum(len(v) for v in s.values()) for k, s in out.items()}
json.dump(rep, open('scripts/dong_build_report.json', 'w'), ensure_ascii=False, indent=1)
