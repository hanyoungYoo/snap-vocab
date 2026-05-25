# Contributing

Thank you for your interest in contributing to snap-vocab!

## Getting Started

```bash
# Clone the repository
git clone https://github.com/hanyoungYoo/snap-vocab
cd snap-vocab

# Install dependencies
uv sync

# Setup environment variables
cp .env.example .env
# Edit .env and fill in required API keys and secrets (local development only)

# Start the database
docker-compose up -d db

# Apply database migrations (first time only)
psql "$DATABASE_URL" -f migrations/001_cards.sql
psql "$DATABASE_URL" -f migrations/002_review_logs.sql
psql "$DATABASE_URL" -f migrations/003_pending_reviews.sql

# Run the development server
uv run uvicorn api.main:app --reload
```

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests and linters locally (or let CI do it)
4. Push and open a Pull Request

## Pull Request Checklist

The following checks are **automated** by GitHub Actions:

- ✅ **Secrets Detection** — API keys, tokens, credentials are automatically detected and blocked
- ✅ **Code Style** — `ruff` checks for Python code style
- ✅ **Gitignore Violations** — `.env` and other local files are checked

**Manual checks (before submitting):**

- [ ] Added or modified `.env*` files by accident? (They should be in `.gitignore`)
- [ ] Hardcoded secrets in code? (Use environment variables instead)
- [ ] Updated `.env.example` if adding new environment variables?
- [ ] Added migrations to `migrations/` for schema changes?
- [ ] Commit messages are clear and descriptive?

## Code Style

- **Python**: Follow `ruff` rules (line length: 100)
- **JavaScript**: Use 2-space indentation, prefer `const`/`let` over `var`
- **SQL**: Uppercase keywords (`SELECT`, `FROM`, `WHERE`)
- **Commit Messages**: Clear and concise
  - ✅ `STEP 01: Add async DB pool initialization`
  - ❌ `fix stuff` / `wip`

## Project Structure

This project uses a **step-based development approach**:

- `영어_학습_프로그램_종합_문서.md` — Complete project design (Korean)
- `STEP NN: ...` files in docs/steps/ — Implementation guides (Korean, local only)
- GitHub Actions — Automated CI/CD checks

For detailed implementation guides, see the project documentation (Korean).

## Reporting Issues

- **Bug Reports**: Include reproduction steps, expected vs actual behavior, and environment details
- **Feature Requests**: Explain the use case and implementation considerations

## License

This project is licensed under [LICENSE](LICENSE).

---

Questions? Open an [Issue](https://github.com/hanyoungYoo/snap-vocab/issues) on GitHub.
