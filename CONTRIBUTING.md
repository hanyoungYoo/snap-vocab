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

## Automated Checks (CI/CD)

**Every PR is automatically checked by GitHub Actions. Failing checks block merge:**

| Check | Command | Blocks Merge? | What It Does |
|-------|---------|---------------|-------------|
| 🔐 Secrets Detection | `git diff` + regex patterns | ✅ **YES** | Detects API keys, tokens, credentials (`sk-`, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, etc.) |
| 📋 Gitignore Violations | `git diff --name-only` | ✅ **YES** | Prevents `.env*`, `AGENTS.md`, `PROGRESS.md`, `docs/steps/`, `.claude/` from being committed |
| 🐍 Python Linting | `ruff check .` | ✅ **YES** | Enforces style: imports, naming, syntax (line length: 100) |
| 🎨 Python Formatting | `ruff format --check .` | ✅ **YES** | Enforces consistent code formatting |
| ✅ Import Validation | `python -c "import api.main; import api.db; import api.deps"` | ✅ **YES** | Ensures critical modules can be imported |
| 🚫 JavaScript Style | Check for `var` usage | ✅ **YES** | Enforces `const`/`let` instead of `var` |
| 🌐 English-Only Code | Detect Korean characters in diffs | ✅ **YES** | Code must be in English (exception: local dev files) |

**You cannot merge a PR if any automated check fails.** See `.github/workflows/` for details.

## Pre-PR Checklist (Local)

Before pushing, run these locally to catch issues early:

```bash
# Check code style
uv run ruff check .

# Check formatting
uv run ruff format --check .

# Run tests
uv run pytest

# (Optional) Simulate secrets detection
git diff origin/main HEAD | grep -iE "sk-[A-Za-z0-9]{20,}|ANTHROPIC_API_KEY|TELEGRAM_BOT_TOKEN" && echo "❌ Secrets found!" || echo "✅ No secrets"
```

## Manual Verification (Before Submitting)

Even though CI catches most issues, double-check these:

- [ ] No `.env`, `.env.*` files committed (should be in `.gitignore`)
- [ ] No API keys, tokens, or credentials in code (use `.env` instead)
- [ ] Updated `.env.example` if adding new environment variables?
- [ ] Added SQL migration files in `migrations/` for schema changes?
- [ ] Commit messages are clear and descriptive
- [ ] If modifying a STEP, updated `PROGRESS.md` status accordingly

## Code Style

- **Python**: Follow `ruff` rules (line length: 100)
- **JavaScript**: Use 2-space indentation, prefer `const`/`let` over `var`
- **SQL**: Uppercase keywords (`SELECT`, `FROM`, `WHERE`)
- **Commit Messages**: Clear and concise
  - ✅ `STEP 01: Add async DB pool initialization`
  - ❌ `fix stuff` / `wip`

## Project Structure

### Public Files (In Repository)

```
snap-vocab/
├── README.md                           # Quick start guide
├── CONTRIBUTING.md                     # This file
├── LICENSE                             # Project license
├── pyproject.toml                      # Python dependencies (uv)
├── .python-version                     # Python 3.13
├── .gitignore                          # Excludes secrets, .env, local files
├── docker-compose.yml                  # Local DB (PostgreSQL)
├── .github/
│   ├── workflows/
│   │   ├── lint.yml                   # Ruff, imports, JS style, English-only checks
│   │   └── secrets-check.yml          # API key detection, .gitignore validation
│   └── pull_request_template.md        # Auto-populated PR description
├── api/                                # FastAPI endpoints, DB access
├── bot/                                # Telegram handlers, SRS logic
├── llm/                                # LLM provider adapters (Claude, OpenAI, etc.)
├── notification/                       # Notification adapters (Telegram, Slack, etc.)
├── prompts/                            # System prompts (constants, no logic)
├── migrations/                         # SQL DDL files (numbered sequentially)
└── extension/                          # Chrome extension (manifest v3)
    ├── manifest.json
    ├── content.js
    ├── popup.html
    └── background.js
```

### Local Files (NOT in Repository - .gitignore)

These files are **excluded from git** for security and development isolation:

```
snap-vocab/
├── .env                                # Environment secrets (❌ NEVER commit)
├── .env.*                              # Variant configs (❌ NEVER commit)
├── AGENTS.md                           # AI assistant guidelines (local only)
├── PROGRESS.md                         # Step progress tracker (local only)
├── docs/steps/                         # Step-by-step guides (local only)
│   ├── README.md
│   ├── 00-initial-setup.md
│   ├── 01-db-and-api.md
│   ├── ...
│   └── 07-deploy.md
├── .venv/                              # Python virtual environment
├── .ruff_cache/                        # Ruff cache
├── extension/dist/                     # Built extension
├── extension/node_modules/             # Node dependencies
├── .claude/                            # Claude Code internals (plans, memory, worktrees)
└── .railway/                           # Railway config
```

### Documentation

The project is organized in **steps**:

- **[영어_학습_프로그램_종합_문서.md](영어_학습_프로그램_종합_문서.md)** — Complete design (Korean, ~970 lines)
- **[PROGRESS.md](PROGRESS.md)** — Step progress tracker (local only)
- **[AGENTS.md](AGENTS.md)** — Guidelines for AI assistants (local only)
- **[docs/steps/](docs/steps/)** — Step-by-step implementation guides (local only, Korean)
  - Each STEP is independent: contains goal, scope, work items, validation criteria

**For detailed implementation guides, see `PROGRESS.md` and `docs/steps/` (local files).**

## Reporting Issues

- **Bug Reports**: Include reproduction steps, expected vs actual behavior, and environment details
- **Feature Requests**: Explain the use case and implementation considerations

## License

This project is licensed under [LICENSE](LICENSE).

---

Questions? Open an [Issue](https://github.com/hanyoungYoo/snap-vocab/issues) on GitHub.
