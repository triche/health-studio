# Health Studio — Next Steps & Recommendations

A review of the full codebase as of April 2026. All 10 implementation phases are complete and working. This document covers what's worth doing next, organized by category and rough priority.

---

## Table of Contents

- [Performance](#performance)
- [Security Hardening](#security-hardening)
- [Frontend Quality of Life](#frontend-quality-of-life)
- [Backend Improvements](#backend-improvements)
- [Data & Portability](#data--portability)
- [CLI Enhancements](#cli-enhancements)
- [Accessibility](#accessibility)
- [Testing Gaps](#testing-gaps)
- [Docker & Deployment](#docker--deployment)
- [Feature Ideas](#feature-ideas)

---

## Performance

### Dashboard N+1 Queries — High Priority

`dashboard.py` has three N+1 query patterns that will degrade as data grows:

1. **Metric types loop** — fetches all metric types, then queries the latest entry *per type* in a loop
2. **PR exercise types** — fetches recent PRs, then looks up the exercise type *per PR* in a loop
3. **Goal progress** — fetches active goals, then computes current value *per goal* (each hitting the DB)

**Fix:** Use `joinedload()` / `selectinload()` for eager loading, or batch-fetch related records with `in_()` clauses. The dashboard is the most-hit page, so this matters first.

### Trend Endpoint Pagination

Trend endpoints (`/api/metrics/trends/{id}`, `/api/results/trends/{id}`) return *all* data points with no limit. A user with years of daily entries will get thousands of points in one response and Plotly will struggle to render them.

**Options:** Add optional `limit` / date range defaults, or implement server-side downsampling for large datasets.

### Goal Progress Caching

`current_value` on goals is recomputed from scratch on every fetch. Fine for now, but could be cached and invalidated when a new metric/result is logged for the linked target.

---

## Security Hardening

### Nginx Security Headers — High Priority

`nginx.conf` has zero security headers. For anything beyond localhost:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

Even for local use, `X-Frame-Options: DENY` prevents clickjacking if the port is accidentally exposed.

### In-Memory Auth State ✅ Implemented

Sessions, challenges, and rate limits are now persisted in SQLite via three new models (`AuthSession`, `AuthChallenge`, `AuthRateLimit`) with an Alembic migration. Process restarts no longer wipe sessions or reset rate limits. Multi-worker sharing would still require Redis.

### Dev Dependencies in Production Docker Image ✅ Implemented

`Dockerfile.backend` now installs only production dependencies (`pip install .` without `.[dev]`), removing pytest, ruff, httpx, and pip-audit from the production image.

### SQLite Encryption at Rest

The database file is plain-text on disk. If the host is compromised, all health data is readable. Consider `sqlcipher` or filesystem-level encryption if the threat model warrants it.

---

## Frontend Quality of Life

### Markdown Editor Toolbar ✅ Implemented

Journal and goal plan editors now use a reusable `MarkdownEditor` component wrapping `@uiw/react-md-editor` with a toolbar providing bold, italic, strikethrough, headings (H1–H4 dropdown), quote, lists (unordered, ordered, checklist), link, image, and horizontal rule. Auto-syncs dark/light mode.

### Keyboard Shortcuts

- **Dark mode toggle:** `Ctrl+Shift+D` or similar
- **New journal entry:** `Ctrl+N` from the journal list
- **Quick save:** `Ctrl+S` in editors (currently requires clicking the button)

### Jump-to-Page Pagination

Current pagination is prev/next only. For long journal or metric histories, a page number input or "jump to page" control would help.

### Chart Export

Plotly supports `toImage()` for PNG/SVG export. An export button on trend charts would let you save or share progress snapshots.

### Better Empty States

Some pages show a bare empty list when there's no data. Friendly empty states with "Get started by..." prompts and direct action buttons would improve first-run experience.

### Time Input Clarity

The hours/minutes/seconds inputs for CrossFit benchmarks work but can be confusing. Consider a single input with format hint (`mm:ss` or `h:mm:ss`) that auto-formats, similar to how stopwatch apps work.

### Toast Positioning

Verify toasts don't overlap with the sidebar on mobile. A bottom-center or top-right position works better on small screens.

---

## Backend Improvements

### Bulk Operations

No bulk endpoints exist. If you ever want to import historical data (e.g., paste a spreadsheet of old metric entries), you'd need to POST one at a time. A `POST /api/metrics/bulk` endpoint would help.

### Soft Deletes

All deletes are hard deletes. If you accidentally delete a journal entry or result, it's gone. Consider adding a `deleted_at` column and keeping records for 30 days before permanent removal, or at minimum a confirmation step.

### Audit Log

No record of what changed and when. A lightweight `audit_log` table (entity, entity_id, action, timestamp) would help with debugging and data recovery.

### API Versioning

All endpoints are under `/api/` with no version prefix. The implementation plan notes adding `/api/v2/` for breaking changes. Worth keeping in mind but not urgent until you actually need a breaking change.

### OpenAPI Documentation

FastAPI auto-generates OpenAPI docs at `/docs`. Verify these are either disabled in production (they expose your full API schema) or protected behind auth.

### Metric Aggregations

The trend endpoint returns raw data points. Server-side aggregations (weekly average, monthly totals, min/max over period) would enable richer dashboard cards without frontend computation.

---

## Data & Portability

### Export / Import — High Value ✅ Implemented

No way to get data out of Health Studio except direct SQLite access. This is the biggest missing capability for a personal data tool.

**Export options (implemented):**
- JSON dump of all data (full backup, machine-readable) — `GET /api/export/json`
- CSV per entity type (journals, metrics, results — spreadsheet-friendly) — `GET /api/export/csv/{entity}`
- Markdown export for journals (one combined `.md` file) — `GET /api/export/journals/markdown`

**Import options (implemented):**
- JSON restore from backup (skips duplicates) — `POST /api/import/json`
- CSV import for metrics/results (bulk historical data) — `POST /api/import/csv/{entity}`

Available via API, frontend Settings page, and CLI (`hs export`, `hs import`).

### Automated Backups

`scripts/db-backup.sh` exists but must be run manually. A cron job or scheduled task integration (even just documenting the crontab line) would prevent data loss.

### Data Migration Path

If you ever want to move from SQLite to PostgreSQL (for better concurrency or cloud hosting), having an export/import pipeline makes this straightforward.

---

## CLI Enhancements

### Fuzzy Name Matching

`resolve.py` only does UUID prefix matching. Being able to type `hs results log "back squat" 315` instead of looking up the UUID would be much more ergonomic. The types list is small enough that case-insensitive substring matching would work.

### Pagination in resolve.py

`resolve_id()` only checks the first page of results. If you have many custom types, a truncated UUID prefix might not find its match.

### Interactive Mode

`hs journal create --editor` opens `$EDITOR`, which is great. Consider extending this pattern:
- `hs metrics log` with no args → interactive prompts (pick type, enter value)
- `hs results log` with no args → interactive prompts with category grouping

### Shell Completions

Typer supports generating shell completions (`hs --install-completion`). Worth documenting in the README or install script.

### ASCII Sparklines in Trends

The implementation plan mentions "ASCII sparkline deferred to Phase 9 polish" for `hs metrics trend`. Still deferred. A mini inline chart in the terminal would be a nice touch.

---

## Accessibility

### Semantic HTML Landmarks

The app uses `<div>` for most structural elements. Adding `<main>`, `<aside>` (sidebar), and `<header>` would help screen readers navigate. The sidebar already uses `<nav>`, which is good.

### Progress Bar Roles

Dashboard goal progress bars are styled `<div>` elements. Adding `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` makes them readable by assistive technology.

### Form Label Associations

Form labels exist but some rely on nesting rather than explicit `for`/`id` attributes. Explicit associations are more robust and work better with assistive tools.

### Live Regions

When charts update, toasts appear, or goals recalculate, screen readers don't know. `aria-live="polite"` on dynamic content regions would announce changes.

### Focus Management

After creating or deleting an item, focus should move to a logical place (e.g., back to the list, or to a confirmation message). Currently it likely stays on the now-gone delete button.

---

## Testing Gaps

### Frontend Error/Edge Cases

Tests mostly mock successful API responses. Not covered:

- API returning 500, 404, network timeout
- Empty data states (no journals, no metrics)
- Very long content (title overflow, huge markdown)
- Session expiry mid-interaction (401 during a save)
- Form validation (required fields, invalid dates, negative values)

### Frontend Accessibility Tests

No tests verify keyboard navigation, focus traps in modals, or screen reader text. `vitest-axe` or `@testing-library/jest-dom` `toHaveAccessibleName()` matchers can catch basic issues.

### Backend Concurrency

No tests for concurrent writes to the same entity. SQLite handles this with locking, but verifying the behavior (especially for PR recalculation) would catch surprises.

### CLI Error Handling

CLI tests mock successful API responses. Testing what happens when the API is down, returns errors, or the config file is malformed would improve robustness.

### Load / Stress Testing

No performance tests exist. A simple script that seeds 10,000 metric entries and times the trend endpoint would establish a baseline and catch the N+1 issue quantitatively.

---

## Docker & Deployment

### Restart Policy

`docker-compose.yml` has no `restart:` policy. Adding `restart: unless-stopped` ensures the app comes back after a host reboot.

### Production Deployment Guide

The README covers local Docker usage but not deploying to a VPS, NAS, or home server. A short guide covering:

- Reverse proxy setup (Caddy/nginx with HTTPS)
- Firewall rules
- Systemd service file (alternative to Docker)
- Backup cron job

...would make self-hosting much easier.

### Docker Image Size Audit

The backend image includes dev dependencies (pytest, ruff, etc.). A multi-stage build or separate install target would shrink the image.

### Health Check Refinement

The backend health check hits `/api/health` which returns `{"status": "ok"}` but doesn't verify the database is reachable. A deeper health check (`SELECT 1` against SQLite) would catch file permission or corruption issues.

---

## Feature Ideas

These are larger efforts that would meaningfully expand what Health Studio does. Listed roughly by value-to-effort ratio.

### Streaks & Habits
Track daily habits (did you work out? meditate? stretch?) with streak counting. Simple boolean entries per day, with a calendar heatmap view (GitHub contribution graph style). Low backend complexity, high daily engagement value.

### Workout Logger
A dedicated page for logging a full workout session: multiple exercises, sets × reps × weight, rest times. Currently each exercise result is a standalone entry with one value. A "workout" entity that groups multiple result entries would better model real training.

### Body Composition Tracking
Extend metrics with body fat percentage, lean mass, BMI calculations. Auto-compute derived metrics when weight + body fat are both logged. Show composition trends over time.

### Photo Progress
Allow attaching photos to journal entries or as standalone progress pics. Before/after comparisons. Storage-wise, keep images on the local filesystem with DB references. This changes the single-user, text-only simplicity though, so consider carefully.

### Weekly/Monthly Reports
Auto-generated summary reports: this week's PRs, total workouts, metric trends, goal progress. Could render as a dedicated page or as a periodic journal entry auto-created by a background task.

### Integrations
- **Apple Health / Google Fit** import (steps, sleep, heart rate)
- **Garmin/Strava** activity import
- **CSV/JSON import from other apps** (MyFitnessPal, Strong, etc.)

These are significant undertakings but would make Health Studio a true data hub rather than a standalone tracker.

### Tags / Categories for Journals
Currently journals are a flat chronological list. Tags (e.g., `#recovery`, `#nutrition`, `#mindset`) would enable filtering and grouping. Simple many-to-many relationship.

### Notes on Dashboard Cards
The dashboard shows recent PRs and metrics but with limited context. Showing the associated notes inline (truncated) would add valuable context at a glance.

---

*Generated April 2026 from codebase review.*
