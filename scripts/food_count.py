#!/usr/bin/env python3
"""TourAPI 음식점(contentTypeId=39) 전국 개수·항목 크기 확인. 키는 기록하지 않음."""
import json, os, urllib.parse, urllib.request, time
KEY = urllib.parse.unquote(os.environ.get('KTO_API_KEY', '').strip())
BASE = 'https://apis.data.go.kr/B551011/KorService2/areaBasedList2'
def call(**p):
    q = urllib.parse.urlencode(dict(serviceKey=KEY, MobileOS='ETC', MobileApp='sanguruem', _type='json', **p))
    err = ''
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + '?' + q, headers={'Accept': 'application/json'}), timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            err = str(e).replace(KEY, '***'); time.sleep(2)
    return 'ERR ' + err
out = {}
txt = call(contentTypeId=39, numOfRows=1, pageNo=1)
try: out['total'] = json.loads(txt)['response']['body']['totalCount']
except Exception: out['total_raw'] = txt[:300].replace(KEY, '***')
# 지역코드별 개수
AR = {1:'서울',2:'인천',3:'대전',4:'대구',5:'광주',6:'부산',7:'울산',8:'세종',31:'경기',32:'강원',33:'충북',34:'충남',35:'경북',36:'경남',37:'전북',38:'전남',39:'제주'}
by = {}
for code, nm in AR.items():
    t = call(contentTypeId=39, areaCode=code, numOfRows=1, pageNo=1)
    try: by[nm] = json.loads(t)['response']['body']['totalCount']
    except Exception: by[nm] = t[:100].replace(KEY, '***')
out['by_area'] = by
# 크기 샘플: 200개를 내려받아 앱용 최소 필드로 변환했을 때 평균 바이트
t = call(contentTypeId=39, numOfRows=200, pageNo=1)
try:
    its = json.loads(t)['response']['body']['items']['item']
    keep = [{'t': i['title'], 'a': i.get('addr1', ''), 'x': i.get('mapx'), 'y': i.get('mapy'), 'c': i.get('cat3'), 'i': i.get('firstimage2') or i.get('firstimage') or ''} for i in its]
    nj = len(json.dumps(keep, ensure_ascii=False).encode('utf-8'))
    out['sample'] = {'n': len(its), 'avg_bytes_with_img': round(nj / len(its)), 'img_rate': round(sum(1 for k in keep if k['i']) / len(keep), 2),
                     'avg_bytes_no_img': round(len(json.dumps([{**k, 'i': ''} for k in keep], ensure_ascii=False).encode('utf-8')) / len(keep)),
                     'fields': sorted(its[0].keys()), 'example': keep[0]}
except Exception:
    out['sample_raw'] = t[:300].replace(KEY, '***')
json.dump(out, open('scripts/food_count.json', 'w'), ensure_ascii=False, indent=1)
