# snap-vocab — Claude Working Guide

## Starting Work

**Always sync with main before starting any task.** This prevents merge conflicts.

```bash
git checkout main
git pull origin main
git checkout -b <type>/<short-description>
```

Never branch off a stale or non-main branch. If already in a worktree, ensure the worktree base is up to date with `git fetch origin main && git rebase origin/main` before making changes.

## Linting & Code Quality

**Ruff Configuration:**
- Excludes markdown files (`.md`) from linting
- Line length: 100 characters
- Python version: 3.13
- Enabled rules: E (style), F (errors), I (imports), UP (upgrades), B (bugbear)

**Running Checks Locally:**
```bash
# Check code style
uv run ruff check . --exclude="*.md"

# Format code
uv run ruff format . --exclude="*.md"

# Type checking
uv run python -c "import api.main; import api.db; import api.deps"

# Run tests
uv run pytest tests/ -v
```

All checks must pass before opening a PR. The GitHub Actions workflow runs these automatically on every PR.

## PR Rules

### Title Format

```
<type>(<scope>): <summary>
```

**type** (lowercase):
- `feat` — new feature
- `fix` — bug fix
- `refactor` — code improvement with no behavior change
- `docs` — documentation only
- `test` — tests only
- `chore` — build, dependencies, or config changes

**scope** (optional): area of change — `api`, `db`, `ui`, `auth`, `migration`, etc.

**summary**: imperative, present tense, under 50 chars, no trailing period

Examples:
- `feat(api): Add vocabulary card search endpoint`
- `fix(db): Resolve connection pool timeout on idle`
- `refactor(ui): Simplify quiz result rendering`
- `docs: Update STEP 03 with new env variables`

### Creating a PR

Always follow this order when creating a PR:

1. Use `gh pr create`
2. Follow the title format above
3. Body must include the `.github/pull_request_template.md` checklist
4. **Always run `/review` skill after creating the PR** to perform a Claude code review

### Branch Naming

```
<type>/<short-description>
```

Examples: `feat/card-search`, `fix/pool-timeout`, `docs/step03-env`
