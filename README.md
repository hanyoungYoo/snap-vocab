# snap-vocab

> LLM과 대화하다 막히는 순간을 자동으로 학습 카드로 만들고, 텔레그램으로 복습 문제를 보내주는 셀프호스팅 영어 학습 도구.

## 빠른 시작 (로컬)

```bash
# 1. Python 3.13 + uv 설치 (없으면)
brew install uv  # 또는 https://docs.astral.sh/uv/

# 2. 의존성 설치
uv sync

# 3. 환경변수 설정
cp .env.example .env
# .env 파일 열어서 API_SECRET_KEY, LLM_API_KEY 등 채우기

# 4. DB 띄우기
docker-compose up -d db

# 5. (다음 스텝부터) 마이그레이션 적용 + 서버 실행
# uv run psql $DATABASE_URL -f migrations/001_*.sql
# uv run uvicorn api.main:app --reload
```

## 문서

- 전체 설계: [영어_학습_프로그램_종합_문서.md](영어_학습_프로그램_종합_문서.md)
- 진행 상황: [PROGRESS.md](PROGRESS.md)
- 작업 가이드 (AI용): [AGENTS.md](AGENTS.md)
- 스텝별 문서: [docs/steps/](docs/steps/)
- 기여 방법: [CONTRIBUTING.md](CONTRIBUTING.md)

## 라이선스

[LICENSE](LICENSE)