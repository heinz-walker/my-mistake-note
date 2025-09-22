# AI_GUIDE — my-mistake-note

> 목적: AI(예: ChatGPT)가 본 리포를 빠르게 이해하고, **정확한 파일/라인 기준**으로 패치 제안·리팩터·버그픽스를 하도록 돕는 안내서.  
> 주의: 비밀키/토큰/.env/DB 등 민감정보는 절대 커밋하지 말 것.

---

## 1) 프로젝트 개요
- **도메인**: 오답노트 웹앱 — 사용자가 틀린 문제를 기록하고, 조건 기반 퀴즈로 복습
- **핵심 플로우**: 문제 등록 → 퀴즈 조건 선택 → 풀이/채점 → 결과 요약(오답노트) → 대시보드
- **스택**: Django + HTML/CSS(Bootstrap) + JS  
- **개발 DB**: SQLite (배포 전환 시 Postgres 권장)

---

## 2) 빠른 시작(로컬)
```bash
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
# (requirements.txt가 있다면) pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
관리자 생성(선택): python manage.py createsuperuser

개발 파일: db.sqlite3, media/, staticfiles/는 Git에 올리지 않음(아래 .gitignore 참고)

3) 디렉터리 지도(핵심만)
config/ : Django 설정/URL 루트

mistake_note/ : 메인 앱 (models, views, urls, templates, static)

templates/mistake_note/ : 페이지들 (예: index.html, quiz_*, question_*, dashboard.html 등)

static/mistake_note/{css,js} : 프런트 리소스 (style.css, main.js)

루트: manage.py, README.md, ai_guide.md, (개발) db.sqlite3 등

리포 루트/파일 존재: GitHub에서 확인 가능. 링크: 리포 루트, 가이드 파일.

리포: https://github.com/heinz-walker/my-mistake-note

가이드(이 문서): ai_guide.md

4) 페이지 & 흐름(요약)
메인 index.html: 시작/최근 항목

문제 추가 add_question.html: 문제·지문·선택지·해설·이미지, CSV 업로드, AI 검증 버튼(Gemini)

퀴즈 선택 quiz_select.html: 시험/모드 선택 + 실시간 가능 문제 수

퀴즈 풀이 quiz_take.html: 단건 풀이 → 즉시 정오답/해설 → 마지막에 ‘결과 보기’

결과 요약 quiz_summary.html: 점수 + 틀린 문제 모아보기(오답노트)

대시보드 dashboard.html: 정답률 추이, 취약 카테고리/태그(Chart.js 연결 예정)

템플릿들은 mistake_note/templates/mistake_note/에 있음.

5) 모델/로깅(개념 요약)
실제 필드명은 models.py 기준. 아래는 AI용 해석 가이드.

Question: exam, category, qtype(객관/주관/복수), content, passage, image, choices, answer, explanation, tags

AnswerLog/Attempt: question, (user), is_correct, submitted_answer, submitted_at, elapsed, attempt_count

집계: 정답률, 최근 추세, 카테고리·태그별 취약도(대시보드)

6) 채점 로직(요약)
주관식: 오타 허용(fuzzy 매칭; 임계값은 상수/설정으로 분리 권장)

복수정답: 정규화(트리밍+정렬) 후 비교

객관식: 단일/다중 체크 처리

테스트 예시(개념):

python
코드 복사
def norm_multi(s): return ",".join(sorted(x.strip().lower() for x in s.split(",")))
assert norm_multi("A,B") == norm_multi("B,A")
7) 정적/미디어
정적 소스: mistake_note/static/…

collectstatic 결과: staticfiles/ (Git 제외)

업로드 미디어: media/ (예: media/questions/…)

8) 보안 & 비밀
아래는 절대 커밋 금지: .env, SECRET_KEY, API 키/토큰, db.sqlite3, media/, staticfiles/

과거 커밋에 포함됐으면 즉시 폐기·교체 + 히스토리 정리 권장

권장 .gitignore

bash
코드 복사
.env
db.sqlite3
media/
staticfiles/
__pycache__/
*.pyc
.DS_Store
.idea/
.vscode/
9) 흔한 작업 요청 템플릿(복붙)
AI에게는 다음처럼 요청하면 파일/라인 단위로 패치를 돌려준다.

less
코드 복사
[리포] https://github.com/heinz-walker/my-mistake-note
[작업] (예) validate_question_api에 타임아웃+재시도(429/5xx 백오프) 추가
[제약] 데이터 모델 변경 금지
[출력] 변경 코드블럭 + 적용 파일/라인 + 변경 이유(한 줄) + 간단 테스트 방법
라인 앵커 링크 팁
https://github.com/<owner>/<repo>/blob/<branch>/mistake_note/views.py#L120-L168

10) TODO / Known Issues (체크리스트)
 디자인 통일: base.html 기준 여백/폰트/버튼 사이즈 토큰화(style.css)

 Gemini 검증 안정화: views.py validate_question_api 입력 검증, 타임아웃, 429/5xx 백오프, 응답 JSON 스키마 고정

 대시보드 데이터 파이프: 최근 7/14/30일 정답률, 카테고리/태그 Top-N 오답률 집계 + Chart.js 바인딩

 태그 시스템(admin): admin.py 필드 표시/위젯/에러 해결

 SQLite “database is locked”: 개발 중 동시쓰기 회피, 트랜잭션 범위 축소, 단일 워커 권장

11) 코드 스타일/CI(권장)
pre-commit: black / ruff / isort

pytest/pytest-django: 기본 채점/집계 테스트

GitHub Actions: 린트 + 테스트 워크플로(.github/workflows/ci.yml)

12) 용어(한·영)
오답노트 = mistake note

시험 종류 = exam

카테고리 = category

문제 종류 = qtype (객관/주관/복수)

해설 = explanation

정답률 = accuracy

많이 틀린 문제 = most wrong

안 풀어본 문제 = least attempted

yaml
코드 복사

---

## 적용 방법 (로컬에서 덮어쓰기 → 푸시)

```bash
# 리포 루트에서 (mynote 가상환경일 필요는 없음)
git pull origin HEAD
# 에디터로 열어 새 내용 붙여넣기
code ai_guide.md          # 또는 nano ai_guide.md
git add ai_guide.md
git commit -m "docs: overhaul ai_guide for AI-first workflow"
git push origin HEAD
업데이트가 반영되면, 내가 이 문서를 기준으로 파일/라인 단위 패치 제안을 바로 진행할 수 있어.
다음으로 어떤 이슈(예: Gemini 검증 안정화, 대시보드 데이터 연결)부터 손볼지 말해줘—그 작업을 네 리포 기준으로 바로 해줄게.
