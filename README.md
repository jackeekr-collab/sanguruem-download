# 산구름 배포 저장소 (공개)

- `festivals.json` : 한국관광공사 지역축제 데이터 (GitHub Actions가 매일 2회 자동 갱신) — 앱이 읽음
- `notice.json` : 개발자 공지 / 최신 산행정보 — 이 파일을 수정하면 앱 알림종에 반영됨
- Releases : 산구름 설치 파일(APK)

## 필요한 설정
1. Settings → Secrets and variables → Actions → **New repository secret** → 이름 `KTO_API_KEY`, 값 = 공공데이터포털 인증키
2. Settings → Pages → Source: **Deploy from a branch** / `main` / `/ (root)`
