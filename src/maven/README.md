# Maven Smart System — 지정학 조기경보 + 투자 신호

팔란티어 Maven Smart System 스타일의 다중 데이터 소스 실시간 수집·분석·알림 개인용 시스템.

## 아키텍처

```
┌──────────────────────────────────────────────────┐
│                  Maven System                     │
│                                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────┐ │
│  │AIS Ships│  │ADS-B Air│  │News RSS │  │X API │ │
│  │aisstream│  │ opensky  │  │SearxNG  │  │xurl  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └──┬──┘ │
│       └────────────┴────────────┴───────────┘    │
│                       │                           │
│               ┌───────▼───────┐                   │
│               │   Analyzer    │                   │
│               │  (Claude API) │                   │
│               └───────┬───────┘                   │
│                       │                           │
│               ┌───────▼───────┐                   │
│               │Signal Generator│                  │
│               │  (Telegram)   │                   │
│               └───────────────┘                   │
└──────────────────────────────────────────────────┘
```

## 빠른 시작

### 1. 패키지 설치

```bash
/Users/alis_mini/.pyenv/versions/3.11.11/bin/pip3 install aiohttp feedparser websockets python-dotenv
```

### 2. 환경변수 설정

`.env` 파일을 편집하세요:

```bash
cd /Users/alis_mini/.openclaw/workspace/scripts/maven
vi .env
```

### 3. 실행

```bash
# Python 경로
PYTHON=/Users/alis_mini/.pyenv/versions/3.11.11/bin/python3

# 1회 실행
$PYTHON maven.py --once

# 테스트 알림 (텔레그램 전송 확인)
$PYTHON maven.py --test

# 감시 모드 (5분 간격 루프)
$PYTHON maven.py --watch

# 감시 모드 (커스텀 간격, 10분)
$PYTHON maven.py --watch --interval 10
```

## 환경변수 목록

| 변수 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `AISSTREAM_API_KEY` | aisstream.io API 키 | 선택 (없으면 시뮬레이션) | — |
| `OPENSKY_USERNAME` | OpenSky Network 계정 | 선택 (없으면 비인증) | — |
| `OPENSKY_PASSWORD` | OpenSky Network 비밀번호 | 선택 | — |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | 선택 (게이트웨이 대체) | — |
| `OPENCLAW_GATEWAY_URL` | OpenClaw 게이트웨이 URL | 선택 | `http://localhost:18789` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API 토큰 | 선택 (게이트웨이 대체) | — |
| `TELEGRAM_CHAT_ID` | Telegram 그룹 채팅 ID | 선택 | `-1003868141703` |
| `SEARXNG_URL` | SearxNG 로컬 인스턴스 URL | 선택 | `http://localhost:8080` |
| `XURL_PATH` | xurl CLI 경로 | 선택 | `xurl` (PATH 탐색) |

## 데이터 소스

### AIS 선박 추적 (aisstream.io)
- **감시 지역**: 호르무즈 해협, 말라카 해협
- **감지 이상**: 선박 급감, 급증, 과도한 정박
- **API 키 발급**: https://aisstream.io 무료 가입

### ADS-B 항공기 추적 (OpenSky Network)
- **감시 공역**: 중동, 대만 해협, 한반도
- **감지 이상**: 군용기 5기 이상 집결
- **무료 가입**: https://opensky-network.org

### 뉴스 수집
- **SearxNG**: 로컬 메타 검색 엔진 (localhost:8080)
- **RSS 피드**: Reuters, AP, BBC (World/Asia/Middle East)
- **필터**: 지정학 키워드 매칭, 최근 1시간

### X(Twitter) 소셜
- **xurl CLI** 활용 (X API v2)
- **키워드**: Iran Hormuz, Taiwan Strait, DPRK, semiconductor embargo 등

## 분석 엔진

Claude API를 통해 수집 데이터 통합 분석. 각 이벤트에 대해:
- **severity** (1-5): 위험 수준
- **category**: energy / semiconductor / currency / conflict / other
- **signal**: buy / sell / hedge / hold / watch
- **confidence**: 확신도 (0.0-1.0)
- **affected_assets**: 영향받는 자산

API 호출 순서: OpenClaw 게이트웨이 → Anthropic 직접 → 규칙 기반 폴백

## 알림 규칙

| Severity | 알림 대상 |
|----------|----------|
| 1-2 | 로그만 저장 |
| 3+ | 텔레그램 topic:37 (Geopolitics) |
| 4+ | + 텔레그램 topic:2 (투자/시장) |
| 5 | + 알리스님 개인 DM |

## LaunchAgent (5분 자동 실행)

```bash
# 설치
cp com.alis.maven.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.alis.maven.plist

# 제거
launchctl unload ~/Library/LaunchAgents/com.alis.maven.plist

# 수동 실행
launchctl start com.alis.maven

# 로그 확인
tail -f /tmp/openclaw/maven.log
```

## 대시보드

`src/components/MavenDashboard.tsx` — React 컴포넌트 (Next.js 호환).

기능:
- 최근 이벤트 피드 (severity별 색상 코딩)
- 지역 히트맵 (호르무즈/대만/한반도/유럽/우크라이나)
- 30초 자동 갱신

API: `GET /api/maven/events?limit=50&days=7&severity=1`

## 로그

`logs/maven_YYYYMMDD.jsonl` — 일자별 JSONL 파일.

각 라인은 실행 1회 결과:
```json
{
  "run_id": "20260307_041000",
  "started_at": "2026-03-07T04:10:00Z",
  "ended_at": "2026-03-07T04:10:25Z",
  "duration_seconds": 25.3,
  "collected_counts": {"ais": 2, "adsb": 3, "news": 8, "social": 12},
  "events": [...],
  "signal_result": {"sent": 1, "logged": 2}
}
```

## 파일 구조

```
scripts/maven/
├── maven.py                 # 메인 실행 파일
├── analyzer.py              # Claude API 분석 엔진
├── signal_generator.py      # 알림 발송
├── collectors/
│   ├── __init__.py
│   ├── ais_collector.py     # 선박 AIS
│   ├── adsb_collector.py    # 항공기 ADS-B
│   ├── news_collector.py    # 뉴스 RSS + SearxNG
│   └── social_collector.py  # X(Twitter) xurl
├── logs/                    # 실행 로그 (JSONL)
├── .env                     # 환경변수
├── com.alis.maven.plist     # macOS LaunchAgent
└── README.md
```
