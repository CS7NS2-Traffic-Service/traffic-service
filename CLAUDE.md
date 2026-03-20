# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**API Gateway** — reverse proxy only. No business logic. Reads `SERVICE_<NAME>=http://host:port` env vars to route `/api/<name>/...` to downstream services. Everything else is forwarded to the BFF. Uses `httpx.AsyncClient` and `StreamingResponse` — headers and body pass through unchanged.

**BFF** — serves the compiled React frontend. Mounts `/assets` as a static directory; all other paths return `index.html` to support client-side routing. The frontend is compiled into the BFF Docker image at build time (multi-stage: Node 22 → Python 3.13-slim).

**Frontend** — React 19 + TypeScript + Vite + Tailwind CSS. In dev mode (`npm run dev`), Vite proxies `/api` to `localhost:8000` so the gateway is still used. Built output lands in `services/bff/traffic-frontend/dist/`.

## Adding a Downstream Service

1. Implement the service and give it a Docker service name (e.g., `traffic-service`)
2. Add it to `docker-compose.yml` with `expose` (no `ports` needed)
3. Add `SERVICE_TRAFFIC: http://traffic-service:<port>` under `api-gateway.environment`

No code changes required in the gateway.

## Key Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Orchestrates api-gateway + bff |
| `services/api-gateway/src/main.py` | Proxy routing logic |
| `services/bff/src/main.py` | SPA serving logic |
| `services/bff/traffic-frontend/vite.config.ts` | Dev proxy config |
| `services/bff/traffic-frontend/src/` | React app source |

## Frontend Conventions

Prefer small, focused components that are easy to manage. Extract logical pieces into subcomponents rather than building large monolithic ones.

## Linter Note

FastAPI matches path parameters by name between the URL pattern and the function signature, so names like `/{full_path:path}` must match the function parameter (`full_path: str`). Do not rename path parameters without updating both places.

## Pre-commit Hooks

The repo uses **Husky** + **lint-staged** (configured in root `package.json`). On every commit:
- **TypeScript/TSX files** in `services/bff/traffic-frontend/` → ESLint with auto-fix
- **Python files** in `services/*/src/` → `ruff check --fix` + `ruff format`

After cloning, run `npm install` at the repo root to activate the hooks.

## Linting Config

Ruff config lives in `ruff.toml` at the repo root (single source of truth for all Python services).
