## TDD Workflow

Follow strict Test-Driven Development for all feature work:

1. **Write tests first** — before writing any production code, write the tests that describe the expected behavior.
2. **Run tests and see them fail** — execute the tests and confirm they fail for the right reasons (e.g. missing module, 404, assertion error). Do not skip this step.
3. **Write the minimal production code** to make the failing tests pass.
4. **Run tests again** and confirm they pass.
5. **Refactor** if needed, re-running tests after each change.

This applies to both backend (pytest) and frontend (vitest) work. Never write implementation code before its corresponding tests exist and have been observed to fail.

## CI Verification

After any significant change (new features, refactors, dependency updates, config changes), run all CI stages locally before considering the work complete:

1. **Backend**: `cd backend && ruff check . && ruff format --check . && pytest -v`
2. **Frontend**: `cd frontend && npm run lint && npm run format:check && npm test && npm run build`
3. **Docker**: `docker compose build`

Fix any failures before moving on.

## Implementation Plan

When implementing phases from `docs/plans/health-studio-implementation-plan.md`, always run the full CI pipeline after completing each phase. Do not consider a phase done until all CI stages pass.
