#!/usr/bin/env python3
"""산림청 등산로정보로 산별 등산로 규모 계산 (GPT 코스 거리 검증용). 키는 기록하지 않음."""
import json, os, io, re, zipfile, heapq, math, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import shapefile
from pyproj import CRS, Transformer
KEY = os.environ.get('DATA_GO_KR_KEY', '').strip()
URL = 'https://apis.data.go.kr/1400000/trailInfoService/getforestspatialdataservice'
import time
def retry(fn, n=4):
    for i in range(n):
        try: return fn()
        except Exception:
            if i == n - 1: raise
            time.sleep(3 * (i + 1))
def api(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, **p))
    def f():
        with urllib.request.urlopen(URL + '?' + q, timeout=60) as r: return r.read().decode('utf-8', 'replace')
    return retry(f)
def hav(a, b, c, d):
    R = 6371000; p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))
src = json.load(open('scripts/trail_verify_source.json'))
out = []
for s in src:
    nm = s['n']; base = re.sub(r'\(.*?\)', '', nm); o = {'n': nm}
    try:
        items = []
        for pg in (1, 2):
            root = ET.fromstring(api(pageNo=pg, numOfRows=50, mntnNm=base))
            items += root.findall('.//item')
            if len(items) >= int(root.findtext('.//totalCount') or 0): break
        o['cands'] = len(items)
        best = None
        for it in items:
            if (it.findtext('mntnnm') or '').strip() != base: continue
            data = retry(lambda: urllib.request.urlopen(it.findtext('mntnfile'), timeout=90).read())
            z = zipfile.ZipFile(io.BytesIO(data))
            way = [n for n in z.namelist() if n.lower().endswith('.shp') and 'WG_MT_WAY' in n.upper()]
            if not way: continue
            b = way[0][:-4]
            sf = shapefile.Reader(shp=io.BytesIO(z.read(b + '.shp')), dbf=io.BytesIO(z.read(b + '.dbf')), encoding='cp949')
            prj = [n for n in z.namelist() if n.lower().endswith('.prj')]
            CANDS = {
              'bessel500k': '+proj=tmerc +lat_0=38 +lon_0=127.0028902777778 +k=1 +x_0=200000 +y_0=500000 +ellps=bessel +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43 +units=m +no_defs',
              'grs80_600k': '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m +no_defs',
              'grs80_500k': '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=500000 +ellps=GRS80 +units=m +no_defs',
              'bessel600k': '+proj=tmerc +lat_0=38 +lon_0=127.0028902777778 +k=1 +x_0=200000 +y_0=600000 +ellps=bessel +units=m +no_defs',
              'epsg5174': 'EPSG:5174', 'epsg5186': 'EPSG:5186'}
            raw = []
            for sr in sf.shapeRecords():
                pts = sr.shape.points
                if len(pts) < 2: continue
                rec = sr.record.as_dict()
                dist = float(rec.get('SECTN_DSTN') or 0) or float(rec.get('Shape_Leng') or 0)
                raw.append((pts, dist, float(rec.get('SECTN_UPLN') or 0)))
            bestc = None
            for cn, cdef in CANDS.items():
                tf = Transformer.from_crs(CRS.from_user_input(cdef), 4326, always_xy=True)
                segs_c = []
                for pts, dist, up in raw:
                    mid = tf.transform(*pts[len(pts) // 2])
                    segs_c.append((pts[0], pts[-1], dist, up, mid, None))
                clat = sum(q[4][1] for q in segs_c) / len(segs_c); clng = sum(q[4][0] for q in segs_c) / len(segs_c)
                dcc = hav(s['lat'], s['lng'], clat, clng) if s.get('lat') else 0
                if bestc is None or dcc < bestc[0]: bestc = (dcc, cn, segs_c, clat, clng)
            o['crs'] = bestc[1]; segs = bestc[2]
            if not segs: continue
            # 중심 좌표
            clat = sum(s_[4][1] for s_ in segs) / len(segs); clng = sum(s_[4][0] for s_ in segs) / len(segs)
            dc = hav(s['lat'], s['lng'], clat, clng) if s.get('lat') else 0
            if best is None or dc < best[0]: best = (dc, segs, clat, clng, len(items))
        if not best: o['status'] = 'no_match'; out.append(o); continue
        dc, segs, clat, clng, nc = best
        o['center_off_m'] = round(dc); o['n_seg'] = len(segs)
        o['total_km'] = round(sum(s_[2] for s_ in segs) / 1000, 2)
        o['up_min_total'] = round(sum(s_[3] for s_ in segs))
        if s.get('lat'):
            o['summit_to_trail_m'] = round(min(hav(s['lat'], s['lng'], s_[4][1], s_[4][0]) for s_ in segs))
        # 그래프: 끝점 2m 격자 스냅
        key = lambda p: (round(p[0] / 3), round(p[1] / 3))
        adj = {}
        for a, b_, d, t, m, ll in segs:
            ka, kb = key(a), key(b_)
            adj.setdefault(ka, []).append((kb, d)); adj.setdefault(kb, []).append((ka, d))
        def dij(st):
            dist = {st: 0}; pq = [(0, st)]
            while pq:
                d0, u = heapq.heappop(pq)
                if d0 > dist[u]: continue
                for v, w in adj[u]:
                    if d0 + w < dist.get(v, 1e18): dist[v] = d0 + w; heapq.heappush(pq, (d0 + w, v))
            return dist
        st = next(iter(adj)); d1 = dij(st); far = max(d1, key=d1.get); d2 = dij(far)
        o['diam_km'] = round(max(d2.values()) / 1000, 2); o['comp_nodes'] = len(d2); o['all_nodes'] = len(adj)
        o['status'] = 'ok'
    except Exception as e:
        o['status'] = 'error'; o['error'] = str(e).replace(KEY, '***')[:200]
    out.append(o)
json.dump(out, open('scripts/trail_verify.json', 'w'), ensure_ascii=False, indent=1)
