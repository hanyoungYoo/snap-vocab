## Description

<!-- Describe your changes here -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Infrastructure / DevOps
- [ ] Other (please describe)

## Related Issue

<!-- If this PR fixes an issue, link it here -->
Closes #(issue number)

## Testing

<!-- Describe how you tested your changes -->

- [ ] Tested locally with `uv run pytest`
- [ ] Manual testing (describe below)
- [ ] No test changes needed

## Checklist

**Automated checks** (GitHub Actions will verify these):
- ✅ No secrets (API keys, tokens, credentials)
- ✅ Code style (`ruff` compliant)
- ✅ No `.gitignore` violations

**Manual verification:**

- [ ] Changes do not break existing functionality
- [ ] New environment variables are documented in `.env.example`
- [ ] Database schema changes include migration SQL files
- [ ] Commit messages are clear and descriptive
- [ ] Code follows the project style guide (Python/JavaScript/SQL)

## Additional Context

<!-- Add any other context about the PR here -->
