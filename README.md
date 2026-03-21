# Traffic Service

A distributed traffic service built with a microservices architecture, using FastAPI, React, and PostgreSQL.

## Architecture

```
Client (:5173 dev / :8000 prod)
  │
  ▼
API Gateway (FastAPI :8000)
  ├── /api/driver/*              ──► Driver Service (:8081)
  ├── /api/booking/*             ──► Booking Service (:8082)
  ├── /api/routes/*              ──► Routes Service (:8083)
  ├── /api/conflict-detection/*  ──► Conflict Detection Service (:8084)
  ├── /api/messaging/*           ──► Messaging Service (:8085)
  └── /*                         ──► BFF (:8080) ──► React SPA
```

**Services:**

| Service | Purpose | Tech |
|---|---|---|
| **API Gateway** | Reverse proxy, JWT validation, rate limiting | FastAPI, httpx, Redis |
| **BFF** | Serves the compiled React frontend | FastAPI |
| **Driver Service** | Driver registration and authentication (JWT) | FastAPI, SQLAlchemy |
| **Booking Service** | Booking lifecycle, publishes/consumes events via Redis Streams | FastAPI, SQLAlchemy, Redis Streams |
| **Routes Service** | Route lookup/computation, road segment management | FastAPI, SQLAlchemy, OSRM |
| **Conflict Detection Service** | Road segment capacity checking, segment reservations | FastAPI, SQLAlchemy, Redis Streams |
| **Messaging Service** | Driver inbox, persists notifications from booking events | FastAPI, SQLAlchemy, Redis Streams |
| **Frontend** | Single-page application | React 19, TypeScript, Vite, Tailwind CSS, Mapbox GL JS |

**Infrastructure:**

| Component | Purpose | Port |
|---|---|---|
| **PostgreSQL** | Persistent storage (shared, one DB, logically isolated per service) | :5432 |
| **Redis** | Event streaming (Redis Streams) and caching | :6379 |
| **OSRM** | Route computation engine (used by Routes Service) | :5000 |
| **pgAdmin** | PostgreSQL web UI | :5050 |
| **RedisInsight** | Redis web UI (streams, keys, consumer groups) | :5540 |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 22+](https://nodejs.org/) (for frontend dev and git hooks)
- [uv](https://docs.astral.sh/uv/) (Python package manager, used by all services)
- [Ruff](https://docs.astral.sh/ruff/) (Python linter/formatter)
- A [Mapbox](https://www.mapbox.com/) access token (free tier, for map rendering)

## Getting Started

### 1. Set environment variables

```bash
# macOS / Linux
export MAPBOX_TOKEN=your-mapbox-token

# Windows (PowerShell)
$env:MAPBOX_TOKEN="your-mapbox-token"
```

The token is passed to the BFF at Docker build time for the frontend map. Without it, the map will not render.

### 2. Install git hooks

```bash
npm install
```

This installs [Husky](https://typicode.github.io/husky/) pre-commit hooks that automatically lint and format staged files on every commit.

### 3. Start the full stack

```bash
docker compose up --build
```

This starts all services, PostgreSQL (:5432), Redis (:6379), OSRM (:5000), pgAdmin (:5050), RedisInsight (:5540), and runs database migrations.

### 4. Frontend development (with hot reload)

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
│   ├── driver-service/             # Driver auth service
│   ├── booking-service/            # Booking management
│   ├── routes-service/             # Route management
│   ├── conflict-detection-service/ # Conflict detection
│   └── messaging-service/          # Messaging
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

## Database Migrations

Migrations use [Alembic](https://alembic.sqlalchemy.org/) and live in `db/migrations/versions/`. A dedicated `db-migrate` container runs `alembic upgrade head` on startup (before any service that depends on it).

### Creating a new migration

```bash
cd db
alembic revision -m "describe your change"
```

This creates a new file in `db/migrations/versions/`. Edit the generated `upgrade()` and `downgrade()` functions to define your schema change.

### Running migrations manually

```bash
# Via Docker (uses DATABASE_URL from docker-compose.yml)
docker compose up db-migrate

# Locally (requires PostgreSQL running on localhost:5432)
cd db
pip install alembic psycopg2-binary
alembic upgrade head
```

### Key files

| File | Purpose |
|---|---|
| `db/alembic.ini` | Alembic config (default DB URL, migration script location) |
| `db/migrations/env.py` | Reads `DATABASE_URL` env var, falls back to `alembic.ini` |
| `db/migrations/versions/` | Migration scripts (one per schema change) |

## Adding a New Service

1. Create the service under `services/<name>/`
2. Add it to `docker-compose.yml` with `expose` (no `ports` needed)
3. Add `SERVICE_<NAME>: http://<service>:<port>` under `api-gateway.environment`

The API gateway automatically routes `/api/<name>/*` to the service — no code changes needed.
