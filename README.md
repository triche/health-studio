# Health Studio

A local-first personal health dashboard, journal, and tracker. Consolidates mental and physical health management into a single, self-hosted web application deployed via Docker.

## Quick Start

```bash
docker compose up
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health check**: http://localhost:8000/api/health

## Development

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest -v
ruff check .
```

### Frontend

```bash
cd frontend
npm install
npm run dev
npm test
npm run lint
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript + Vite |
| UI | Tailwind CSS |
| Backend | Python + FastAPI |
| Database | SQLite (via SQLAlchemy) |
| Auth | WebAuthn / Passkeys |
| Containerization | Docker + Docker Compose |

## Security Notes

- **Single-user application** — designed for one person, no multi-tenant support
- **Ports bound to localhost only** (`127.0.0.1`) — not exposed to the network by default
- **CORS** restricted to `http://localhost:3000`
- **Request body size** limited to 1 MB
- **Docker containers** run as non-root with `read_only` filesystem and `no-new-privileges`
- **Error responses** do not expose stack traces when `DEBUG=false`
- **WebAuthn / Passkeys** for passwordless authentication (Phase 7)
- **API keys** are bcrypt-hashed and never stored in plaintext

## License

See [LICENSE](LICENSE).
