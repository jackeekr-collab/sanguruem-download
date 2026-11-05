"""전국휴양림표준데이터 API 응답 항목 확인용(임시). 키는 출력하지 않고, 항목 이름과 첫 2건만 보여 준다."""
import json, os, sys, urllib.parse, urllib.request

BASE = "https://api.data.go.kr/openapi/tn_pubr_public_rcrfrst_api"
names = ["RECREATION_API_KEY", "FOREST_API_KEY", "KTO_API_KEY"]
for nm in names:
    raw = os.environ.get(nm, "").strip()
    if not raw:
        print(nm, ": 없음")
        continue
    key = urllib.parse.unquote(raw)
    q = urllib.parse.urlencode({"serviceKey": key, "pageNo": 1, "numOfRows": 2, "type": "json"})
    try:
        with urllib.request.urlopen(BASE + "?" + q, timeout=40) as r:
            txt = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(nm, ": 호출 실패", type(e).__name__, str(e)[:120])
        continue
    print(nm, ": 응답 길이", len(txt))
    try:
        j = json.loads(txt)
    except Exception:
        print("JSON 아님:", txt[:300].replace(key, "***"))
        continue
    root = j.get("response", j)
    body = root.get("body", {})
    hdr = root.get("header", {})
    print("header:", hdr, "totalCount:", body.get("totalCount"))
    items = body.get("items")
    if isinstance(items, dict):
        items = items.get("item", items)
    if isinstance(items, list) and items:
        print("항목 이름:", list(items[0].keys()))
        for it in items[:2]:
            print(json.dumps(it, ensure_ascii=False)[:1500])
        break
    print("items 없음:", json.dumps(j, ensure_ascii=False)[:1200])
