# snap-vocab — Claude Working Guide

## Branch Strategy

Three long-lived branches:

| Branch | Purpose |
|--------|---------|
| `main` | Integration — all feature PRs merge here |
| `release` | Production — Railway deploys from this branch |
| `feat/*`, `fix/*`, etc. | Short-lived feature branches, always cut from `main` |

**Deploy flow:**
```
feat/* → main (PR merge)   ← code integration, no deploy
main → release (PR)        ← intentional release, triggers Railway deploy
```

**Releasing to production:**
1. Tag `main` with the new version
2. Create a GitHub Release from the tag
3. Open a PR from `main` → `release` — always tag first, then open the PR
4. After the release PR merges, immediately open a back merge PR (`release` → `main`) to keep branches in sync

```bash
# Step 1-3: tag and release
git tag -a vX.Y.Z -m "vX.Y.Z — <summary>"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z — <summary>" --notes "..."
gh pr create --base release --title "release: vX.Y.Z"

# Step 4: back merge after release PR is merged
gh pr create --base main --head release --title "chore: back merge release into main post vX.Y.Z"
```

**Why back merge matters:** if `release` diverges from `main` (e.g. due to conflict resolution commits), the next release PR will hit conflicts again. Back merging after every release keeps the two branches in sync.

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

> CI runs **both** `ruff check` (lint) and `ruff format --check` (formatting). Always run both before committing — missing the format step is a common source of CI failure.

```bash
# Check code style
uv run ruff check . --exclude="*.md"

# Check formatting (CI uses --check; omit it to auto-fix)
uv run ruff format --check . --exclude="*.md"

# Auto-fix formatting
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

**Before opening any PR, always sync with the latest `main`:**

```bash
git fetch origin main
git rebase origin/main
```

This prevents merge conflicts on the PR.

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
