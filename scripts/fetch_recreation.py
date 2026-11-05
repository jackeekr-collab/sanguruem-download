"""전국휴양림표준데이터 API(tn_pubr_public_rcrfrst_api) → recreation.json (앱이 읽는 파일)
설정(Secrets): RECREATION_API_KEY (없으면 FOREST_API_KEY, KTO_API_KEY 순으로 사용)
출처: 공공데이터포털 전국휴양림표준데이터 (저작자표시, CC BY)"""
import json, os, re, sys, time, datetime, urllib.parse, urllib.request

BASE = "https://api.data.go.kr/openapi/tn_pubr_public_rcrfrst_api"
raw = next((os.environ.get(k, "").strip() for k in ("RECREATION_API_KEY", "FOREST_API_KEY", "KTO_API_KEY") if os.environ.get(k, "").strip()), "")
if not raw:
    sys.exit("API 키 시크릿이 없습니다 (RECREATION_API_KEY / FOREST_API_KEY / KTO_API_KEY)")
KEY = urllib.parse.unquote(raw)
KST = datetime.timezone(datetime.timedelta(hours=9))
REG = [('서울', 0), ('경기', 0), ('인천', 0), ('강원', 1), ('충청북', 2), ('충북', 2), ('충청남', 3), ('충남', 3), ('대전', 3), ('세종', 3), ('전라남', 4), ('전남', 4), ('광주', 4), ('전라북', 5), ('전북', 5), ('경상남', 6), ('경남', 6), ('부산', 6), ('울산', 6), ('경상북', 7), ('경북', 7), ('대구', 7), ('제주', 8)]
NAMES = ['서울,경기권', '강원권', '충북권', '충남권', '전남권', '전북권', '경남권', '경북권', '제주권']


def call(page):
    q = urllib.parse.urlencode({"serviceKey": KEY, "pageNo": page, "numOfRows": 200, "type": "json"})
    last = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(BASE + "?" + q, timeout=40) as r:
                j = json.loads(r.read().decode("utf-8"))
            root = j.get("response", j)
            hdr = root.get("header", {})
            if hdr.get("resultCode") not in ("00", "0000"):
                sys.exit("API 오류: %s" % hdr)
            body = root.get("body", {})
            items = body.get("items") or []
            if isinstance(items, dict):
                items = items.get("item", [])
            if isinstance(items, dict):
                items = [items]
            return items, int(body.get("totalCount") or 0)
        except SystemExit:
            raise
        except Exception as e:
            last = e
            time.sleep(3)
    sys.exit("호출 실패: %s" % type(last).__name__)


s = lambda v: re.sub(r"\s+", " ", str(v or "")).strip()
out, seen, page, total = [], set(), 1, 0
while True:
    items, total = call(page)
    for it in items:
        n, ad = s(it.get("rcrfrstNm")), s(it.get("rdnmadr"))
        try:
            lat, lng = float(it.get("latitude")), float(it.get("longitude"))
        except Exception:
            continue
        key = (n, ad.split(" ", 1)[-1])
        if not n or key in seen:
            continue
        seen.add(key)
        rg = next((NAMES[i] for k, i in REG if (s(it.get("ctprvnNm")) or ad).startswith(k)), "")
        fee = s(it.get("admfee"))
        fee = "무료" if fee in ("0", "없음", "무료", "별도 입장료 없음") else fee
        url = s(it.get("homepageUrl"))
        if url and not url.startswith("http"):
            url = "https://" + url
        try:
            cap = int(float(it.get("aceptncCo")))
        except Exception:
            cap = None
        out.append({"n": n, "rg": rg, "ty": s(it.get("rcrfrstType")), "ad": ad, "tel": s(it.get("telephoneNumber")), "fee": fee,
                    "stay": s(it.get("stayngPosblYn")) == "Y", "fac": s(it.get("mainFcltyNm")), "org": s(it.get("institutionNm")),
                    "cap": cap, "url": url, "lat": lat, "lng": lng})
    if page * 200 >= total or not items:
        break
    page += 1
if len(out) < 100:
    sys.exit("수집된 휴양림이 너무 적습니다(%d) — 기존 파일 유지" % len(out))
json.dump({"updated": datetime.datetime.now(KST).strftime("%Y-%m-%d"), "count": len(out), "items": out},
          open("recreation.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("완료: %d곳 (API 전체 %d건, 중복 정리 후)" % (len(out), total))
