#!/usr/bin/env python3
"""TourAPI 음식점 전국 목록 -> food.json (앱용 축약본). 키는 기록하지 않음.
항목: [id, 이름, 주소, 위도, 경도, 분류번호, 사진주소(없으면 ''), 저작권유형(1/3, 사진 없으면 0)]"""
import json, os, urllib.parse, urllib.request, time, collections, gzip, datetime, re, random
KEY = urllib.parse.unquote(os.environ.get('KTO_API_KEY', '').strip())
BASE = 'https://apis.data.go.kr/B551011/KorService2/areaBasedList2'
def call(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, MobileOS='ETC', MobileApp='sanguruem', _type='json', **p))
    err = ''
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + '?' + q, headers={'Accept': 'application/json'}), timeout=60) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))['response']['body']
        except Exception as e:
            err = str(e).replace(KEY, '***'); time.sleep(3)
    raise SystemExit('API 실패: ' + err)
items = []; pg = 1
while True:
    b = call(contentTypeId=39, numOfRows=1000, pageNo=pg)
    it = (b.get('items') or {}).get('item', []) if isinstance(b.get('items'), dict) else []
    items += it
    if len(it) < 1000 or pg > 30: break
    pg += 1
KINDS = ['한식', '중식', '일식', '양식', '분식·간식', '카페·빵', '기타']
def kind(c):
    if c.startswith('FD01'): return 0
    if c == 'FD020100': return 1
    if c == 'FD020200': return 2
    if c == 'FD020300': return 3
    if c.startswith('FD02'): return 6
    if c.startswith('FD03'): return 5 if c in ('FD030100',) else 4
    if c.startswith('FD05'): return 5
    return -1   # 술집 등은 뺌
seen = set(); out = []; stat = collections.Counter(); drop = collections.Counter()
for i in items:
    cid = i.get('contentid')
    if cid in seen: drop['중복'] += 1; continue
    seen.add(cid)
    try: lat = round(float(i['mapy']), 5); lng = round(float(i['mapx']), 5)
    except Exception: drop['좌표없음'] += 1; continue
    if not (33 <= lat <= 39 and 124 <= lng <= 132): drop['좌표 범위 밖'] += 1; continue
    k = kind(i.get('lclsSystm3') or '')
    if k < 0: drop['제외 분류(술집 등)'] += 1; continue
    cp = i.get('cpyrhtDivCd') or ''
    img = (i.get('firstimage2') or i.get('firstimage') or '') if cp in ('Type1', 'Type3') else ''
    t = (1 if cp == 'Type1' else 3) if img else 0
    if cp and not img and cp in ('Type1', 'Type3'): stat['사진주소 없음'] += 1
    out.append([cid, (i.get('title') or '').strip(), (i.get('addr1') or '').strip(), lat, lng, k, img, t]); stat[KINDS[k]] += 1
# 사진 주소 앞부분 줄이기
imgs = [o[6] for o in out if o[6]]
pre = collections.Counter(re.match(r'(https?://[^/]+/[^/]+/[^/]+/)', u).group(1) if re.match(r'(https?://[^/]+/[^/]+/[^/]+/)', u) else '' for u in imgs)
P = [p for p, n in pre.most_common(3) if p and n > 100]
for o in out:
    for n, p in enumerate(P):
        if o[6].startswith(p): o[6] = '%d|' % n + o[6][len(p):]; break
doc = {'updated': datetime.date.today().isoformat(), 'count': len(out), 'kinds': KINDS, 'pre': P, 'items': out}
txt = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
open('food.json', 'w', encoding='utf-8').write(txt)
# 사진 서버 확인(표본): https로 되는지, 크기
random.seed(1); samp = random.sample([o for o in items if (o.get('cpyrhtDivCd') in ('Type1', 'Type3')) and (o.get('firstimage2') or o.get('firstimage'))], 12)
probe = []
for o in samp:
    u = o.get('firstimage2') or o.get('firstimage'); r = {'url_scheme': u.split(':')[0], 'host': urllib.parse.urlparse(u).netloc, 'which': 'thumb' if o.get('firstimage2') else 'full'}
    for sch in ('https', 'http'):
        uu = sch + ':' + u.split(':', 1)[1]
        try:
            with urllib.request.urlopen(urllib.request.Request(uu, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as rr:
                d = rr.read(); r[sch] = {'status': rr.status, 'type': rr.headers.get('Content-Type'), 'bytes': len(d)}
        except Exception as e: r[sch] = 'ERR ' + str(e)[:60]
    probe.append(r)
rep = {'raw_downloaded': len(items), 'kept': len(out), 'dropped': dict(drop), 'by_kind': dict(stat), 'with_photo': sum(1 for o in out if o[6]),
       'photo_type': dict(collections.Counter(o[7] for o in out)), 'file_bytes': len(txt.encode()), 'gzip_bytes': len(gzip.compress(txt.encode())),
       'prefixes': P, 'thumb_share': sum(1 for o in items if o.get('firstimage2')) , 'image_probe': probe, 'sample': out[:3]}
json.dump(rep, open('scripts/food_build_report.json', 'w'), ensure_ascii=False, indent=1)
