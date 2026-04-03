# Traffic Service

A distributed traffic service built with a microservices architecture, using FastAPI, React, and
PostgreSQL.

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

| Service                        | Purpose                                                        | Tech                                                   |
| ------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------ |
| **API Gateway**                | Reverse proxy, JWT validation, rate limiting                   | FastAPI, httpx, Redis                                  |
| **BFF**                        | Serves the compiled React frontend                             | FastAPI                                                |
| **Driver Service**             | Driver registration and authentication (JWT)                   | FastAPI, SQLAlchemy                                    |
| **Booking Service**            | Booking lifecycle, publishes/consumes events via Redis Streams | FastAPI, SQLAlchemy, Redis Streams                     |
| **Routes Service**             | Route lookup/computation, road segment management              | FastAPI, SQLAlchemy, OSRM                              |
| **Conflict Detection Service** | Road segment capacity checking, segment reservations           | FastAPI, SQLAlchemy, Redis Streams                     |
| **Messaging Service**          | Driver inbox, persists notifications from booking events       | FastAPI, SQLAlchemy, Redis Streams                     |
| **Frontend**                   | Single-page application                                        | React 19, TypeScript, Vite, Tailwind CSS, Mapbox GL JS |

**Infrastructure:**

| Component        | Purpose                                                             | Port  |
| ---------------- | ------------------------------------------------------------------- | ----- |
| **PostgreSQL**   | Persistent storage (shared, one DB, logically isolated per service) | :5432 |
| **Redis**        | Event streaming (Redis Streams) and caching                         | :6379 |
| **OSRM**         | Route computation engine (used by Routes Service)                   | :5000 |
| **pgAdmin**      | PostgreSQL web UI                                                   | :5050 |
| **RedisInsight** | Redis web UI (streams, keys, consumer groups)                       | :5540 |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 22+](https://nodejs.org/) (for frontend dev and git hooks)
- [uv](https://docs.astral.sh/uv/) (Python package manager, used by all services)
- [Ruff](https://docs.astral.sh/ruff/) (Python linter/formatter)
- A [Mapbox](https://www.mapbox.com/) access token (free tier, for map rendering)
- [minikube](https://minikube.sigs.k8s.io/) and [kubectl](https://kubernetes.io/docs/tasks/tools/) (for Kubernetes deployment)
- [Helm](https://helm.sh/) (for Kubernetes chart management)

## Getting Started

### 1. Set environment variables

Add a .env file in the root of the project and set the MAPBOX_TOKEN

```.env
MAPBOX_TOKEN=your-mapbox-token
```

The token is passed to the BFF at Docker build time for the frontend map. Without it, the map will
not render.

### 2. Install git hooks

```bash
npm install
```

This installs [Husky](https://typicode.github.io/husky/) pre-commit hooks that automatically lint
and format staged files on every commit.

### 3. Start the full stack

```bash
docker compose up --build
```

This starts all services, PostgreSQL (:5432), Redis (:6379), OSRM (:5000), pgAdmin (:5050),
RedisInsight (:5540), and runs database migrations.

### 4. Frontend development (with hot reload)

```bash
cd services/bff/traffic-frontend
npm install
npm run dev
```

The Vite dev server starts on `http://localhost:5173` and proxies `/api` requests to the API gateway
at `localhost:8000`.

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

Migrations use [Alembic](https://alembic.sqlalchemy.org/) and live in `db/migrations/versions/`. A
dedicated `db-migrate` container runs `alembic upgrade head` on startup (before any service that
depends on it).

### Creating a new migration

```bash
cd db
alembic revision -m "describe your change"
```

This creates a new file in `db/migrations/versions/`. Edit the generated `upgrade()` and
`downgrade()` functions to define your schema change.

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

| File                      | Purpose                                                    |
| ------------------------- | ---------------------------------------------------------- |
| `db/alembic.ini`          | Alembic config (default DB URL, migration script location) |
| `db/migrations/env.py`    | Reads `DATABASE_URL` env var, falls back to `alembic.ini`  |
| `db/migrations/versions/` | Migration scripts (one per schema change)                  |

## E2E Testing

End-to-end tests use [Playwright](https://playwright.dev/) and live in `e2e-tests/`. They test the
full stack through the browser — from the React frontend through the API Gateway to all downstream
services and the database.

Traces, screenshots, and videos are recorded for every test run and can be viewed in the Playwright
HTML report.

### Running the tests

The full docker-compose stack must be running before executing tests:

```bash
docker compose up --build -d
```

Then run the tests:

```bash
cd e2e-tests
npm test
```

### Viewing traces

After a run, open the HTML report:

```bash
cd e2e-tests
npm run report
```

This opens the Playwright trace viewer in your browser. Click any test to see a timeline of every
action, screenshot at each step, and all network requests made during that test.

### Test structure

```
e2e-tests/
├── playwright.config.ts   # baseURL, trace/screenshot/video settings
└── tests/
    ├── auth/              # Registration and login flows
    ├── bookings/          # Booking lifecycle tests
    └── inbox/             # Notification tests
```

### Strategy

| Test type | Tool | Purpose |
| --------- | ---- | ------- |
| UI flows (register, login, book route) | Browser | Validates the full user journey through the UI |
| Concurrent bookings / conflict detection | API (`request` fixture) | Precise control over parallel requests without browser overhead |

Tests are not run on every commit (the stack is too heavy for pre-commit hooks). They run on
pre-push or in CI.

## Kubernetes Deployment

The application can be deployed to a Kubernetes cluster using a Helm chart located in `charts/`.

### Architecture

All services run as Kubernetes Deployments with ClusterIP Services for internal communication. The
API Gateway is the only service exposed externally via NodePort on port `30080`. Shared configuration
(database URL, Redis URL, JWT secret) is managed through a single ConfigMap (`traffic-config`).

```
charts/
├── Chart.yaml
└── templates/
    ├── configmap.yaml                    # Shared env vars for all services
    ├── api-gateway/                      # NodePort :30080 (external entry point)
    ├── bff/                              # ClusterIP :8080
    ├── driver-service/                   # ClusterIP :8081
    ├── booking-service/                  # ClusterIP :8082
    ├── routes-service/                   # ClusterIP :8083
    ├── conflict-detection-service/       # ClusterIP :8084
    ├── messaging-service/                # ClusterIP :8085
    ├── postgres/                         # ClusterIP :5432 + PersistentVolumeClaim
    ├── redis/                            # ClusterIP :6379
    ├── osrm/                             # ClusterIP :5000
    ├── migrations/                       # Job (runs Alembic migrations)
    └── admin/
        ├── pgadmin/                      # ClusterIP :80
        └── redisinsight/                 # ClusterIP :5540
```

Each application service includes:
- A liveness probe on `/health` (Kubernetes restarts the pod if it fails)
- A readiness probe on `/health` (Kubernetes stops routing traffic until the pod is ready)
- An init container that waits for database migrations to complete before starting

### Prerequisites

1. Start minikube:

```bash
minikube start
```

2. Point your Docker CLI at minikube's Docker daemon:

```bash
eval $(minikube docker-env)
```

All `docker build` commands in the steps below must run in a shell where this eval has been executed,
otherwise the images will be built into your local daemon and minikube won't be able to find them.

### Build images

Build all service images into minikube's Docker daemon:

```bash
docker build -t api-gateway:latest services/api-gateway/
docker build -t bff:latest --build-arg VITE_MAPBOX_TOKEN=$MAPBOX_TOKEN services/bff/
docker build -t driver-service:latest services/driver-service/
docker build -t booking-service:latest services/booking-service/
docker build -t routes-service:latest services/routes-service/
docker build -t conflict-detection-service:latest services/conflict-detection-service/
docker build -t messaging-service:latest services/messaging-service/
docker build -t db-migrate:latest db/
docker build -t osrm-ireland:latest osrm-data/
```

All images use `imagePullPolicy: Never` so Kubernetes uses the locally built images instead of
trying to pull from a registry.

### Deploy

```bash
helm install traffic-service ./charts
```

Watch pods come up:

```bash
kubectl get pods -w
```

The startup order is handled by init containers:
1. Postgres starts first
2. The `db-migrate` Job waits for Postgres, then runs Alembic migrations
3. All application services wait for migrations to complete, then start

### Access the application

On macOS the minikube IP is not directly reachable from the host. Use the built-in tunnel:

```bash
minikube service api-gateway
```

This opens the API Gateway in your browser automatically.

### Access admin tools

pgAdmin and RedisInsight are internal services. Access them via port-forwarding:

```bash
kubectl port-forward deployment/pgadmin 8888:80
kubectl port-forward deployment/redisinsight 5540:5540
```

- pgAdmin: `http://localhost:8888` (login: `admin@admin.com` / `admin`)
- RedisInsight: `http://localhost:5540` (connect to `redis://redis:6379`)

### Updating after code changes

After modifying a service, rebuild its image and restart the deployment:

```bash
eval $(minikube docker-env)
docker build -t <service-name>:latest services/<service-name>/
kubectl rollout restart deployment/<service-name>
```

Since all images use the `latest` tag, Kubernetes won't detect a change automatically.
`rollout restart` forces the pods to recreate with the new image.

### Tear down

```bash
helm uninstall traffic-service
kubectl delete pvc --all
```

`helm uninstall` removes all resources except PersistentVolumeClaims (to prevent accidental data
loss). Delete PVCs separately to fully clean up.

## Adding a New Service

1. Create the service under `services/<name>/`
2. Add it to `docker-compose.yml` with `expose` (no `ports` needed)
3. Add `SERVICE_<NAME>: http://<service>:<port>` under `api-gateway.environment`

The API gateway automatically routes `/api/<name>/*` to the service — no code changes needed.
