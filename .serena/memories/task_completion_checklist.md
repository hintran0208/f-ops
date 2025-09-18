# Task Completion Checklist

When completing any development task in the F-Ops project, ensure you:

## 1. Code Quality Checks
- [ ] Run code formatter: `ruff format backend/ cli/`
- [ ] Run linter: `ruff check backend/ cli/`
- [ ] Fix any linting issues identified
- [ ] Ensure all imports are properly organized

## 2. Testing
- [ ] Run existing tests: `pytest tests/`
- [ ] Add new tests for new functionality
- [ ] Ensure test coverage for critical paths
- [ ] Run E2E tests if applicable: `python tests/test_e2e.py`

## 3. Documentation
- [ ] Update docstrings for new/modified functions
- [ ] Update README.md if adding new features
- [ ] Add inline comments for complex logic
- [ ] Update API documentation if endpoints changed

## 4. Manual Verification
- [ ] Test the feature manually via CLI
- [ ] Verify API endpoints via `/docs` interface
- [ ] Check logs for any errors or warnings
- [ ] Ensure backward compatibility

## 5. Environment & Configuration
- [ ] Update .env.example if new env vars added
- [ ] Update requirements.txt if new dependencies added
- [ ] Update docker-compose.yml if services changed
- [ ] Ensure all secrets are properly managed

## 6. Before Committing
- [ ] Review all changes: `git diff`
- [ ] Ensure no sensitive data in commits
- [ ] Write clear commit message following convention:
  - feat: new feature
  - fix: bug fix
  - docs: documentation
  - refactor: code refactoring
  - test: testing
  - chore: maintenance

## 7. Performance & Security
- [ ] Check for performance bottlenecks
- [ ] Ensure no SQL injection vulnerabilities
- [ ] Validate all user inputs
- [ ] Check for proper error handling
- [ ] Ensure audit logging for critical operations

## Quick Command Summary
```bash
# Essential checks before marking task complete
ruff format backend/ cli/
ruff check backend/ cli/
pytest tests/
git status
git diff
```

## Notes
- The project uses ruff for formatting and linting (black, flake8, mypy not configured)
- pytest is available for testing
- Focus on FastAPI best practices for backend code
- Ensure CLI commands follow Typer patterns