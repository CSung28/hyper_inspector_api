# Hyper Inspector API

Tableau `.hyper` 파일을 업로드하고, 테이블 구조와 샘플 데이터를 확인한 뒤 Hyper SQL 기반 Insight 분석까지 실행할 수 있는 FastAPI 앱입니다.

## 주요 기능

- `.hyper` 파일 업로드
- Hyper 파일 안의 테이블 목록 확인
- 선택한 테이블의 스키마, row count, preview 확인
- preview CSV 다운로드
- 웹 UI에서 `데이터 확인` / `Insight 분석` 탭 분리
- 데이터 미리보기 표 가로 스크롤 지원
- Hyper SQL 집계 기반 profile 생성
- 컬럼 역할 후보 탐지
  - 날짜 컬럼 후보
  - 측정값 후보
  - Sales, Profit, Quantity 후보
  - 차원 컬럼 후보
- 자연어 질문을 분석 계획 JSON으로 변환
- 검증된 분석 계획만 내부 SQL builder로 Hyper SQL 생성
- SELECT 쿼리만 실행
- LLM API key가 없을 때 rule-based planner로 동작

## Insight 분석 흐름

인사이트 탭에서는 정해진 추천 버튼 중심이 아니라, 사용자가 자연어로 질문하면 다음 순서로 처리합니다.

1. 사용자가 자연어 질문 입력
2. `POST /hyper/{file_id}/ask` 호출
3. Hyper profile 정보 생성
4. 질문을 구조화된 query plan JSON으로 변환
5. query plan을 실제 profile과 대조해 검증
6. 검증된 plan만 내부 `sql_builder`로 SELECT Hyper SQL 생성
7. Hyper SQL 집계 쿼리 실행
8. 자연어 답변, KPI/표, 사용 컬럼, 기간, 가정, confidence, SQL 반환

## 지원 질문 예시

- `최근 3개월 Sales 매출은 얼마야?`
- `월별 Sales 추이를 보여줘`
- `Region별 Sales TOP 5`
- `최근 월 Sales 전월 대비`
- `Category별 Profit 합계를 보여줘`
- `Order Date 기준으로 가장 최근 데이터는 언제야?`
- `데이터는 언제부터 언제까지 있어?`

## 지원 intent

- `recent_period_sum`
- `monthly_trend`
- `top_n_by_dimension`
- `month_over_month`
- `overall_sum`
- `overall_avg`
- `min_max_date`
- `row_count`
- `distinct_count`
- `null_count`
- `unsupported`

## API

기존 Hyper API:

- `GET /health`
- `POST /hyper/upload`
- `GET /hyper/{file_id}/tables`
- `GET /hyper/{file_id}/schema`
- `GET /hyper/{file_id}/row-count`
- `GET /hyper/{file_id}/preview`
- `GET /hyper/{file_id}/preview.csv`

Profile / Insight API:

- `GET /hyper/{file_id}/profile`
- `GET /hyper/{file_id}/insights/suggestions`
- `POST /hyper/{file_id}/insights/query`
- `GET /hyper/{file_id}/insights/monthly-trend`
- `GET /hyper/{file_id}/insights/top-n`

자연어 질문 API:

- `POST /hyper/{file_id}/ask`
- `POST /hyper/{file_id}/ask/plan`
- `POST /hyper/{file_id}/ask/execute-plan`

## 환경 변수

`.env.example`을 참고해 설정합니다.

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

`OPENAI_API_KEY`가 없으면 OpenAI 호출 없이 rule-based planner로 동작합니다.

## 실행 방법

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

웹 UI:

```text
http://127.0.0.1:8001/
```

API 문서:

```text
http://127.0.0.1:8001/docs
```

## 테스트

```bash
pytest -q
```

현재 테스트는 LLM 없이 rule-based planner와 query plan validator가 예시 질문을 처리하는지 확인합니다.

## 지금까지 추가된 작업 정리

`Hyper Inspector API 개발 1` 작업에서 추가/개선한 내용:

- 초보자가 보기 쉬운 웹 UI 구성
- 업로드, 테이블 선택, schema, row count, preview 확인 흐름 정리
- 데이터 확인 탭과 Insight 분석 탭 분리
- preview 테이블 가로 스크롤 처리
- `hyper_profiler.py` 추가
  - 테이블 row count
  - 컬럼별 null count, distinct count, min/max
  - 날짜 min/max
  - 숫자형 sum/avg
  - 텍스트 top values
- `semantic_detector.py` 추가
  - 날짜, 측정값, Sales, Profit, Quantity, 차원 후보 탐지
  - confidence score 제공
- `sql_builder.py` 추가 및 확장
  - Hyper 테이블명/컬럼명 안전 처리
  - SELECT-only 검사
  - query plan 기반 Hyper SQL 생성
- `insight_engine.py` 추가 및 확장
  - 최근 기간 합계
  - 월별 추이
  - 차원별 TOP N
  - 전월 대비
  - 검증된 query plan 실행
- `insight_routes.py` 추가
  - profile, suggestions, insight query API 제공
- `ask_routes.py` 추가
  - 자연어 질문 API 제공
  - plan 생성 전용 API 제공
  - 검증된 plan 실행 API 제공
- `nl_query_planner.py` 추가
  - OpenAI JSON planner 연동
  - API key 미설정 시 rule-based planner fallback
- `query_plan_validator.py` 추가
  - profile에 존재하는 테이블/컬럼만 허용
  - intent별 필수 컬럼 검증
  - 타입 검증
  - aggregation, limit, filter 검증
  - 존재하지 않는 컬럼은 후보 제안 후 clarification 반환
- `answer_formatter.py` 추가
  - KPI/표 결과를 사용자 친화적 자연어 답변으로 변환
- 자연어 Insight UI 추가
  - 질문 입력창
  - 실행 버튼
  - 계획만 보기 버튼
  - 결과 답변
  - KPI/테이블
  - 사용 테이블/컬럼/기간
  - 가정과 confidence
  - SQL 보기 토글

