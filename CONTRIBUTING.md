# 기여 가이드

snap-vocab 에 기여해주신다면 감사합니다!

## 시작하기

```bash
# 1. 레포 클론
git clone https://github.com/user/snap-vocab
cd snap-vocab

# 2. 의존성 설치
uv sync

# 3. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 등을 채워주세요 (로컬 개발용)

# 4. DB 띄우기
docker-compose up -d db

# 5. 마이그레이션 적용 (처음 한 번)
psql "$DATABASE_URL" -f migrations/001_cards.sql
psql "$DATABASE_URL" -f migrations/002_review_logs.sql
psql "$DATABASE_URL" -f migrations/003_pending_reviews.sql

# 6. 서버 실행
uv run uvicorn api.main:app --reload
```

## 개발 워크플로

### 새 기능 추가

1. **브랜치 생성** — `git checkout -b feature/your-feature-name`
2. **작업** — 관련 STEP 문서 읽고 진행
3. **테스트** — `uv run pytest` + 수동 테스트
4. **코드 스타일** — `uv run ruff check .` 통과
5. **커밋** — 명확한 커밋 메시지
6. **PR** — **아래 체크리스트 필독**

### 버그 수정

같은 흐름. 버그 리포트 링크가 있으면 PR 본문에 포함.

## PR 전 필수 체크리스트

**⚠️ 시크릿 유출 방지 (매우 중요)**

- [ ] `.env` 파일이 커밋되지 않았는가? (`.gitignore` 확인)
- [ ] API 키, 토큰, 패스워드가 코드에 하드코딩되지 않았는가?
  - 예: `ANTHROPIC_API_KEY=sk-...` ❌
  - 대신: `settings.llm_api_key` (환경변수에서만 로드) ✅
- [ ] 로그 출력에 민감정보가 있는가? 제거할 것.
- [ ] 테스트 파일에 테스트용 시크릿이 평문으로 있는가? 환경변수로 옮길 것.

**✅ 코드 품질**

- [ ] `uv run ruff check .` 통과했는가?
- [ ] `uv run pytest` 통과했는가? (있으면)
- [ ] 새 의존성을 추가했다면 `pyproject.toml` 과 `uv.lock` 둘 다 커밋했는가?
- [ ] 새 환경변수를 추가했다면 `.env.example` 도 갱신했는가?
- [ ] DB 스키마를 변경했다면 `migrations/` 에 SQL 파일 추가했는가?

**📝 문서**

- [ ] 주요 변경은 해당 STEP 파일(`docs/steps/NN-*.md`)의 "메모" 섹션에 반영했는가?
- [ ] 새 환경변수/설정이 있으면 `README.md` 나 STEP 파일에 기록했는가?
- [ ] 사용자 입장에서 사용법이 명확한가?

**🧪 테스트**

- [ ] 로컬에서 정상 동작하는가?
- [ ] 엣지 케이스를 생각해봤는가?
  - 빈 입력
  - 매우 긴 입력 (10,000자)
  - 다국어
  - 특수문자

**🔐 보안**

- [ ] 사용자 입력을 검증했는가? (길이, 타입)
- [ ] SQL injection 위험이 있는가? (raw query 쓸 때)
- [ ] API 인증은 제대로 되어있는가?
- [ ] 민감 작업(`DELETE`, `UPDATE`)에 확인 단계가 있는가?

## 코드 스타일

- **Python**: `ruff` 규칙 준수 (라인길이 100)
- **JavaScript**: 기본 들여쓰기 2칸, `var` 쓰지 말 것 (`let`/`const`)
- **SQL**: 예약어 대문자 (`SELECT`, `FROM`)
- **커밋 메시지**: 명확하고 간결하게
  - ✅ `STEP 01: Add async DB pool initialization`
  - ❌ `fix stuff` / `wip` / `asdfgh`

## 어디서부터 시작할까?

1. [영어_학습_프로그램_종합_문서.md](영어_학습_프로그램_종합_문서.md) — 전체 설계
2. [PROGRESS.md](PROGRESS.md) — 진행 상황 확인
3. 관심 있는 STEP 파일 (`docs/steps/NN-*.md`) — 상세 가이드

## 문제 제보

GitHub Issues로 버그/기능 제안을 올려주세요.

- **버그**: 재현 방법, 예상 vs 실제 동작, 환경(Python 버전 등)
- **기능 제안**: 배경, 사용 시나리오, 구현 난이도 추정

## 라이선스

이 프로젝트는 [LICENSE](LICENSE) 에 따라 배포됩니다.

---

질문이 있으면 Issues 를 열거나 토론을 시작하세요!
