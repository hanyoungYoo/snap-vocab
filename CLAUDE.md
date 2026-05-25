# snap-vocab — Claude Working Guide

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
