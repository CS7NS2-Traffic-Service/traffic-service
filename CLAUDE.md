# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

Read PROJECT.md before starting any task. It contains the full system architecture, service
boundaries, event schemas, and coding conventions.

## Running the Stack

```bash
docker compose up --build        # Build and start all services
docker compose up --build api-gateway  # Rebuild a single service
```

Frontend dev server (with hot reload, proxies `/api` to `localhost:8000`):

```bash
cd services/bff/traffic-frontend
npm install
npm run dev
```

Frontend lint and build:

```bash
npm run lint    # ESLint
npm run build   # TypeScript check + Vite build
```

## Architecture

```
Client
  │
  ▼
API Gateway (FastAPI :8000)          services/api-gateway/src/main.py
  ├── /api/{service}/* ──► SERVICE_{NAME} env var (dynamic routing)
  └── /*              ──► BFF (FastAPI :8080)     services/bff/src/main.py
                               └── serves compiled React SPA
```

**API Gateway** — reverse proxy only. No business logic. Reads `SERVICE_<NAME>=http://host:port` env
vars to route `/api/<name>/...` to downstream services. Everything else is forwarded to the BFF.
Uses `httpx.AsyncClient` and `Response` — strips hop-by-hop headers, preserves content-type, returns buffered responses.

**BFF** — serves the compiled React frontend. Mounts `/assets` as a static directory; all other
paths return `index.html` to support client-side routing. The frontend is compiled into the BFF
Docker image at build time (multi-stage: Node 22 → Python 3.13-slim).

**Frontend** — React 19 + TypeScript + Vite + Tailwind CSS. In dev mode (`npm run dev`), Vite
proxies `/api` to `localhost:8000` so the gateway is still used. Built output lands in
`services/bff/traffic-frontend/dist/`.

## Adding a Downstream Service

1. Implement the service and give it a Docker service name (e.g., `traffic-service`)
2. Add it to `docker-compose.yml` with `expose` (no `ports` needed)
3. Add `SERVICE_TRAFFIC: http://traffic-service:<port>` under `api-gateway.environment`

No code changes required in the gateway.

## Database Migrations

Migrations use Alembic, located in `db/migrations/versions/`. The `db-migrate` Docker container runs
`alembic upgrade head` on startup before services start. `env.py` reads the `DATABASE_URL` env var
(set in `docker-compose.yml`), falling back to the URL in `alembic.ini`.

```bash
cd db
alembic revision -m "describe your change"   # Create a new migration
alembic upgrade head                          # Run migrations locally
```

Migration scripts are manual — write `upgrade()` and `downgrade()` functions in the generated file.

## Key Files

| File                                           | Purpose                        |
| ---------------------------------------------- | ------------------------------ |
| `docker-compose.yml`                           | Orchestrates api-gateway + bff |
| `services/api-gateway/src/main.py`             | Proxy routing logic            |
| `services/bff/src/main.py`                     | SPA serving logic              |
| `services/bff/traffic-frontend/vite.config.ts` | Dev proxy config               |
| `services/bff/traffic-frontend/src/`           | React app source               |

## Frontend Conventions

Prefer small, focused components that are easy to manage. Extract logical pieces into subcomponents
rather than building large monolithic ones.

**Vite 8 / Rolldown chunking** — Vite 8 uses Rolldown which splits vendor deps into many small chunks
by default. Behind a reverse proxy this causes too many concurrent requests and page freezes. Keep
`manualChunks` in `vite.config.ts` to consolidate all `node_modules` into a single vendor chunk:

```ts
build: {
  rollupOptions: {
    output: {
      manualChunks(id) {
        if (id.includes('node_modules')) return 'vendor'
      },
    },
  },
},
```

**Lazy-load heavy routes** — `BookRoutePage` imports mapbox-gl (~2MB vendor bundle). Keep it
lazy-loaded in `App.tsx` so it doesn't block initial page load:

```tsx
const BookRoutePage = lazy(() => import('./pages/BookRoute/BookRoutePage'))
```

**Browser extensions on deployed URLs** — Grammarly's MutationObserver fights with React's DOM
reconciliation on non-localhost URLs (extensions are disabled on localhost). No website-side fix —
disable Grammarly for the deployed domain via the extension settings, or use incognito for demos.

## Cross-Service Foreign Keys

Each service has its own `declarative_base()`. SQLAlchemy cannot resolve `ForeignKey('other_table.id')`
if the target table belongs to a different service's metadata registry. **Never use `ForeignKey(...)` in
SQLAlchemy models for columns that reference tables owned by another service.** Just declare the column
type (e.g. `mapped_column(UUID(as_uuid=True), nullable=False)`). The actual DB-level FK constraints are
created by Alembic migrations and still enforce referential integrity at the database level.

## Linter Note

FastAPI matches path parameters by name between the URL pattern and the function signature, so names
like `/{full_path:path}` must match the function parameter (`full_path: str`). Do not rename path
parameters without updating both places.

## Pre-commit Hooks

The repo uses **Husky** + **lint-staged** (configured in root `package.json`). On every commit:

- **TypeScript/TSX files** in `services/bff/traffic-frontend/` → ESLint with auto-fix
- **Python files** in `services/*/src/` → `ruff check --fix` + `ruff format`

After cloning, run `npm install` at the repo root to activate the hooks.

## Linting Config

Ruff config lives in `ruff.toml` at the repo root (single source of truth for all Python services).
