## CI Verification

After any significant change (new features, refactors, dependency updates, config changes), run all CI stages locally before considering the work complete:

1. **Backend**: `cd backend && ruff check . && ruff format --check . && pytest -v`
2. **Frontend**: `cd frontend && npm run lint && npm run format:check && npm test && npm run build`
3. **Docker**: `docker compose build`

Fix any failures before moving on.

## Implementation Plan

When implementing phases from `docs/plans/health-studio-implementation-plan.md`, always run the full CI pipeline after completing each phase. Do not consider a phase done until all CI stages pass.
