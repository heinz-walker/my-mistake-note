# AI_GUIDE.md

> **목적:** 이 문서는 AI 보조자(예: ChatGPT)가 `my-mistake-note` 코드베이스를 빠르게 이해하고, 정확하게 수정/확장/디버깅을 돕도록 하는 안내서입니다. 민감정보(비밀키/토큰/개인데이터)는 절대 포함하지 않습니다.

---

## 1) 프로젝트 한눈에 보기
- **프로젝트명:** my-mistake-note (오답노트 웹 앱)
- **목표:** 사용자가 틀린 문제를 기록하고, 맞춤형 퀴즈로 효율적 복습을 지원
- **핵심 가치:** 간편한 문제 등록 → 조건 기반 퀴즈 생성 → 즉시 채점/해설 → 취약 영역 분석 대시보드
- **기술 스택:**
  - **백엔드:** Python 3, Django
  - **프런트엔드:** HTML, CSS(Bootstrap 5), JavaScript
  - **데이터베이스:** SQLite3 (개발)
  - **주요 라이브러리:** `django-summernote`(리치 텍스트), `fuzzywuzzy`(주관식 채점), `Chart.js`(시각화), `google-generativeai`(Gemini API)

---

## 2) 실행/개발 환경
> 아래 값/키는 예시입니다. 실제 비밀값은 **.env** 파일로 관리하고, 절대 깃에 올리지 않습니다.

### 로컬 실행(개발)
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # 관리자 계정 생성(선택)
python manage.py runserver
```

### 환경 변수(예시)
```
DJANGO_SETTINGS_MODULE=config.settings
DEBUG=True
# ALLOWED_HOSTS는 개발에서는 빈 값/localhost, 배포 시 도메인 지정
```

### 정적/미디어 파일
- **정적 소스:** `mistake_note/static/`
- **collectstatic 결과:** `staticfiles/` (보통 Git에 **포함하지 않음**)
- **미디어 업로드:** `media/` (예: 문제 이미지 `media/questions/`)

### 권장 `.gitignore` 요약
```
*.pyc
__pycache__/
.DS_Store
.env
/media/
/staticfiles/
db.sqlite3
```

---

## 3) 디렉터리 레이아웃(요약)
```
my-mistake-note/
├─ config/
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  └─ wsgi.py
├─ media/
│  └─ questions/  # 업로드 이미지 저장
├─ mistake_note/
│  ├─ migrations/
│  ├─ static/mistake_note/
│  │  ├─ css/style.css
│  │  └─ js/main.js
│  ├─ templates/
│  │  ├─ admin/mistake_note/question/change_form.html
│  │  ├─ base.html
│  │  └─ mistake_note/
│  │     ├─ add_question.html
│  │     ├─ import_page.html
│  │     ├─ index.html
│  │     ├─ question_detail.html
│  │     ├─ question_list.html
│  │     ├─ question_result.html
│  │     ├─ quiz_select.html
│  │     ├─ quiz_start.html
│  │     ├─ quiz_summary.html
│  │     └─ quiz_take.html
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ forms.py
│  ├─ models.py
│  ├─ tests.py
│  ├─ urls.py
│  └─ views.py
├─ staticfiles/
├─ db.sqlite3
└─ manage.py
```

---

## 4) 주요 페이지/흐름
- **메인(`index.html`)**: 시작 페이지. `문제 추가하기` / `문제 풀기` 버튼 + 최근 추가 문제 목록.
- **문제 추가(`add_question.html`)**: 문제/지문/선택지/해설 입력, 이미지 업로드, CSV 업로드, **AI 검증(Gemini)**.
- **퀴즈 모드 선택(`quiz_select.html`)**: 시험 종류/퀴즈 모드 선택, 조건에 따른 **가능 문제 수 실시간 표시**.
- **퀴즈 풀이(`quiz_take.html`)**: 문제 단건 표시, 제출 시 즉시 정오답/해설, 마지막에 `결과 보기`.
- **결과 요약(`quiz_summary.html`)**: 총점 및 틀린 문제 모아보기(오답노트 역할).
- **학습 대시보드(`dashboard.html`)**: 정답률 추이, 취약 카테고리/태그 시각화(Chart.js).

---

## 5) 문제 추가 페이지(상세)
- **필드 순서:** `시험 종류` → `카테고리` → `문제 종류` → `문제` → `지문(선택)` → `이미지(선택)` → `선택지` → `정답` → `해설` → `태그`
- **리치 텍스트:** `문제`/`지문`/`해설`에 `django-summernote` 적용.
- **동적 동작:**
  - 카테고리: 선택된 `시험 종류`에 따른 필터링
  - 선택지: 객관식/복수정답에서만 표시, 동적 추가/제거
- **관리 편의:** `시험/카테고리` 옆에 **추가 버튼** → 관리자 페이지로 바로 이동
- **AI 검증(Gemini):** `AI 검증` 버튼 → Gemini API로 문제 유효성 검사 및 피드백

---

## 6) 퀴즈 기능(상세)
- **퀴즈 모드:**
  - 전체 / 많이 틀린 문제 / 많이 안 풀어본 문제
  - `객관식만` / `주관식만` / `복수 정답만`
- **문제 수 설정:** 원하는 개수 지정 후 시작
- **실시간 문제 수 표시:** 선택 조건 변경 시 가능한 문제 수 즉시 갱신
- **채점 로직:**
  - **주관식:** `fuzzywuzzy`로 오타 허용(임계값은 설정값으로 관리 권장)
  - **복수 정답:** 정답/응답을 정규화(정렬)하여 정확 비교
- **결과 메시지:** `정답입니다! 🎉` / `틀렸습니다. 😭` + 정답/해설 출력

---

## 7) (요약) 데이터 모델/기록 지표
> 아래는 AI가 이해를 돕기 위한 추론용 요약입니다. 실제 필드명은 `models.py`를 기준으로 확인하세요.
- **Question**: exam(시험), category(카테고리), qtype(문제 종류: 객관/주관/복수), content(문제), passage(지문), image, choices(선택지), answer(정답), explanation(해설), tags
- **Attempt/AnswerLog**: question, user(옵션), is_correct, submitted_at, submitted_answer, elapsed, attempt_count
- **Aggregates**: 정답률, 최근 추세, 카테고리/태그별 취약도(대시보드 용)

---

## 8) API/뷰(발췌 가이드)
- **문제 검증 API:** `validate_question_api` (in `views.py`)
  - 입력: 질문 본문/정답/선택지 등
  - 처리: `google-generativeai`를 이용해 일관성/모호성 점검
  - 출력: 요약 피드백(JSON)
- **퀴즈 흐름:** `quiz_select` → `quiz_start` → `quiz_take` → `quiz_summary`
- **대시보드:** `dashboard` (데이터 집계 후 Chart.js에 투입)

---

## 9) 품질/보안 가이드
- **민감정보 금지:** `SECRET_KEY`, API 키, DB 접속정보는 반드시 `.env`(또는 Secret Manager)로 분리
- **에러 재현 템플릿:**
  - 목표/재현 단계/기대/실제/관련 파일/로그를 함께 제공
- **테스트 권장:**
  - 핵심 로직의 단위테스트(`pytest` 또는 `manage.py test`) 추가
- **타임존/로캘:** `settings.py`에서 `TIME_ZONE='Asia/Seoul'`, `USE_TZ=False` (현 설정 가정)

---

## 10) 알려진 이슈(TODO)
- [ ] **디자인 통일:** `base.html` 기준으로 Bootstrap 스타일링 디테일 보완
- [ ] **Gemini 검증 오류:** `views.py: validate_question_api` 호출/응답 처리 개선 필요
- [ ] **대시보드 데이터 가공:** `dashboard.html` 그래프용 집계 로직 연결
- [ ] **태그 시스템 오류:** `admin.py`의 태그 표시/동작 점검
- [ ] **(참고) SQLite "database is locked" 간헐:** 동시 쓰기/긴 트랜잭션 시 발생 가능 → 트랜잭션 범위 축소/재시도/단일 워커 개발 모드 권장

---

## 11) 협업/브랜치 전략(권장)
- 기본 브랜치: `main`
- 보호 규칙: PR 필수, 상태체크 필수(선택)
- 커밋 메시지: `feat:`, `fix:`, `refactor:`, `docs:` 등 관례 사용
- PR 템플릿: 목표/변경점/테스트/스크린샷/리스크/관련 이슈

---

## 12) AI에게 질문하는 법(템플릿)
```
[목표] 한 줄 요약
[상황] 재현 단계, 기대/실제 동작
[맥락] 버전/환경(로컬/배포), 의존성
[파일] 관련 파일/코드블록 (또는 링크)
[제약] 변경 금지 영역/마감/성능 요구
[출력형식] 코드 패치만 / 단계별 설명 / 테스트 포함 등
```

---

## 13) 부록: 빠른 문제해결 메모
- 정적/미디어 경로 꼬임 → `STATIC_URL/STATICFILES_DIRS/STATIC_ROOT` vs `MEDIA_*` 재확인
- Summernote 높이/넓이/툴바 → `settings.py`의 `SUMMERNOTE_CONFIG`
- CSV 업로드 인코딩 문제 → `utf-8-sig` 처리 권장
- 퍼포먼스(나중) → Postgres 전환, 인덱스/셀렉터 최적화, N+1 쿼리 점검
