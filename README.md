# TrendOps: LLM 기반 산업 트렌드 요약 서비스

## Intro.
- 개요: 국내 주요 기업의 산업 트렌드를 분석하여 제공하는 서비스
- 배경: 취준하면서 자소서 쓸때 기업 산업트렌드 분석을 반복하며 관련 서비스가 있으면 좋겠다고 느낌

- 시퀀스
    1. 매일 1번씩 국내 대기업 관련 뉴스를 크롤링
        - 주기적으로 크롤링하다 ip차단될 경우 존재?
    2. 매주 1번씩 크롤링된 데이터에서 정보를 요약함
        - 구현 어떻게 할지… ML적으로 어떻게 풀지?
        - 원본 데이터를 모두 저장하고 → 요약하고 → 그걸로 새로운 데이터 생성
    3. 등록된 사용자에게 요약된 정보를 메일로 전달
        - 각각 사용자마다 관심있는 기업/직무별로 구분해서 메일 보내야할듯
        - 웹사이트는 어떻게 구축해야할지..

- 서비스 분리
    1. 크롤링
        - `selenium`
    2. api 서버: steamlit(ui, 웹사이트와의 통신)
        - `fastAPI`
    3. ML: 실제로 데이터 요약하고 생성
        - `transformers`, `pandas` → `vllm` (서빙하기 위해), `sglang` 을 써서 serving해보는거 추천. 실제로 왜 쓰는지 스터디 해보는거 추천!!
    4. 스케줄러: 매일/매주 크롤링, 메일 보내도록 지정
        - `airflow` ??? → 리눅스 환경이라면 크론탭 이용해서 그냥 스케줄링 하는것도 괜찮음
    5. db: db 관리 → 크롤링한 데이터를 rdb를 어떻게 저장할지도 고민 필요(스키마 설계)
        - `sql`, `pandas`
    6. vector-db: (관계형 DB와는 데이터 구조와 검색 방식이 완전히 다르므로, 전문 데이터베이스를 독립적으로 운영하는 것이 효율적입니다.) ← 라고 하는데 진짜 필요할지..?
        - 특정 키워드, 내용 기준으로 데이터를 모은다고 할 경우 필요할수도..

-----
# Milestone

## 1주 차: 데이터 수집 및 저장 (Foundation)

🎯 주간 목표: 크롤링으로 데이터를 수집 --> Docker 컨테이너로 실행되는 DB에 적재하는 파이프라인 구축

### Day 1-2: 학습 및 기본 테스트
- 학습:
    - [ ] `requests`, `BeautifulSoup4` 사용법
    - [ ] PostgreSQL 기본 (`CREATE`, `INSERT`, `SELECT`)
- 구현:
    - [ ] `docker pull postgres` 실행 및 접속
    - [ ] 로컬에서 뉴스 기사 제목/본문 크롤링 테스트

### Day 3-6: 구현 및 통합
- 학습:
  -  [ ] Python DB 연결 (`SQLAlchemy` 또는 `psycopg2`)
- 구현:
    - [ ] `crawler.py`: 뉴스 기사(제목, 본문, URL 등) 수집 스크립트 작성
    - [ ] `database.py`: DB 연결 및 수집 데이터 `INSERT` 로직 구현
    - [ ] `docker-compose.yml` (v1): `postgres` 서비스 정의

🏁 1주 차 마일스톤: `crawler.py` 실행 시, Docker 컨테이너 DB에 뉴스 원문이 적재됨

---

## 2주 차: 핵심 로직 (ML) 및 컨테이너화

🎯 주간 목표: DB에 쌓인 데이터를 ML 모델로 요약하고, 전체 파이프라인(크롤러, 요약기, DB)을 `docker-compose`로 통합합니다.

### Day 1: 학습 및 모델 테스트
- 학습:
    - [ ] HuggingFace `transformers` 라이브러리
    - [ ] 요약 파이프라인 사용법 (e.g., `gogamza/kobart-summarization`)
- 구현:
    - [ ] 로컬에서 DB 데이터로 요약 기능 테스트

### Day 2-5: 구현 및 Docker화
- 학습:
    - [ ] `Dockerfile` 작성법
- 구현:
    - [ ] `summarizer.py`: DB에서 기사를 `SELECT` -> 모델로 요약 -> 결과를 DB에 `UPDATE`
    - [ ] `Dockerfile` 작성 (crawler, summarizer 각각)
    - [ ] `docker-compose.yml` (v2): `crawler`, `summarizer` 서비스 추가 (`depends_on` 설정)

🏁 2주 차 마일스톤: `docker-compose up` 명령어로 크롤링과 요약이 순차적으로 실행되고 DB에 저장됨

---

## 3주 차: 결과 시각화 (UI) 및 기본 자동화

🎯 주간 목표: 사용자가 요약된 결과를 볼 수 있는 웹 UI를 만들고, 데이터 수집/요약을 주기적으로 실행되도록 구성합니다.

### Day 1: 학습 및 UI 테스트
- 학습:
    - [ ] `Streamlit` 기본 사용법 (`st.title`, `st.dataframe`)
- 구현:
    - [ ] Streamlit으로 `pandas` DataFrame 출력 테스트

### Day 2-5: 구현 및 자동화
- 학습:
    - [ ] 경량 스케줄링 (e.g., Python `time.sleep` 루프)
- 구현:
    - [ ] `app.py`: Streamlit 앱 작성 (DB 연결 -> 요약 결과 로드 -> 화면 출력)
    - [ ] `Dockerfile` 작성 (streamlit용)
    - [ ] `docker-compose.yml` (v3): `streamlit` 서비스 추가 (포트 `8501` 노출)
    - [ ] `scheduler` 서비스 추가 (e.g., 24시간마다 `crawler`와 `summarizer`를 실행하는 Python 스크립트)

🏁 3주 차 마일스톤: `docker-compose up` 실행 후, `localhost:8501` 접속 시 요약된 뉴스 목록이 웹에 표시됨

---

## 4주 차: 폴리싱 및 선택적 기능 추가

🎯 주간 목표: 프로젝트를 완성도 있게 마무리하고(README 필수), 핵심 기능 외의 부가 기능을 구현합니다.

### Day 1-3: 문서화 및 리팩토링
- 학습:
    - [ ] `README.md` 작성법 (아키텍처 다이어그램 등)
    - [ ] `.env` 파일을 이용한 환경변수 관리 (`python-dotenv`)
- 구현:
    - [ ] README.md 작성 (필수)
        - [ ] 프로젝트 개요, 아키텍처 다이어그램, 실행 방법 (`docker-compose up`) 포함
    - [ ] 코드 리팩토링 (DB 접속 정보 등 `.env`로 분리)

### Day 4-6: 선택적 기능 추가
- 학습:
    - [ ] Python `smtplib` (메일 발송)
- 구현:
    - [ ] (Optional) `emailer.py`: DB에서 요약본을 가져와 메일로 발송하는 스크립트 작성
    - [ ] (Optional) `scheduler`가 `emailer.py`도 실행하도록 추가

🏁 최종 마일스톤: 누구나 `README.md`를 보고 프로젝트를 손쉽게 실행할 수 있음
