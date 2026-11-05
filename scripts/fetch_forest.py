"""산림청 명산등산로 API(gdTrailInfoOpenAPI) → forest.json (앱이 읽는 파일)
- 100대명산(블.야) 산 이름으로 검색해 이름이 맞는 산의 정보를 모읍니다.
- 필요한 설정(저장소 Settings > Secrets and variables > Actions):
    FOREST_API_KEY   : 산림청 명산등산로 활용신청이 승인된 인증키 (없으면 KTO_API_KEY를 대신 사용)
    FOREST_API_BASE  : (선택) End Point를 바꿔야 할 때만. 기본값 https://apis.data.go.kr/1400000/cultureInfoService
"""
import json, os, re, sys, time, html, urllib.parse, urllib.request, datetime
import xml.etree.ElementTree as ET

KEY = urllib.parse.unquote((os.environ.get("FOREST_API_KEY", "").strip() or os.environ.get("KTO_API_KEY", "").strip()))
BASE = (os.environ.get("FOREST_API_BASE", "").strip() or "https://apis.data.go.kr/1400000/cultureInfoService").rstrip("/")
if not KEY:
    sys.exit("FOREST_API_KEY(또는 KTO_API_KEY) 시크릿이 없습니다")
KST = datetime.timezone(datetime.timedelta(hours=9))


def clean(t):
    t = t or ""
    for _ in range(3):                      # &lt;br&gt; 처럼 두 번 이스케이프된 경우까지 풀기
        u = html.unescape(t)
        if u == t:
            break
        t = u
    t = re.sub(r"(?i)<\s*br\s*/?>|</p>|</li>|</div>", "\n", t)
    t = re.sub(r"(?i)</?(p|div|span|b|strong|i|em|u|a|img|font|ul|ol|li|table|tbody|thead|tr|td|th|h[1-6])\b[^>]*>", "", t)   # HTML 태그만 제거(<제목> 같은 꺾쇠 글은 유지)
    t = t.replace(" ", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t)
    return t.strip()


def call(name):
    q = urllib.parse.urlencode({"serviceKey": KEY, "pageNo": 1, "numOfRows": 20, "searchMtNm": name})
    url = BASE + "/gdTrailInfoOpenAPI?" + q
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
                return ET.fromstring(r.read())
        except Exception as e:
            last = e
            time.sleep(2)
    print("  실패:", name, last)
    return None


def nm(it):
    return (it.findtext("mntnnm") or it.findtext("mntnm") or "").strip()


def base(s):
    return re.sub(r"\(.*?\)", "", s).strip()


def pick(items, name, reg=""):
    """이름이 같은 산(괄호 안 봉우리 표기는 무시)을 고른다. 같은 이름이 여럿이면 소재지(시·군)로 구분."""
    b = base(name)
    cands = [it for it in items if base(nm(it)) == b]
    if not cands:
        cands = [it for it in items if nm(it) and (base(nm(it)).startswith(b) or b.startswith(base(nm(it))))]
    if len(cands) > 1 and reg:
        tok = reg.split()[-1]                       # 예: "충남 서산시" → "서산시"
        sub = [it for it in cands if tok in (it.findtext("areanm") or "") or tok[:-1] in (it.findtext("areanm") or "")]
        if sub:
            cands = sub
    if not cands:
        return None
    if reg:                                          # 이름만 같고 다른 지역의 산이면 연결하지 않는다
        tok = reg.split()[-1]
        area = cands[0].findtext("areanm") or ""
        if tok not in area and tok[:-1] not in area:
            print("지역 불일치로 제외:", name, "(", reg, ") ≠", nm(cands[0]), "(", area[:40], ")")
            return None
    return cands[0]


def build(it):
    g = lambda k: clean(it.findtext(k))
    o = {"code": g("mntncd"), "nm": g("mntnnm") or g("mntnm"), "sub": g("subnm"), "h": g("mntheight"), "area": g("areanm"),
         "reason": g("aeatreason"), "overview": g("overview"), "course": g("etccourse"), "transport": g("transport"), "tour": g("tourisminf")}
    if not o["overview"]:
        o["overview"] = g("details")[:1500]
    return {k: v for k, v in o.items() if v}


mts = json.load(open(os.path.join(os.path.dirname(__file__), "mountains.json"), encoding="utf-8"))
out, unmatched = {}, []
for m in mts:
    root = call(base(m["n"]))
    time.sleep(0.3)
    if root is None:
        unmatched.append(m["n"] + "(호출 실패)")
        continue
    code = (root.findtext(".//resultCode") or "").strip()
    if code not in ("00", "0000", ""):
        sys.exit("API 오류: %s %s" % (code, root.findtext(".//resultMsg")))
    its = root.findall(".//item")
    it = pick(its, m["n"], m.get("reg", ""))
    if it is None:
        unmatched.append(m["n"])
        print("후보 없음:", m["n"], "→ 검색결과", [nm(x) for x in its][:8])
        continue
    out[m["id"]] = build(it)
    print("OK", m["n"], "→", out[m["id"]].get("nm"))

if not out:
    sys.exit("가져온 산이 없습니다 (End Point/인증키 확인)")
res = {"updated": datetime.datetime.now(KST).strftime("%Y-%m-%d"), "count": len(out), "unmatched": unmatched, "items": out}
json.dump(res, open("forest.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("완료: %d곳, 매칭 안 됨 %d곳: %s" % (len(out), len(unmatched), ", ".join(unmatched)))
