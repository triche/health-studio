# Health Studio

A local-first personal health dashboard, journal, and tracker. Consolidates mental and physical health management into a single, self-hosted web application deployed via Docker. All data lives locally on the host machine.

## Features

- **Journal** — Markdown journal entries with rich editing and preview
- **Metrics** — Track body metrics (weight, waist, steps, sleep, water) with interactive Plotly.js trend charts and 7-day moving averages
- **Results** — Log exercise results with automatic PR detection across Olympic lifts, powerlifts, CrossFit benchmarks, and running
- **Goals** — Set goals linked to metrics or exercises with progress tracking and Markdown plans
- **Dashboard** — Aggregated overview of recent activity, active goals, latest metrics, and recent PRs
- **Dark/Light mode** — Toggle between themes; preference persisted in localStorage
- **Responsive layout** — Collapsible sidebar for mobile; full sidebar on desktop
- **CLI** — Full-featured command-line interface (`hs`) for managing data from the terminal

## Quick Start

```bash
docker compose up
```

Visit **http://localhost:3000** to register a passkey and start using the app.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/health |

## Architecture

```
┌────────────────┐      ┌────────────────┐      ┌──────────┐
│   React SPA    │─────▶│  FastAPI       │─────▶│  SQLite  │
│  (Vite + TS)   │ REST │  (Python 3.12) │      │          │
│  port 3000     │      │  port 8000     │      │ data/    │
└────────────────┘      └────────────────┘      └──────────┘
```

- **Frontend**: React 19, TypeScript, Tailwind CSS, Plotly.js, react-markdown
- **Backend**: FastAPI, SQLAlchemy, Alembic, py_webauthn
- **Database**: SQLite — zero-config, file-based, stored in `backend/data/`
- **Auth**: WebAuthn/Passkeys (passwordless) + scoped API keys for CLI/scripts

## Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Run tests and linting:

```bash
cd backend
ruff check . && ruff format --check .
pytest -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Run tests and linting:

```bash
cd frontend
npm run lint && npm run format:check
npm test
npm run build
```

### CLI

```bash
cd cli
pip install -e ".[dev]"
hs --help
```

Configure the CLI:

```bash
hs config init              # Create ~/.health-studio/config.toml
hs config set url http://localhost:8000
hs config set api-key <your-key>
```

CLI commands:

```
hs dashboard                # Show dashboard summary
hs journal list             # List journal entries
hs journal create           # Create a new entry
hs metrics list             # List metric types
hs metrics log <type> <val> # Log a metric value
hs metrics trend <type>     # Show recent trend
hs results list             # List exercise types
hs results log <type> <val> # Log a result
hs goals list               # List goals
hs goals create             # Create a goal
```

## API Reference

All endpoints are prefixed with `/api`. Authentication is required for all endpoints except `/api/health` and `/api/auth/status`.

### Auth
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/status` | Check registration and auth state |
| POST | `/api/auth/register` | Begin passkey registration |
| POST | `/api/auth/register/complete` | Complete passkey registration |
| POST | `/api/auth/login` | Begin passkey authentication |
| POST | `/api/auth/login/complete` | Complete passkey authentication |
| POST | `/api/auth/logout` | Invalidate session |

### API Keys
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/keys` | List API keys (metadata only) |
| POST | `/api/keys` | Create new API key |
| DELETE | `/api/keys/{id}` | Revoke an API key |

### Journal
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/journals` | List entries (paginated) |
| GET | `/api/journals/{id}` | Get single entry |
| POST | `/api/journals` | Create entry |
| PUT | `/api/journals/{id}` | Update entry |
| DELETE | `/api/journals/{id}` | Delete entry |

### Metrics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metric-types` | List metric types |
| POST | `/api/metric-types` | Create metric type |
| PUT | `/api/metric-types/{id}` | Update metric type |
| DELETE | `/api/metric-types/{id}` | Delete metric type |
| GET | `/api/metrics` | List metric entries |
| POST | `/api/metrics` | Log a metric entry |
| GET | `/api/metrics/trends/{type_id}` | Get trend data |

### Results
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/exercise-types` | List exercise types |
| POST | `/api/exercise-types` | Create exercise type |
| PUT | `/api/exercise-types/{id}` | Update exercise type |
| DELETE | `/api/exercise-types/{id}` | Delete exercise type |
| GET | `/api/results` | List result entries |
| POST | `/api/results` | Log a result |
| GET | `/api/results/prs/{exercise_type_id}` | PR history |
| GET | `/api/results/trends/{exercise_type_id}` | Trend data |

### Goals
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/goals` | List goals |
| GET | `/api/goals/{id}` | Get goal with progress |
| POST | `/api/goals` | Create goal |
| PUT | `/api/goals/{id}` | Update goal |
| DELETE | `/api/goals/{id}` | Delete goal |

### Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard/summary` | Aggregated overview |

## Security

- **Single-user application** — designed for one person, no multi-tenant support
- **Ports bound to localhost only** (`127.0.0.1`) — not exposed to the network by default
- **CORS** restricted to `http://localhost:3000`
- **Request body size** limited to 1 MB
- **Docker containers** run as non-root with `read_only` filesystem and `no-new-privileges`
- **Error responses** do not expose stack traces when `DEBUG=false`
- **WebAuthn / Passkeys** for passwordless authentication
- **API keys** are bcrypt-hashed and never stored in plaintext

## License

See [LICENSE](LICENSE).
