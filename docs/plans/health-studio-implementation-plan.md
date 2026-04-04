# Health Studio — Implementation Plan

## Overview

Health Studio is a local-first personal health dashboard, journal, and tracker. It consolidates mental and physical health management into a single, self-hosted web application deployed via Docker. All data lives locally on the host machine.

**Single-user application.** Health Studio is designed for one person. There is no multi-user or multi-tenant support. Authentication exists solely to protect the local instance from unauthorized access — not to distinguish between users. This simplifies the data model (no `user_id` foreign keys) and the auth flow (one registered passkey owner).

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React + TypeScript + Vite | Modern, fast build tooling; strong typing for maintainability |
| **UI Framework** | Tailwind CSS | Utility-first CSS for rapid, consistent styling; easy dark mode support |
| **Markdown Editing** | `react-markdown` + `@uiw/react-md-editor` | Rich Markdown authoring for journals and goal plans |
| **Visualization** | Plotly.js (`react-plotly.js`) | Interactive, publication-quality charts for trends and metrics |
| **Backend** | Python + FastAPI | Lightweight, async-ready, auto-generated OpenAPI docs; clean REST API |
| **Database** | SQLite (via SQLAlchemy) | Zero-config local persistence; efficient structured queries |
| **Authentication** | WebAuthn / Passkeys (`py_webauthn`) | Modern passwordless auth per requirements |
| **API Keys** | Scoped bearer tokens (stored hashed in SQLite) | Programmatic API access for scripts and CLI |
| **Testing** | pytest (backend), Vitest + React Testing Library (frontend) | TDD-first workflow |
| **Linting** | Ruff (backend), ESLint + Prettier (frontend) | Consistent code style, CI-enforceable |
| **Containerization** | Docker + Docker Compose | Single `docker compose up` to run the full stack locally |
| **CI** | GitHub Actions | Automated lint, test, and build checks on every push/PR |
| **CLI** | Python + Typer + `httpx` | Rich terminal UI; async HTTP client for API calls; installable as a standalone executable via `pipx` or shell wrapper |

---

## Project Structure

```
health-studio/
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── README.md
├── docs/
│   └── index.html
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── journal.py
│   │   │   ├── metric.py
│   │   │   ├── result.py
│   │   │   ├── goal.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── journal.py
│   │   │   ├── metric.py
│   │   │   ├── result.py
│   │   │   └── goal.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── journals.py
│   │   │   ├── metrics.py
│   │   │   ├── results.py
│   │   │   ├── goals.py
│   │   │   └── api_keys.py
│   │   └── services/
│   │       ├── auth.py
│   │       ├── journal.py
│   │       ├── metric.py
│   │       ├── result.py
│   │       └── goal.py
│   └── tests/
│       ├── conftest.py
│       ├── test_journals.py
│       ├── test_metrics.py
│       ├── test_results.py
│       ├── test_goals.py
│       └── test_auth.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   │   └── logo.png
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── DarkModeToggle.tsx
│   │   │   ├── MarkdownEditor.tsx
│   │   │   └── PlotlyChart.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Journal.tsx
│   │   │   ├── Metrics.tsx
│   │   │   ├── Results.tsx
│   │   │   ├── Goals.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   └── tests/
│       ├── setup.ts
│       ├── Dashboard.test.tsx
│       ├── Journal.test.tsx
│       ├── Metrics.test.tsx
│       ├── Results.test.tsx
│       └── Goals.test.tsx
└── assets/
    └── logo.svg          # Source logo (transparent PNG exported from this)
├── cli/
│   ├── pyproject.toml        # Standalone package: health-studio-cli
│   ├── health_studio_cli/
│   │   ├── __init__.py
│   │   ├── __main__.py       # python -m health_studio_cli
│   │   ├── main.py           # Typer app, ASCII art banner
│   │   ├── config.py         # ~/.health-studio/config.toml reader/writer
│   │   ├── api.py            # httpx client wrapper (base URL + API key from config)
│   │   ├── commands/
│   │   │   ├── journal.py
│   │   │   ├── metrics.py
│   │   │   ├── results.py
│   │   │   ├── goals.py
│   │   │   └── config_cmd.py  # `hs config` — init/edit config file
│   │   └── display.py        # Rich tables, formatters, ASCII art
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_journal.py
│   │   ├── test_metrics.py
│   │   ├── test_results.py
│   │   ├── test_goals.py
│   │   └── test_config.py
│   └── scripts/
│       ├── install.sh         # macOS/Linux install script
│       └── install.ps1        # Windows PowerShell install script
```

---

## Data Model (SQLite)

### `users` (single row)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key, always `1` |
| display_name | TEXT | |
| credential_id | BLOB | WebAuthn credential |
| public_key | BLOB | WebAuthn public key |
| sign_count | INTEGER | Replay protection |
| created_at | DATETIME | |

> Only one row will ever exist. Registration is disabled once a user is registered.

### `api_keys`
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| name | TEXT | Label for the key |
| key_hash | TEXT | bcrypt hash of the key |
| prefix | TEXT | First 8 chars for identification |
| created_at | DATETIME | |
| last_used_at | DATETIME | Nullable |
| revoked | BOOLEAN | Soft-delete |

### `journal_entries`
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| title | TEXT | |
| content | TEXT | Markdown body |
| entry_date | DATE | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### `metric_types`
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| name | TEXT | e.g., "Weight", "Waist Circumference" |
| unit | TEXT | e.g., "lbs", "inches", "steps" |
| created_at | DATETIME | |

### `metric_entries`
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| metric_type_id | TEXT (FK) | |
| value | REAL | |
| recorded_date | DATE | |
| notes | TEXT | Optional Markdown |
| created_at | DATETIME | |

### `exercise_types`
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| name | TEXT | e.g., "Back Squat", "Fran", "5K Run" |
| category | TEXT | "olympic_lift", "power_lift", "crossfit_benchmark", "running", "custom" |
| result_unit | TEXT | "lbs", "seconds", "time" |
| created_at | DATETIME | |

### `result_entries`
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| exercise_type_id | TEXT (FK) | |
| value | REAL | Weight in lbs, or time in seconds |
| display_value | TEXT | Formatted for display (e.g., "5:23") |
| recorded_date | DATE | |
| is_pr | BOOLEAN | Flagged automatically or manually |
| notes | TEXT | Optional Markdown |
| created_at | DATETIME | |

### `goals`
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| title | TEXT | |
| description | TEXT | Markdown |
| plan | TEXT | Markdown write-up of the plan |
| target_type | TEXT | "metric" or "result" |
| target_id | TEXT | FK to metric_type or exercise_type |
| target_value | REAL | Target number |
| current_value | REAL | Computed or cached |
| status | TEXT | "active", "completed", "abandoned" |
| deadline | DATE | Nullable |
| created_at | DATETIME | |
| updated_at | DATETIME | |

---

## REST API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Begin passkey registration |
| POST | `/api/auth/register/complete` | Complete passkey registration |
| POST | `/api/auth/login` | Begin passkey authentication |
| POST | `/api/auth/login/complete` | Complete passkey authentication |
| POST | `/api/auth/logout` | Invalidate session |

### API Keys
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/keys` | List API keys (metadata only) |
| POST | `/api/keys` | Create new API key (returns raw key once) |
| DELETE | `/api/keys/{id}` | Revoke an API key |

### Journal
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/journals` | List entries (paginated, filterable by date range) |
| GET | `/api/journals/{id}` | Get single entry |
| POST | `/api/journals` | Create entry |
| PUT | `/api/journals/{id}` | Update entry |
| DELETE | `/api/journals/{id}` | Delete entry |

### Metrics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metric-types` | List metric types |
| POST | `/api/metric-types` | Create new metric type |
| PUT | `/api/metric-types/{id}` | Update metric type |
| DELETE | `/api/metric-types/{id}` | Delete metric type |
| GET | `/api/metrics` | List metric entries (filterable by type, date range) |
| GET | `/api/metrics/{id}` | Get single entry |
| POST | `/api/metrics` | Log a metric entry |
| PUT | `/api/metrics/{id}` | Update entry |
| DELETE | `/api/metrics/{id}` | Delete entry |
| GET | `/api/metrics/trends/{type_id}` | Get trend data for charting |

### Results
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/exercise-types` | List exercise types |
| POST | `/api/exercise-types` | Create new exercise type |
| PUT | `/api/exercise-types/{id}` | Update exercise type |
| DELETE | `/api/exercise-types/{id}` | Delete exercise type |
| GET | `/api/results` | List result entries (filterable by exercise, date range) |
| GET | `/api/results/{id}` | Get single entry |
| POST | `/api/results` | Log a result |
| PUT | `/api/results/{id}` | Update entry |
| DELETE | `/api/results/{id}` | Delete entry |
| GET | `/api/results/prs/{exercise_type_id}` | Get PR history for an exercise |
| GET | `/api/results/trends/{exercise_type_id}` | Get trend data for charting |

### Goals
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/goals` | List goals (filterable by status) |
| GET | `/api/goals/{id}` | Get single goal with progress |
| POST | `/api/goals` | Create goal |
| PUT | `/api/goals/{id}` | Update goal |
| DELETE | `/api/goals/{id}` | Delete goal |

### Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard/summary` | Aggregated overview (recent entries, active goals, latest metrics) |

---

## Seed Data

On first run (or via a seed command), populate the following defaults so the app is immediately useful:

### Default Metric Types
- Weight (lbs)
- Waist Circumference (inches)
- Steps (count)
- Sleep Duration (hours)
- Water Intake (oz)

### Default Exercise Types

**Olympic Lifts**: Snatch, Clean & Jerk, Push Press, Push Jerk, Split Jerk

**Power Lifts**: Back Squat, Front Squat, Deadlift, Bench Press, Overhead Press

**CrossFit Benchmarks**: Fran, Grace, Murph, Helen, Diane, Elizabeth, Jackie, Karen, Cindy, Annie, Fight Gone Bad, Filthy Fifty, DT, Isabel, Amanda

**Running Distances**: 400m, 800m, 1 Mile, 5K, 10K, Half Marathon, Marathon

---

## UX & Design Spec

- **Color palette**: Primary blue (#3B82F6), accent teal (#14B8A6), secondary purple (#8B5CF6); dark backgrounds (#0F172A, #1E293B); light text (#F1F5F9)
- **Typography**: Inter (headings + body) — clean sans-serif available via Google Fonts
- **Dark mode**: Default on; toggleable via header control; preference persisted in `localStorage`
- **Logo**: Transparent PNG, displayed in the header and used as `favicon.ico`; the logo should evoke health/vitality (heart rate line motif or similar)
- **Layout**: Fixed sidebar navigation (collapsible on mobile); main content area with max-width constraint for readability
- **Charts**: Plotly dark theme matching the app palette; hover tooltips; date-range selectors

---

## Development Phases

Each phase is scoped to be implementable in a single LLM session and results in a commit-ready, working state.

---

### Phase 1 — Project Scaffolding & CI

**Goal**: Establish the repository structure, tooling, linting, Docker configuration, and CI pipeline. No features yet — just a working skeleton that builds, lints, and passes an empty test suite.

**Deliverables**:
- Initialize git repo with `.gitignore`
- Backend: `pyproject.toml` with FastAPI, SQLAlchemy, Alembic, pytest, Ruff
- Backend: `app/main.py` with a health-check endpoint (`GET /api/health`)
- Backend: `tests/conftest.py` + `test_health.py`
- Frontend: Vite + React + TypeScript scaffold
- Frontend: Tailwind CSS configured with the project color palette and dark mode
- Frontend: ESLint + Prettier config
- Frontend: one passing placeholder test via Vitest
- `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml` (ports bound to `127.0.0.1`; non-root user; `read_only` + `no-new-privileges`)
- CORS middleware configured: allow origin `http://localhost:3000` only
- Request body size limit middleware (1 MB default)
- FastAPI exception handlers: generic error responses, no stack traces when `DEBUG=false`
- `.github/workflows/ci.yml` — lint, test, build for both backend and frontend; `pip-audit` and `npm audit` as warning steps
- `README.md` and `docs/index.html` with project overview and security notes
- Verify: `docker compose up` starts both services; CI passes

**Tests**:
- `GET /api/health` returns `200 {"status": "ok"}`
- Frontend renders without errors
- Cross-origin request from a disallowed origin is rejected
- Request body > 1 MB returns 413
- Error response with `DEBUG=false` does not contain a stack trace

---

### Phase 2 — Database, Models & Migrations

**Goal**: Define all SQLAlchemy models, create Alembic migrations, and implement the seed data command.

**Deliverables**:
- All models defined: `users`, `api_keys`, `journal_entries`, `metric_types`, `metric_entries`, `exercise_types`, `result_entries`, `goals`
- `database.py` — SQLite engine, session factory
- Alembic initial migration auto-generated from models
- CLI command (`python -m app.seed`) to populate default metric types and exercise types
- `config.py` — settings loaded from environment variables (database path, etc.)
- Logo: Design SVG source (`assets/logo.svg`), export transparent PNG (`frontend/public/logo.png`), favicon (`frontend/public/favicon.ico`), and mobile icon (`frontend/public/logo-192.png`); add to `index.html` *(moved from Phase 9)*

**Tests**:
- Models can be created and queried in an in-memory SQLite test database
- Seed command populates expected default metric types and exercise types
- Alembic migration applies cleanly to a fresh database

---

### Phase 3 — Journal CRUD (Backend + Frontend)

**Goal**: Full journal entry lifecycle — the first user-facing feature, end to end.

**Deliverables**:
- Backend: `routers/journals.py`, `services/journal.py`, `schemas/journal.py`
- All CRUD endpoints for journal entries (no auth yet — added in Phase 7)
- Frontend: Journal list page, journal detail/edit page with Markdown editor
- Frontend: Markdown rendering via `react-markdown` + `rehype-sanitize` (strict allowlist — no `<script>`, no event handlers, no `javascript:` URIs)
- Frontend: API client module (`api/client.ts`) with fetch wrapper (includes `X-Requested-With: HealthStudio` header on all requests)

**Tests** (TDD):
- Backend: Create, read, update, delete journal entries; pagination; date filtering
- Frontend: Renders journal list; creates a new entry; edits existing entry

---

### Phase 4 — Metrics Tracking (Backend + Frontend)

**Goal**: Metric types and metric entry CRUD, plus trend visualization.

**Deliverables**:
- Backend: CRUD for metric types and metric entries; trend endpoint returning time-series data
- Frontend: Metrics page — type selector, entry log form, Plotly trend chart
- Ability to add custom metric types from the UI
- Duration input: metric types with unit `"minutes"` render hours + minutes inputs; stored as total minutes, displayed as `Xh Ym`
- Seed data: default metric types and exercise types populated via `entrypoint.sh` on first container start (idempotent — safe on every restart, no lifespan seeding)
- Sleep Duration seed unit changed from `"hours"` to `"minutes"` for proper hours+minutes UX
- 7-day running average: toggle checkbox above the chart adds a dashed teal trend line; carries forward last known value for days without entries
- Chart: Plotly legend text set to white (`#F1F5F9`) for visibility on dark background
- Basic sidebar navigation: logo + "Health Studio" header, NavLink entries for Journal and Metrics (moved forward from Phase 9 for usability during development)

**Tests** (TDD):
- Backend: CRUD for types and entries; trend endpoint returns correct shape; seed function populates defaults and is idempotent
- Frontend: Renders metric type list; logs an entry; chart renders with data; 7-day average toggle adds second trace; hours+minutes inputs for duration types; duration display formatting

---

### Phase 5 — Results Tracking (Backend + Frontend)

**Goal**: Exercise types, result logging, PR detection, trend visualization, and rich editing UX.

**Deliverables**:
- Backend: CRUD for exercise types and result entries; auto-PR detection logic; PR history endpoint; trend endpoint
- Frontend: Results page — exercise selector, result log form, PR badges, Plotly trend chart
- Ability to add custom exercise types from the UI
- Time-based input UX: hours/minutes/seconds inputs for time-based exercises (stored as total seconds, displayed as `Xh Ym Zs`)
- RX checkbox for CrossFit benchmarks: `is_rx` field on `result_entries` (Alembic migration); PR logic updated so RX beats non-RX for time-based CrossFit benchmarks
- Inline edit mode: edit value, date, notes, and RX flag directly in the results table with Save/Cancel affordance
- PR recalculation on update: when a result's value or `is_rx` flag is edited, PR status is recalculated across all entries for that exercise (uses `exclude_id` to avoid self-comparison)
- Show/hide graph toggle: compact icon button above the table; graphs hidden by default to keep the page focused on data entry
- Alembic migration runs on container start (`alembic upgrade head` in `entrypoint.sh`) so new columns are applied automatically
- Inline edit mode also added to Metrics page (edit value, date, notes) for consistency

**Tests** (TDD):
- Backend: PR is correctly flagged when a new best is logged; trend and PR endpoints return correct data; RX PR logic (6 tests); PR recalculation on update (value change, RX flag change, unrelated field preserves PR)
- Frontend: Renders exercise list; logs a result; PR badge appears; chart renders behind toggle; inline edit (enter, save, cancel); RX checkbox in create and edit modes

---

### Phase 5.5 — Type Selector UX Cleanup (Frontend)

**Goal**: Replace the tag button list for type selection on Results and Metrics pages with a compact dropdown + manage panel.

**Deliverables**:
- Results page: exercise type selector is now a `<select>` dropdown with `<optgroup>` categories (Olympic Lift, Power Lift, CrossFit Benchmark, Running, Custom)
- Metrics page: metric type selector is now a `<select>` dropdown
- Both pages: "Manage" toggle button replaces the old inline `+ Add Type` button and per-type `×` delete buttons
- Manage panel (shown on toggle) contains existing types as compact chips with delete buttons, plus the create form
- Default view is clean: dropdown + Manage button on one line; no tag clutter

**Tests** (TDD):
- Dropdown renders as `<select>` with correct default value
- Switching type via dropdown triggers data reload
- Manage panel shows/hides on toggle with delete buttons and create form
- Toggle closes manage panel on second click

---

### Phase 6 — Goals & Dashboard (Backend + Frontend)

**Goal**: Goal creation with Markdown plans, progress tracking, and a summary dashboard.

**Deliverables**:

#### Backend
- CRUD for goals (`/api/goals`): create, read, list (with status filter + pagination), update, delete
- Goal model fields: `title`, `description`, `plan` (Markdown), `target_type` (metric or result), `target_id`, `target_value`, `start_value` (optional), `current_value` (computed), `lower_is_better` (boolean, default false), `status` (active/completed/abandoned), `deadline` (optional date)
- Dynamic progress computation in service layer:
  - `current_value` auto-computed from latest metric entry or best PR for the linked target
  - When `start_value` is set, progress = percentage of distance from start→target covered: `(current - start) / (target - start) * 100` for higher-is-better, `(start - current) / (start - target) * 100` for lower-is-better (clamped 0–100)
  - When `start_value` is null, legacy formula: `current / target * 100` for higher-is-better, `target / current * 100` for lower-is-better
- Dashboard summary endpoint (`/api/dashboard/summary`): recent journals (last 5), active goals with progress, latest metric per type, recent PRs (last 5)
- Alembic migrations for `lower_is_better` and `start_value` columns on the `goals` table

#### Frontend
- Goals page — create/edit form with Markdown plan editor, progress bar, status management (active/completed/abandoned filter)
- Goal form fields: title, description, plan (Markdown textarea), target type selector (metric/exercise result), target selector (populated from metric types or exercise types), target value, starting value (optional), deadline, "Lower is better" checkbox with helper text
- Goal display: progress bar (primary color for active, accent for completed), direction indicator (`↓ Lower is better` / `↑ Higher is better`), start value shown when set, deadline display
- Collapsible plan disclosure ("▶ Plan" toggle) with `react-markdown` + `remark-gfm` rendering (tables, strikethrough, GFM support) using `@tailwindcss/typography` prose styling
- Dashboard page — 4 summary cards: Recent Journal Entries (links), Active Goals (progress bars), Latest Metrics (with duration formatting for minutes≥60), Recent PRs (badges)
- Default route changed from `/journals` to `/dashboard`; Sidebar updated with Dashboard and Goals navigation links

#### Additional Enhancements (implemented during Phase 6)
- Added `reps` as an exercise result unit type (Results page dropdown); existing higher-is-better PR logic covers reps naturally
- Installed `remark-gfm` for GFM Markdown support (tables, strikethrough) in Goals plans and Journal edit preview
- Installed `@tailwindcss/typography` plugin with custom dark-mode prose theme (slate text, blue links, dark code blocks, styled table borders, muted strikethrough)
- Duration formatting helper on Dashboard for metrics with `unit="minutes"` and value≥60 → "Xh Ym" display

**Tests** (TDD):
- Backend: Goal CRUD (12 tests), goal progress computation (3 tests), lower-is-better flag (7 tests), start_value progress (10 tests), dashboard summary aggregation (5 tests) — 37 goal-specific tests
- Backend: Reps PR detection (3 tests)
- Frontend: Goals page — renders list, empty state, progress bar, create goal, complete, delete, filter by status, direction indicators, lower-is-better checkbox, start value display/creation (12 tests)
- Frontend: Dashboard — summary cards, goal progress bar, empty state, PR badges (4 tests)

---

### Phase 7 — Authentication & API Keys

**Goal**: Passkey registration/login and API key management.

**Deliverables**:
- Backend: WebAuthn registration and authentication flow via `py_webauthn` (single-user; registration locks after first user)
- Backend: Challenges are random, single-use, server-stored with 5-minute TTL; `sign_count` validated on each auth
- Backend: Session management (HTTP-only cookie; `SameSite=Strict`; `Path=/api`; cryptographically random token via `secrets.token_urlsafe(32)`)
- Backend: Session token regenerated on login; idle timeout 24h; absolute timeout 7d; logout deletes session server-side
- Backend: API key generation (returned once), bcrypt-hashed storage, validation, and revocation
- Backend: Rate limit on failed auth attempts (5/min per IP) to resist brute-force
- Backend: Auth middleware — all existing endpoints require authentication (session cookie or API key header); `X-Requested-With` header required on state-changing requests (CSRF defense)
- Frontend: One-time registration page (shown only on first launch) and login page with passkey UI
- Frontend: Settings page for API key management (create, list, revoke); raw key shown once with copy button, then never again

**Tests** (TDD):
- Backend: Registration locks after first user; second registration attempt returns 403
- Backend: Authentication ceremony mocked; session validation; API key creation and auth
- Unauthenticated requests to protected endpoints return 401

---

### Phase 8 — CLI (`hs`)

**Goal**: A standalone command-line interface that talks to the Health Studio REST API, installable as a normal executable (`hs`) with no virtualenv activation required.

**Deliverables**:

#### CLI Core
- Standalone Python package in `cli/` with its own `pyproject.toml`
- Entry point: `hs` (via `[project.scripts]` in `pyproject.toml`)
- Built with Typer (command framework) + Rich (terminal formatting) + httpx (async HTTP client)
- ASCII art logo banner displayed on `hs --help` and `hs` (no args):
  ```
  ╦ ╦╔═╗╔═╗╦ ╔╦╗╦ ╦  ╔═╗╔╦╗╦ ╦╔╦╗╦╔═╗
  ╠═╣║╣ ╠═╣║  ║ ╠═╣  ╚═╗ ║ ║ ║ ║║║║ ║
  ╩ ╩╚═╝╩ ╩╩═╝╩ ╩ ╩  ╚═╝ ╩ ╚═╝═╩╝╩╚═╝
  ```
- `--version` flag

#### Configuration (`~/.health-studio/config.toml`)
- Created by `hs config init` — interactive prompts for base URL and API key
- TOML format:
  ```toml
  [server]
  base_url = "http://localhost:8000"

  [auth]
  api_key = "hs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  ```
- `hs config show` — prints current config (API key masked except prefix)
- `hs config set <key> <value>` — update a single config value
- Config file permissions set to `600` on creation (owner-only read/write)
- API key is read from config file, or from `HEALTH_STUDIO_API_KEY` env var (env var takes precedence)

#### Commands
- `hs journal list [--since DATE] [--limit N]` — tabular list of journal entries
- `hs journal show <id>` — render Markdown content in the terminal (via Rich Markdown)
- `hs journal create --title "..." --file entry.md` — create from a Markdown file
- `hs journal create --title "..." --editor` — open `$EDITOR` to compose, then submit
- `hs metrics types` — list metric types
- `hs metrics log <type> <value> [--date DATE] [--notes "..."]` — log a metric entry
- `hs metrics trend <type> [--since DATE]` — ASCII sparkline or table of recent values
- `hs results types` — list exercise types
- `hs results log <exercise> <value> [--date DATE] [--notes "..."]` — log a result
- `hs results prs [exercise]` — show PR table
- `hs goals list [--status active|completed|abandoned]` — list goals
- `hs goals show <id>` — show goal detail with progress
- `hs dashboard` — compact summary (mirrors the web dashboard)

#### Install Scripts
- `cli/scripts/install.sh` (macOS/Linux):
  - Checks for Python ≥ 3.11; installs via `pipx install .` if `pipx` is available, otherwise `pip install --user .`
  - Verifies `hs` is on `$PATH`; if not, prints the path to add
  - Creates `~/.health-studio/` directory with `700` permissions
  - Prints post-install instruction: "Run `hs config init` to connect to your Health Studio instance"
- `cli/scripts/install.ps1` (Windows PowerShell): equivalent logic using `pipx` or `pip install --user`
- Both scripts are idempotent (safe to re-run)

#### Security
- API key is never logged or printed in full (masked in `hs config show`)
- Config file created with `600` permissions; install script sets `700` on the directory
- httpx client sends API key via `Authorization: Bearer <key>` header — never in query params or URLs
- All user-supplied arguments are passed as request body/params — never interpolated into URLs

**Tests** (TDD):
- Config init creates TOML file with correct structure and `600` permissions
- Config reader falls back to env var when config file is absent
- Each command group calls the correct API endpoint with correct HTTP method and params (mocked httpx)
- `hs --help` output contains the ASCII art banner
- `hs journal create --file` reads the file and sends content to API
- Error responses from the API are displayed as user-friendly messages, not raw JSON

---

### Phase 9 — Polish, Logo & Documentation

**Goal**: Final UX polish, logo asset, and comprehensive documentation.

**Deliverables**:
- ~~Logo: Design and export transparent PNG; add to header and as favicon~~ *(moved to Phase 2)*
- UX: Responsive sidebar; mobile breakpoints; loading states; empty states; toast notifications for actions
- Dark mode toggle finalized and persisted
- `README.md` fully updated with setup instructions, architecture overview, API reference summary, CLI usage, screenshots
- `docs/index.html` kept in sync with README content
- Review and fill any gaps in test coverage

**Tests**:
- Dark mode toggle persists preference
- Responsive layout renders correctly at mobile breakpoints
- All existing tests still pass (regression)

---

### Phase 10 — End-to-End Testing (Playwright)

**Goal**: Add a comprehensive end-to-end test suite using Playwright to verify critical user flows against the real running application. This phase should be implemented after all feature phases are complete.

**Deliverables**:
- Playwright installed and configured in the frontend project (or a dedicated `e2e/` directory at the repo root)
- Playwright config targeting the Docker Compose stack (`http://localhost:3000`)
- Docker Compose test profile or script that spins up the full stack, runs Playwright, and tears down
- E2E tests covering the core user flows:
  - **Journal**: Create a new journal entry, verify it appears in the list, edit it, delete it
  - **Metrics**: Create a custom metric type, log entries, verify chart renders, edit an entry, delete it
  - **Results**: Create a custom exercise type, log results with PR detection, verify PR badge appears, edit a result, toggle RX flag, verify graph toggle
  - **Goals**: Create a goal linked to a metric or exercise, verify progress updates, mark as completed
  - **Dashboard**: Verify summary cards reflect data from other modules
  - **Auth** (once implemented): Registration flow, login, logout, session expiry, API key creation
  - **Navigation**: Sidebar links navigate correctly; browser back/forward work; deep links load the correct page
  - **Responsive layout**: Key flows work at mobile viewport widths
- CI integration: Playwright tests run as a separate job in `.github/workflows/ci.yml` after the unit test jobs pass
- Test data seeding: a fixture or setup script that populates the database with known test data before each test suite run; teardown after

**Tests**:
- All E2E scenarios listed above pass against a clean Docker Compose stack
- Tests are deterministic and do not depend on execution order
- CI job uploads Playwright trace files and screenshots as artifacts on failure for debugging

---

## CI Pipeline (`.github/workflows/ci.yml`)

Triggered on every push and pull request:

```
Jobs:
  backend:
    - Checkout
    - Set up Python 3.12
    - Install dependencies (pip install -e ".[dev]")
    - Ruff lint + format check
    - pytest with coverage report
  frontend:
    - Checkout
    - Set up Node 20
    - npm ci
    - ESLint
    - Prettier --check
    - Vitest run
    - vite build
  cli:
    - Checkout
    - Set up Python 3.12
    - Install CLI package (pip install -e "cli/[dev]")
    - Ruff lint + format check
    - pytest cli/tests/
```

---

## Docker Compose Topology

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "127.0.0.1:8000:8000"   # Bind to localhost only — never expose to LAN
    volumes:
      - ./data:/app/data    # SQLite file persisted on host
    environment:
      - DATABASE_URL=sqlite:///data/health_studio.db
      - DEBUG=false
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "127.0.0.1:3000:3000"   # Bind to localhost only
    read_only: true
    security_opt:
      - no-new-privileges:true
    depends_on:
      - backend
```

---

## TDD Workflow (Per Feature)

1. Write failing tests that define the expected endpoint behavior or component rendering.
2. Implement the minimal code to make the tests pass.
3. Refactor for clarity while keeping tests green.
4. Run linters (`ruff check`, `eslint`, `prettier --check`).
5. Commit with a descriptive message referencing the phase.

---

## Conventions

- **Commits**: `phase-N: short description` (e.g., `phase-3: add journal CRUD endpoints and tests`)
- **Branch strategy**: Feature branches per phase, merged to `main` via PR
- **API versioning**: All endpoints under `/api/` — no version prefix initially; add `/api/v2/` only if breaking changes arise
- **Error responses**: Consistent JSON shape: `{"detail": "message"}` with appropriate HTTP status codes
- **Dates**: ISO 8601 (`YYYY-MM-DD`) everywhere — API, database, UI
- **IDs**: UUIDs generated server-side

---

## Threat Analysis

Even as a single-user local application, Health Studio stores sensitive personal health data. The following threat model ensures the app is secure by design.

### Threat Surface Summary

| # | Threat | Category | Severity | Phase Addressed |
|---|--------|----------|----------|----------------|
| T1 | Network exposure via Docker port binding | Network | **High** | 1 |
| T2 | Cross-Site Scripting (XSS) via Markdown rendering | Injection | **High** | 3 |
| T3 | Cross-Site Request Forgery (CSRF) | Session | **High** | 7 |
| T4 | SQL Injection | Injection | **Medium** | 2 |
| T5 | Session hijacking / fixation | Session | **High** | 7 |
| T6 | API key leakage | Credential Mgmt | **Medium** | 7 |
| T7 | Data at rest exposure (SQLite file) | Data Protection | **Medium** | 2 |
| T8 | Dependency supply-chain attacks | Supply Chain | **Medium** | 1 |
| T9 | Sensitive data in logs / error responses | Information Disclosure | **Medium** | 1 |
| T10 | Docker container running as root | Privilege Escalation | **Medium** | 1 |
| T11 | Unrestricted CORS | Network | **Medium** | 1 |
| T12 | WebAuthn challenge replay | Authentication | **Medium** | 7 |
| T13 | Markdown editor code injection (stored XSS) | Injection | **High** | 3 |
| T14 | Denial of service via large payloads | Availability | **Low** | 1 |

### Detailed Mitigations

#### T1 — Network Exposure via Docker

**Threat**: By default, `docker compose` binds ports to `0.0.0.0`, exposing the app to every device on the local network (and potentially the internet if the host has a public IP or is on an open Wi-Fi network).

**Mitigations**:
- Bind all published ports to `127.0.0.1` only in `docker-compose.yml` (e.g., `127.0.0.1:8000:8000`).
- Document this as a critical security setting in `README.md`.
- Add a startup log message confirming the listen address.

#### T2 / T13 — XSS via Markdown Rendering

**Threat**: User-authored Markdown (journals, goal plans, notes) is rendered as HTML. Malicious or accidental `<script>` tags, `onerror` handlers, or `javascript:` URIs could execute arbitrary code in the browser. Even though the user is also the author, this matters if data is ever imported, pasted from external sources, or if the API is accessed by a script that writes to the DB.

**Mitigations**:
- Use `react-markdown` with `rehype-sanitize` — a strict allowlist-based HTML sanitizer that strips all dangerous elements and attributes.
- Never use `dangerouslySetInnerHTML` for Markdown content.
- Configure `rehype-sanitize` with the GitHub schema (default) which blocks `<script>`, `<iframe>`, `<object>`, `<embed>`, event handlers, and `javascript:` URIs.
- Test: Verify that `<script>alert(1)</script>` in a journal entry renders as escaped text, not executable HTML.

#### T3 — Cross-Site Request Forgery (CSRF)

**Threat**: A malicious page opened in the same browser could make authenticated requests to `localhost:8000` using the session cookie, performing unwanted state changes (deleting data, creating entries, etc.).

**Mitigations**:
- Set `SameSite=Strict` on the session cookie (prevents the browser from sending the cookie on cross-origin requests).
- Require a custom header (`X-Requested-With: HealthStudio`) on all state-changing API requests; the frontend includes it in the fetch wrapper. Browsers block cross-origin requests with custom headers unless CORS allows it.
- CORS origin allowlist is `http://localhost:3000` only — no wildcards.

#### T4 — SQL Injection

**Threat**: Direct string interpolation into SQL queries could allow injection.

**Mitigations**:
- All database access goes through SQLAlchemy ORM — queries are parameterized by default.
- Never use raw SQL string formatting. If raw SQL is ever needed, use `text()` with bound parameters.
- Ruff lint rule `S608` (hardcoded SQL expressions) is enabled to catch accidental raw SQL.
- Pydantic schemas validate and constrain all input fields (types, lengths, allowed values) before they reach the ORM.
- Test: Include a test that attempts SQL injection via API input and verifies it is treated as literal text.

#### T5 — Session Hijacking / Fixation

**Threat**: If the session token is stolen or predictable, an attacker on the same network could impersonate the user.

**Mitigations**:
- Session cookie flags: `HttpOnly` (no JS access), `Secure=false` (localhost is HTTP — acceptable), `SameSite=Strict`, `Path=/api`.
- Use cryptographically random session tokens (Python `secrets.token_urlsafe(32)`).
- Regenerate the session token on every successful login to prevent fixation.
- Session expiry: configurable idle timeout (default 24 hours); absolute timeout (default 7 days).
- Logout invalidates the session server-side (delete from store), not just the cookie.

#### T6 — API Key Leakage

**Threat**: API keys could be logged, stored in plaintext, or exposed in API responses.

**Mitigations**:
- Raw API key is returned exactly once at creation time; only the `prefix` and `key_hash` are stored.
- API keys are hashed with bcrypt before storage — not reversible.
- API key values are never included in logs, error messages, or any GET response.
- `GET /api/keys` returns only name, prefix, created/last-used dates, and revocation status.
- Rate-limit failed API key authentication attempts (5 failures per minute) to resist brute-force.

#### T7 — Data at Rest Exposure

**Threat**: The SQLite file on the host contains sensitive health data. Anyone with file-system access to the host can read it.

**Mitigations**:
- Set the SQLite file permissions to `600` (owner read/write only) via the Docker entrypoint script.
- Document that users should rely on OS-level full-disk encryption (FileVault on macOS, LUKS on Linux) as the primary data-at-rest protection.
- The Docker volume mount (`./data`) should not be world-readable; document the recommended `chmod 700 ./data`.
- Consider adding an optional SQLite encryption layer (SQLCipher) as a future enhancement — note this in the plan but do not implement in v1.

#### T8 — Dependency Supply-Chain Attacks

**Threat**: Compromised npm or PyPI packages could introduce backdoors.

**Mitigations**:
- Pin all dependency versions in `pyproject.toml` and `package-lock.json` (lock files committed to git).
- Enable GitHub Dependabot alerts and security updates on the repository.
- CI pipeline includes `npm audit` (frontend) and `pip-audit` (backend) as non-blocking warning steps.
- Use minimal, well-maintained dependencies; audit any new dependency before adding.

#### T9 — Sensitive Data in Logs / Error Responses

**Threat**: Health data, session tokens, or stack traces could leak into logs or API error responses.

**Mitigations**:
- FastAPI exception handlers return generic `{"detail": "message"}` — never raw stack traces in production mode.
- Configure Python logging to redact or exclude request bodies on health-data endpoints.
- Never log session tokens, API keys, or passkey credentials.
- Set `DEBUG=false` by default in Docker; only enable via explicit environment variable.

#### T10 — Docker Container Running as Root

**Threat**: If the container is compromised, a root-level process can escape to the host more easily.

**Mitigations**:
- Both Dockerfiles create and use a non-root user (`USER appuser`).
- The SQLite data directory is owned by `appuser` inside the container.
- Use `--read-only` filesystem where possible; mount only the data volume as writable.

#### T11 — Unrestricted CORS

**Threat**: A permissive CORS policy (e.g., `Access-Control-Allow-Origin: *`) would allow any website to make authenticated requests.

**Mitigations**:
- CORS middleware allows only `http://localhost:3000` as the origin.
- `Access-Control-Allow-Credentials: true` is set (required for cookies), but only for the allowed origin.
- No wildcard origins, methods, or headers.

#### T12 — WebAuthn Challenge Replay

**Threat**: An attacker who intercepts a WebAuthn challenge/response pair could replay it.

**Mitigations**:
- Challenges are random, single-use, and stored server-side with a short TTL (5 minutes).
- After verification, the challenge is deleted — replay returns an error.
- `sign_count` is validated and incremented on each authentication to detect cloned authenticators.

#### T14 — Denial of Service via Large Payloads

**Threat**: Extremely large request bodies could exhaust memory or disk.

**Mitigations**:
- FastAPI request body size limit: 1 MB default (configurable).
- Markdown content fields have a max length validation in Pydantic schemas (e.g., 100 KB for journal content).
- Pagination enforced on all list endpoints (max 100 items per page).

### Security Testing Checklist

These tests should be included across the relevant phases:

- [ ] `<script>alert(1)</script>` in Markdown fields renders as escaped text (Phase 3)
- [ ] SQL injection attempt via API input is treated as literal text (Phase 2)
- [ ] Cross-origin request without CORS allowlist is rejected (Phase 1)
- [ ] Request without session cookie or API key returns 401 (Phase 7)
- [ ] Second registration attempt returns 403 (Phase 7)
- [ ] Revoked API key returns 401 (Phase 7)
- [ ] Expired session returns 401 (Phase 7)
- [ ] Request body exceeding 1 MB is rejected with 413 (Phase 1)
- [ ] `GET /api/keys` never returns raw key values (Phase 7)
- [ ] Error responses do not contain stack traces when `DEBUG=false` (Phase 1)

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| WebAuthn complexity on localhost | Use `localhost` as the relying party; test with Chrome DevTools virtual authenticator |
| Plotly bundle size | Lazy-load chart components; use partial Plotly bundles if needed |
| SQLite concurrency limits | Single-user local app — not a concern; use WAL mode for safety |
| LLM context limits per phase | Each phase is scoped to ~4–8 files of changes; models/schemas are small and self-contained |
| Compromised dependency | Pinned versions, lock files, Dependabot alerts, `pip-audit` / `npm audit` in CI |
| Accidental public exposure | Ports bound to `127.0.0.1` only; documented in README with warnings |
| Data loss | SQLite WAL mode; document backup strategy (`cp data/health_studio.db backup/`) |
