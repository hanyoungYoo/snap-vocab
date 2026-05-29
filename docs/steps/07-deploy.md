# STEP 07: Railway 배포

> **Status**: todo
> **Depends on**: STEP 05, STEP 06
> **Last updated**: 2026-05-25

## 목표

snap-vocab 을 Railway에 배포해, Chrome 확장에서 캡처한 카드가 운영 DB에 저장되고 매일 정해진 시간에 텔레그램으로 복습 알림이 도착하도록 만든다.

## 범위 (In Scope)

- `Dockerfile` (api + bot + scheduler 단일 컨테이너)
- Railway 프로젝트 + PostgreSQL 플러그인 생성
- 환경변수 등록
- GitHub 레포 연결, 자동 배포
- Telegram `setWebhook` 을 Railway URL 로 갱신
- Chrome 확장의 `apiUrl` 을 Railway URL 로 변경
- 운영 환경 헬스체크 + 첫 캡처 + 다음날 복습 알림 확인

## 범위 밖 (Out of Scope)

- 다중 인스턴스 / 오토스케일 (1인용)
- CI/CD 강화 (Railway 자동 배포로 충분)
- 모니터링 / 로깅 인프라
- 도메인/HTTPS 커스텀 (Railway 기본 도메인 사용)

## 사전 결정 사항

- **단일 컨테이너 / 단일 서비스**: API + webhook + scheduler 모두 하나의 FastAPI 프로세스. Railway service 도 하나 + Postgres 플러그인.
- **스케줄러 중복 발송 방지**: replicas = 1 유지. 종합 문서의 "Service 1/2/3" 분리는 본 프로젝트에선 불필요.
- **HEALTHCHECK**: `GET /` 사용. Railway healthcheck 설정.
- **마이그레이션**: Railway 배포 후 일회성으로 `railway run psql … < migrations/*.sql` 수동 실행. (자동화 필요해지면 startup script로 옮김.)

## 작업 항목

- [ ] `Dockerfile` 작성
- [ ] `docker-compose.yml` 에 `api` 서비스 추가 (로컬에서 Dockerfile 테스트)
- [ ] 로컬에서 `docker compose up --build` 로 검증
- [ ] Railway 계정 / 프로젝트 생성
- [ ] PostgreSQL 플러그인 추가 → `DATABASE_URL` 자동 주입 확인
- [ ] GitHub 레포 연결, 자동 배포 활성화
- [ ] Railway Variables 에 모든 env 등록 (LLM_API_KEY 등)
- [ ] 첫 배포 → 헬스체크 통과 확인
- [ ] `railway run psql $DATABASE_URL -f migrations/001_cards.sql` (002, 003도)
- [ ] `setWebhook` 호출로 Railway URL 등록
- [ ] Chrome 확장 popup 에서 apiUrl 을 Railway URL 로 변경
- [ ] 확장에서 캡처 → DB 저장 확인
- [ ] DB에 테스트 카드의 next_review를 오늘로 → 트리거(또는 시간 변경) → 텔레그램 도착 확인
- [ ] 정상 시간(REVIEW_TIME) 까지 기다려 자동 발송 확인 (선택)
- [ ] PROGRESS.md 갱신 (✅)

## 핵심 파일

### `Dockerfile`

```dockerfile
FROM python:3.13-slim

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 의존성 먼저 (캐시 활용)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 앱 코드
COPY . .
RUN uv sync --frozen --no-dev

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uv run uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
```

### `docker-compose.yml` (api 추가)

```yaml
services:
  api:
    build: .
    env_file: .env
    ports: ["8000:8000"]
    depends_on: [db]

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: snap_vocab
      POSTGRES_USER: snap
      POSTGRES_PASSWORD: snap
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

volumes:
  postgres_data:
```

### Railway 환경변수 체크리스트

| 키 | 비고 |
|---|---|
| `DATABASE_URL` | Postgres 플러그인이 자동 주입 |
| `API_SECRET_KEY` | 강한 랜덤 문자열 (확장과 공유) |
| `LLM_PROVIDER` | `claude` |
| `LLM_API_KEY` | Anthropic API 키 |
| `EXTRACT_MODEL` | `claude-haiku-4-5-20251001` |
| `REVIEW_MODEL` | `claude-sonnet-4-6` |
| `NOTIFICATION_PROVIDER` | `telegram` |
| `TELEGRAM_BOT_TOKEN` | BotFather 토큰 |
| `TELEGRAM_CHAT_ID` | 본인 chat_id |
| `TELEGRAM_WEBHOOK_SECRET` | 랜덤 문자열 |
| `REVIEW_TIME` | `21:00` |
| `REVIEW_MAX_CARDS` | `5` |

### Telegram setWebhook

```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://<railway-domain>/api/webhook/telegram" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"

# 등록 확인
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

### 마이그레이션 적용 (Railway)

```bash
railway run psql "$DATABASE_URL" -f migrations/001_cards.sql
railway run psql "$DATABASE_URL" -f migrations/002_review_logs.sql
railway run psql "$DATABASE_URL" -f migrations/003_pending_reviews.sql
```

## 참고 (종합 문서 발췌)

- [영어_학습_프로그램_종합_문서.md](../../영어_학습_프로그램_종합_문서.md) §배포 §Railway 배포 — Railway 셋업/Webhook 등록

## 검증

1. 로컬: `docker compose up --build` → `curl http://localhost:8000/` → `{"status":"ok"}`
2. Railway 배포 성공, `curl https://<domain>/` 응답 OK
3. `getWebhookInfo` 가 등록된 URL을 표시, `last_error_message` 없음
4. Chrome 확장 popup에서 apiUrl 변경 → 실 페이지에서 캡처 → 저장 성공
5. Railway DB 에 카드 행 존재 확인 (`railway run psql $DATABASE_URL -c 'SELECT count(*) FROM cards;'`)
6. 텔레그램에서 `/ping` → `pong`
7. `next_review` 조작 후 `POST /api/admin/trigger-review` → 텔레그램 문제 도착
8. (선택) 다음 `REVIEW_TIME` (KST) 까지 대기 → 자동 발송 확인

8개 모두 통과 시 MVP 운영 완료.

## 메모

- Railway 무료 티어는 슬립이 있을 수 있음 — APScheduler는 프로세스가 깨어 있어야 동작. 활성화 유지 필요(소액 결제 또는 외부 ping).
- 비용 모니터링: Anthropic API 사용량이 가장 큼. 추출은 Haiku로 묶어두고, 매일 출제 카드 수(`REVIEW_MAX_CARDS`)를 조절해 비용 통제.
- 향후 추가할 것: 백업 스크립트 (`pg_dump`), 로그 적재(Postgres `review_logs` 외에 운영 로그), 알림 실패 재시도.
