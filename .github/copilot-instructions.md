## Data Safety

Before executing any command or action that may cause data loss — including but not limited to `docker compose down -v`, `docker volume rm`, `rm -rf` on data directories, database drops/resets, or any operation that could destroy Docker volumes, databases, or user-entered data — you MUST:

1. **Stop** — do not execute the command.
2. **Explain** — clearly describe what the command will do and what data is at risk.
3. **Ask permission** — wait for explicit approval before proceeding.

This applies even if the data loss is a side effect rather than the primary intent. When in doubt, assume data is at risk and ask.

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

## Health Data Questions & Analysis

When the user asks questions about their health data, wants analysis or insights, or asks you to interact with their Health Studio application data, **always** read the skill file at `.github/skills/health-studio-cli/SKILL.md` and use the `hs` CLI to query the running application. Do not guess or fabricate data — use the CLI commands to retrieve real data, then analyze and respond based on actual results.

This applies to any question about: metrics, goals, exercise results, personal records, trends, journal entries, progress, dashboard summaries, or any request for health-related insights and analysis.

## Implementation Plan

When implementing phases from `docs/plans/health-studio-implementation-plan.md`, always run the full CI pipeline after completing each phase. Do not consider a phase done until all CI stages pass.
