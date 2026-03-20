# Traffic Service

A distributed traffic service built with a microservices architecture, using FastAPI, React, and PostgreSQL.

## Architecture

```
Client (:5173 dev / :8000 prod)
  │
  ▼
API Gateway (FastAPI :8000)
  ├── /api/driver/* ──► Driver Service (:8081)
  └── /*            ──► BFF (:8080) ──► React SPA
```

| Service | Purpose | Tech |
|---|---|---|
| **API Gateway** | Reverse proxy, routes `/api/<service>/*` to downstream services | FastAPI, httpx |
| **BFF** | Serves the compiled React frontend | FastAPI |
| **Driver Service** | Driver registration and authentication (JWT) | FastAPI, SQLAlchemy |
| **Frontend** | Single-page application | React 19, TypeScript, Vite, Tailwind CSS |
| **PostgreSQL** | Persistent storage | PostgreSQL 17 |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 22+](https://nodejs.org/) (for frontend dev and git hooks)
- [uv](https://docs.astral.sh/uv/) (Python package manager, used by all services)
- [Ruff](https://docs.astral.sh/ruff/) (Python linter/formatter)

## Getting Started

### 1. Install git hooks

```bash
npm install
```

This installs [Husky](https://typicode.github.io/husky/) pre-commit hooks that automatically lint and format staged files on every commit.

### 2. Start the full stack

```bash
docker compose up --build
```

This starts the API gateway (:8000), BFF (:8080), driver service (:8081), PostgreSQL (:5432), pgAdmin (:5050), and runs database migrations.

### 3. Frontend development (with hot reload)

```bash
cd services/bff/traffic-frontend
npm install
npm run dev
```

The Vite dev server starts on `http://localhost:5173` and proxies `/api` requests to the API gateway at `localhost:8000`.

## Project Structure

```
├── docker-compose.yml              # Service orchestration
├── ruff.toml                       # Python linter/formatter config (global)
├── package.json                    # Husky + lint-staged config
├── db/
│   └── migrations/                 # Alembic database migrations
├── services/
│   ├── api-gateway/                # Reverse proxy
│   │   └── src/main.py
│   ├── bff/                        # Backend-for-Frontend
│   │   ├── src/main.py
│   │   └── traffic-frontend/       # React SPA
│   │       └── src/
│   │           ├── pages/          # Route pages
│   │           ├── components/     # UI components
│   │           ├── api/            # API client functions
│   │           ├── hooks/          # React Query mutations
│   │           └── stores/         # Zustand state stores
│   └── driver-service/             # Driver auth service
│       └── src/
│           ├── models/             # SQLAlchemy models
│           ├── routes/             # API route handlers
│           └── services/           # Business logic
```

## Linting

Pre-commit hooks run automatically, but you can also lint manually:

```bash
# Run all lint checks (same as pre-commit)
npx lint-staged

# Python — from repo root
ruff check services/            # Lint
ruff format --check services/   # Check formatting
ruff format services/           # Apply formatting

# Frontend — from services/bff/traffic-frontend/
npm run lint                    # ESLint
npm run build                   # TypeScript type check + Vite build
```

## Adding a New Service

1. Create the service under `services/<name>/`
2. Add it to `docker-compose.yml` with `expose` (no `ports` needed)
3. Add `SERVICE_<NAME>: http://<service>:<port>` under `api-gateway.environment`

The API gateway automatically routes `/api/<name>/*` to the service — no code changes needed.
