# Googer

**7개 검색 엔진을 지원하는 Python 멀티 엔진 검색 라이브러리.**

DuckDuckGo · Brave · Google · Ecosia · Yahoo · AOL · Naver — 하나의 API로 통합 검색.

## 설치

```bash
pip install googer
```

## 기본 사용법

```python
from googer import Googer

# 검색 (기본: auto 모드 — 엔진 자동 선택 & 장애 시 자동 전환)
results = Googer().search("python programming")
for r in results:
    print(r.title, r.href)
```

## 엔진 선택

```python
from googer import Googer

# 특정 엔진 지정
g = Googer(engine="brave")
results = g.search("rust language")

# 멀티 엔진 — 여러 엔진 동시 검색 후 결과 병합
g = Googer(engine="multi")
results = g.search("machine learning")

# 메서드별로 엔진 오버라이드
g = Googer(engine="duckduckgo")
results = g.search("AI news", engine="naver")  # 이 호출만 네이버 사용
```

### 지원 엔진

| 엔진 | 텍스트 | 이미지 | 뉴스 | 비디오 |
|------|:---:|:---:|:---:|:---:|
| `duckduckgo` | ✅ | ✅ | ✅ | ✅ |
| `brave` | ✅ | | ✅ | ✅ |
| `google` | ✅ | ✅ | ✅ | ✅ |
| `ecosia` | ✅ | | | |
| `yahoo` | ✅ | | | |
| `aol` | ✅ | | | |
| `naver` | ✅ | | | |

### 엔진 모드

| 모드 | 설명 |
|------|------|
| `auto` | 기본값. 폴백 순서대로 시도하여 첫 성공 엔진 사용 |
| `multi` | 여러 엔진을 동시 호출 후 결과 병합 & 중복 제거 |
| `duckduckgo`, `brave`, ... | 특정 엔진만 사용 |

## 검색 종류

```python
from googer import Googer

g = Googer()

# 텍스트 검색
results = g.search("python", region="ko-kr", max_results=20)

# 이미지 검색
images = g.images("cute cats", size="large", color="color")
for img in images:
    print(img.title, img.image)

# 뉴스 검색 (최근 24시간)
news = g.news("AI", timelimit="d")
for n in news:
    print(n.title, n.source, n.date)

# 비디오 검색 (짧은 영상)
videos = g.videos("python tutorial", duration="short")

# 자동완성 제안
suggestions = g.suggest("python")

# 즉답 (instant answer)
answer = g.answers("python release date")
```

## 고급 쿼리

```python
from googer import Googer, Query

q = (
    Query("machine learning")
    .exact("neural network")
    .site("arxiv.org")
    .filetype("pdf")
    .exclude("tutorial")
)

results = Googer().search(q, max_results=20)
```

## 프록시 & 컨텍스트 매니저

```python
from googer import Googer

# 프록시 (환경변수 GOOGER_PROXY도 지원)
with Googer(proxy="socks5://127.0.0.1:9150") as g:
    results = g.search("privacy tools")

# Tor Browser 단축키
with Googer(proxy="tb") as g:
    results = g.search("onion sites")
```

## 전체 옵션

```python
g = Googer(
    engine="auto",          # auto | multi | duckduckgo | brave | google | ecosia | yahoo | aol | naver
    proxy=None,             # 프록시 URL (http/https/socks5)
    timeout=10,             # 요청 타임아웃 (초)
    max_retries=3,          # 재시도 횟수
    cache_ttl=300,          # 캐시 유지 시간 (초, 0=비활성)
    backend="http",         # http | browser
    headless=True,          # browser 백엔드 사용 시 헤드리스 모드
    verify=True,            # SSL 인증서 검증
)
```

## CLI

```bash
# 텍스트 검색
googer search -q "python programming" -m 5

# 엔진 지정
googer search -q "뉴스" --engine naver

# 멀티 엔진 검색
googer search -q "AI" --engine multi

# 뉴스 (최근 1주)
googer news -q "AI" -t w

# 이미지
googer images -q "landscape" --size large

# 비디오
googer videos -q "cooking" --duration short

# 자동완성
googer suggest -q "python"

# 결과 저장
googer search -q "python" -o results.json
googer search -q "python" -o results.csv

# 프록시
googer search -q "python" --proxy socks5://127.0.0.1:9150

# 버전 확인
googer version
```

### CLI 옵션

| 옵션 | 축약 | 설명 |
|------|------|------|
| `--query` | `-q` | 검색어 (필수) |
| `--engine` | | 엔진 선택 (기본: `auto`) |
| `--region` | `-r` | 지역 코드 (기본: `us-en`) |
| `--safesearch` | `-s` | `on` / `moderate` / `off` |
| `--timelimit` | `-t` | `h`(시간) `d`(일) `w`(주) `m`(월) `y`(년) |
| `--max-results` | `-m` | 최대 결과 수 (기본: `10`) |
| `--backend` | | `http` / `browser` |
| `--proxy` | | 프록시 URL |
| `--timeout` | | 타임아웃 초 (기본: `10`) |
| `--output` | `-o` | `.json` 또는 `.csv` 파일 저장 |
| `--no-color` | | 컬러 출력 비활성화 |

## 환경변수

| 변수 | 설명 |
|------|------|
| `GOOGER_PROXY` | 기본 프록시 URL |

## 요구사항

- Python 3.10+
- [primp](https://github.com/deedy5/primp) — TLS 핑거프린트 임퍼스네이션 HTTP 클라이언트
- [lxml](https://lxml.de/) — HTML 파싱
- [click](https://click.palletsprojects.com/) — CLI 프레임워크

## 라이선스

Apache License 2.0 — [LICENSE.md](LICENSE.md)
