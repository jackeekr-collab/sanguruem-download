"""한국관광공사 TourAPI(KorService2/searchFestival2) → festivals.json (앱이 읽는 파일)"""
import json, os, sys, urllib.parse, urllib.request, datetime

KEY = os.environ.get("KTO_API_KEY", "").strip()
if not KEY:
    sys.exit("KTO_API_KEY 시크릿이 없습니다 (저장소 Settings > Secrets and variables > Actions)")
try:
    KEY = urllib.parse.unquote(KEY)
except Exception:
    pass

BASE = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"
KST = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(KST).date()
start = (today - datetime.timedelta(days=120)).strftime("%Y%m%d")  # 진행 중인 긴 행사까지 포함


def call(page):
    q = urllib.parse.urlencode({
        "serviceKey": KEY, "MobileOS": "ETC", "MobileApp": "sanguruem", "_type": "json",
        "eventStartDate": start, "arrange": "A", "numOfRows": 200, "pageNo": page})
    req = urllib.request.Request(BASE + "?" + q, headers={"Accept": "application/json"})
    txt = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = r.read().decode("utf-8")
            break
        except Exception as e:  # 해외 IP 접속 지연/차단 대비 재시도
            print("시도 %d 실패: %s" % (attempt + 1, e))
    if txt is None:
        sys.exit("공공데이터포털에 연결하지 못했습니다(시간 초과)")
    try:
        j = json.loads(txt)
    except Exception:
        sys.exit("JSON이 아닌 응답: " + txt[:300])
    h = j.get("response", {}).get("header", {})
    if h.get("resultCode") not in ("0000", "00"):
        sys.exit("API 오류: %s" % h)
    body = j["response"].get("body", {})
    items = body.get("items") or {}
    items = items.get("item", []) if isinstance(items, dict) else []
    if isinstance(items, dict):
        items = [items]
    return items, int(body.get("totalCount") or 0)


def d(s):
    s = str(s or "")
    return "%s-%s-%s" % (s[:4], s[4:6], s[6:8]) if len(s) >= 8 else ""


out, page, total = [], 1, 0
while True:
    items, total = call(page)
    for it in items:
        end = d(it.get("eventenddate")) or d(it.get("eventstartdate"))
        if not end or end < today.isoformat():
            continue
        try:
            lat, lng = float(it.get("mapy") or 0) or None, float(it.get("mapx") or 0) or None
        except ValueError:
            lat = lng = None
        out.append({"id": it.get("contentid"), "title": (it.get("title") or "").strip(),
                    "addr": ((it.get("addr1") or "") + " " + (it.get("addr2") or "")).strip(),
                    "start": d(it.get("eventstartdate")), "end": end, "lat": lat, "lng": lng,
                    "img": it.get("firstimage") or "", "tel": it.get("tel") or ""})
    if page * 200 >= total or not items or page >= 20:
        break
    page += 1

if total and not out:
    sys.exit("조회는 되었으나 유효한 축제가 0건 — 기존 파일 유지")
out.sort(key=lambda x: (x["start"], x["title"]))
res = {"updated": today.isoformat(), "count": len(out), "items": out}
with open("festivals.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
print("festivals:", len(out), "of", total)
