# AGENTS.md

This file provides guidance for agentic coding agents operating in this repository.

## Build, Lint, and Test Commands

### Full Stack (Docker)
```bash
docker compose up --build                    # Build and start all services
docker compose up --build <service-name>    # Rebuild a single service
```

### Frontend (React + TypeScript + Vite)
```bash
cd services/bff/traffic-frontend
npm install                                 # Install dependencies
npm run dev                                 # Dev server with hot reload
npm run build                               # TypeScript check + Vite build
npm run lint                                # ESLint
npm run lint --fix                          # ESLint with auto-fix
npm run test                                # Run all tests (Vitest)
npm run test -- <test-file>                 # Run single test file
npm run test -- --run                       # Run tests (alias for vitest run)
```

### E2E Tests (Playwright)
```bash
cd e2e-tests
npm install
npm run test                                # Run all e2e tests
npm run test:headed                         # Run with browser visible
npm run test -- --project=chromium          # Run specific browser
```

### Python Services (FastAPI)
```bash
# Linting (all Python services)
ruff check --fix --config ruff.toml
ruff format --config ruff.toml

# Run a single service locally
cd services/<service-name>
uvicorn src.main:app --reload --port 8000

# Database migrations
cd db
alembic revision -m "describe your change"   # Create migration
alembic upgrade head                         # Run migrations
```

## Code Style Guidelines

### Python

**Imports**
- Standard library first, then third-party, then local
- Use absolute imports (e.g., `from infrastructure.database import get_db`)
- Group with blank lines between groups

**Formatting**
- Line length: 88 characters (from ruff.toml)
- Use single quotes for strings
- Run `ruff format` before committing

**Types**
- Use type hints for all function parameters and return types
- Prefer `str | None` over `Optional[str]`
- Use dataclasses for simple domain objects

**Naming**
- `snake_case` for functions, variables, and modules
- `PascalCase` for classes and dataclasses
- Prefix private functions with `_`

**Error Handling**
- Use custom exceptions with meaningful names
- Return appropriate HTTP status codes in FastAPI endpoints
- Log errors with appropriate severity before re-raising

**FastAPI Patterns**
- Use `Depends()` in route function parameters (don't disable B008)
- Match path parameter names between URL pattern and function signature

### TypeScript/JavaScript

**Imports**
- Use path aliases: `@/` maps to `./src/`
- Order: React imports, then third-party, then local components/utils

**Formatting**
- ESLint handles formatting
- Use `@/` alias for absolute imports

**Types**
- Prefer explicit types over `any`
- Use interfaces for object shapes, types for unions/intersections

**Naming**
- `camelCase` for variables and functions
- `PascalCase` for components and classes
- `kebab-case` for file names (e.g., `book-route-page.tsx`)

**Components**
- Prefer small, focused components
- Extract logical pieces into subcomponents
- Lazy-load heavy routes (e.g., mapbox-gl)
- Use `manualChunks` in Vite config to consolidate vendor deps

### Database

**Cross-Service Foreign Keys**
- Each service has its own SQLAlchemy `declarative_base()`
- Never use `ForeignKey(...)` for tables owned by other services
- Declare column type directly (e.g., `mapped_column(UUID(as_uuid=True))`)
- Create actual FK constraints via Alembic migrations

### Testing

**Frontend (Vitest)**
- Co-locate tests with components (e.g., `Component.tsx` and `Component.test.tsx`)
- Use `@testing-library/react` for component testing

**E2E (Playwright)**
- Tests go in `e2e-tests/tests/`
- Use descriptive test names

### Pre-commit Hooks

The repo uses Husky + lint-staged. After cloning, run:
```bash
npm install
```

On every commit:
- TypeScript/TSX files → ESLint with auto-fix
- Python files → `ruff check --fix` + `ruff format`

### Key Architecture Patterns

**API Gateway** - Reverse proxy only. Reads `SERVICE_<NAME>` env vars to route `/api/<name>/*` to downstream services. No business logic.

**BFF** - Serves compiled React SPA. Mounts `/assets` as static. All other routes return `index.html` for client-side routing.

**Service Communication** - Services communicate via HTTP through the API gateway. Avoid direct service-to-service calls.

### Relevant Documentation

- See `CLAUDE.md` for detailed architecture and system design
- See `PROJECT.md` for event schemas and service boundaries
