# Traffic Booking Service — Technical Documentation

## 1. Project Overview

A globally-accessible distributed traffic booking service where drivers must pre-book every journey
before starting it. No driver may begin a journey without receiving an approval notification. The
system supports millions of concurrent users worldwide.

**Core Architectural Principle:**

- **External communication** (client → system) is **synchronous** via REST/HTTP
- **Internal communication** (service → service) is **asynchronous** via Redis Streams

This separation allows the system to present a simple, predictable API to clients while enabling
loosely-coupled, scalable service-to-service communication internally.

---

## 2. Architecture Overview

### 2.1 Service Inventory

| Service                | Language                    | Database Ownership          | Key Responsibility                                |
| ---------------------- | --------------------------- | --------------------------- | ------------------------------------------------- |
| **API Gateway**        | Python (FastAPI)            | None                        | Reverse proxy, JWT validation, rate limiting      |
| **BFF**                | Python (FastAPI) + React 19 | None                        | Serves compiled React SPA                         |
| **Driver Service**     | Python (FastAPI)            | `drivers`                   | Driver registration, authentication, JWT issuance |
| **Booking Service**    | Go (chi)                    | `bookings`, `outbox_events` | Booking lifecycle, event orchestration            |
| **Route Service**      | Python (FastAPI)            | `routes`, `road_segments`   | Route lookup, OSRM integration                    |
| **Conflict Detection** | Python (FastAPI)            | `segment_reservations`      | Road segment capacity checking                    |
| **Messaging Service**  | Python (FastAPI)            | `messages`                  | Driver inbox, notification persistence            |

### 2.2 Communication Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌──────────────┐
│ API Gateway  │──► JWT validation, rate limiting
└──────┬───────┘
       │
       ├──► /api/driver/* ──► Driver Service
       ├──► /api/booking/* ──► Booking Service (Go)
       ├──► /api/routes/* ──► Route Service
       ├──► /api/conflict-detection/* ──► Conflict Detection Service
       ├──► /api/messaging/* ──► Messaging Service
       │
       └──► /* ──► BFF ──► React SPA
```

### 2.3 Async Event Flow

```
Booking Service
    │
    ▼ (booking.created)
Redis Stream
    │
    ▼
Conflict Detection Service
    │
    ▼ (route.assessed)
Redis Stream
    │
    ▼
Booking Service ──► updates status
    │
    ▼ (booking.updated)
Redis Stream
    │
    ├──► Conflict Detection ──► releases reservations
    │
    └──► Messaging Service ──► creates notification
```

---

## 3. Services

### 3.1 API Gateway

The API Gateway is the single entry point for all client requests. It performs no business logic —
its sole purpose is routing and security enforcement.

**Responsibilities:**

- JWT token validation on every authenticated request
- Rate limiting: 100 requests per driver per minute (Redis-based)
- Dynamic routing to downstream services via `SERVICE_*` environment variables
- Public path whitelist: `/api/driver/auth/login`, `/api/driver/auth/register`, `/health`

**Key Design:**

- Reads `SERVICE_<NAME>` env vars to route `/api/<name>/*` to downstream services
- Injects `X-Driver-ID` header after token verification
- Fail-open rate limiting: if Redis is unavailable, requests pass through

### 3.2 BFF (Backend for Frontend)

The BFF serves the compiled React single-page application and proxies API requests during
development.

**Responsibilities:**

- Serves static React SPA at all non-API paths
- Mounts `/assets` for compiled frontend assets
- In development: Vite proxies `/api` to `localhost:8000`

**Frontend Pages:** | Path | Purpose | |------|---------| | `/login` | Driver login | | `/register`
| Driver registration | | `/routes` | Browse routes with Mapbox map, segment capacity overlay | |
`/bookings` | Submit bookings, view status | | `/inbox` | Driver message inbox | | `/dashboard` |
Admin view with live health and booking throughput |

### 3.3 Driver Service

Handles driver identity and authentication.

**Endpoints:**

- `POST /auth/register` — create account, return JWT
- `POST /auth/login` — verify credentials, return JWT
- `GET /drivers/me` — return current driver profile

**Key Design:**

- Passwords hashed with bcrypt
- JWT signed with `HS256`, 24-hour expiry
- Email uniqueness enforced at database level

### 3.4 Booking Service

Written in Go to demonstrate polyglot architecture. Orchestrates the booking lifecycle using the
Transactional Outbox pattern.

**Endpoints:**

- `POST /bookings` — create booking, returns immediately (202 Accepted)
- `GET /bookings` — list driver's bookings
- `GET /bookings/{id}` — get booking status
- `DELETE /bookings/{id}` — cancel booking

**Key Design — Transactional Outbox:** Rather than publishing events directly to Redis Streams
(which risks losing events if the service crashes after DB commit but before Redis write), the
Booking Service:

1. Writes events to an `outbox_events` table in the same transaction as the booking change
2. A background relay polls the outbox table every 500ms
3. The relay publishes events to Redis Streams and marks them as published

This guarantees at-least-once delivery with exactly-once processing downstream (via idempotency
tracking).

**Booking State Machine:**

```
PENDING ──► APPROVED  (route.assessed: segments_available = true)
PENDING ──► REJECTED  (route.assessed: segments_available = false)
PENDING ──► EXPIRED   (departure_time passed, background expiry loop)
APPROVED ─► CANCELLED (driver cancels)
```

**Expiry Loop:** A background goroutine runs every 30 seconds to expire bookings past their
departure time.

### 3.5 Route Service

Manages route computation and road segment data.

**Endpoints:**

- `GET /routes?origin_lat=X&origin_lng=Y&dest_lat=Z&dest_lng=W` — find or compute route
- `GET /routes/{id}` — get route with geometry
- `GET /routes/{id}/segments` — get ordered segment list

**Key Design:**

- Routes cached by origin/destination coordinates
- Integrates with OSRM (Open Source Routing Machine) for routing calculations
- Extracts OSM way IDs from OSRM response and maps them to internal segment IDs
- Road segment data seeded via Overpass API import

**OSRM Integration:**

- Route Service queries OSRM internally via HTTP
- OSRM returns route geometry (GeoJSON) and ordered OSM way IDs
- Route Service stores computed routes for reuse

### 3.6 Conflict Detection Service

Ensures road segments are not overbooked.

**Events Consumed:**

- `booking.created` — checks capacity, creates reservations, publishes `route.assessed`
- `booking.updated` (CANCELLED/EXPIRED) — releases reservations

**Key Design — Concurrent Booking Prevention:** Uses `SELECT ... FOR UPDATE` to lock segment rows
during capacity checking. This prevents race conditions where two drivers book the same slot
simultaneously.

**Capacity Checking Logic:** For each segment on the route:

1. Count existing reservations with overlapping time windows
2. Compare against segment capacity
3. If any segment is full, reject the booking

**Redis Caching:**

- Segment capacity cached with 30-second TTL
- Fallback to database query if Redis is unavailable

### 3.7 Messaging Service

Persists notifications for drivers based on booking status changes.

**Endpoints:**

- `GET /messages` — list messages for driver
- `PUT /messages/{id}/read` — mark as read

**Key Design:**

- Consumes `booking.updated` events
- Creates human-readable messages per status (APPROVED/REJECTED/CANCELLED/EXPIRED)
- Idempotent via `processed_events` table

---

## 4. Event System (Redis Streams)

### 4.1 Event Types

| Event             | Producer           | Consumer                      | Purpose                    |
| ----------------- | ------------------ | ----------------------------- | -------------------------- |
| `booking.created` | Booking Service    | Conflict Detection            | Trigger capacity check     |
| `route.assessed`  | Conflict Detection | Booking Service               | Report availability result |
| `booking.updated` | Booking Service    | Conflict Detection, Messaging | Status change notification |

### 4.2 Consumer Patterns

**Consumer Groups:** All consumers use Redis Streams consumer groups (`XREADGROUP`) to:

- Distribute load across multiple instances of the same service
- Track which messages have been acknowledged

**Idempotency:** Each consumer service maintains a `processed_events` table. Before processing, it
checks if the event has been seen. After processing, it records the event ID.

**Dead Letter Queues:** Failed messages (after 3 retries) are moved to `{stream}.dlq` for manual
inspection and replay.

### 4.3 Event Envelope

```json
{
  "event_id": "uuid",
  "correlation_id": "uuid",
  "event_type": "booking.created",
  "created_at": "ISO8601",
  "data": {
    /* event-specific payload */
  }
}
```

Correlation IDs enable tracing requests across services.

---

## 5. Database

### 5.1 Shared PostgreSQL

All services share one PostgreSQL instance with logically isolated schemas. Each service has its own
SQLAlchemy `declarative_base()` or Go model definitions.

**Rationale:** Simplifies infrastructure while maintaining logical service boundaries.

### 5.2 Migration Strategy

Alembic manages schema versions in `db/migrations/versions/`. A dedicated `db-migrate` container
runs `alembic upgrade head` on startup before any application service starts.

### 5.3 Cross-Service References

SQLAlchemy cannot resolve `ForeignKey()` references across different model registries. Therefore:

- Cross-service FKs are declared as plain typed columns (e.g., `UUID`)
- Database-level constraints are created by Alembic migrations

### 5.4 Key Tables

| Table                  | Owner              | Purpose                  |
| ---------------------- | ------------------ | ------------------------ |
| `drivers`              | Driver Service     | Driver profiles          |
| `bookings`             | Booking Service    | Booking records          |
| `routes`               | Route Service      | Cached routes            |
| `road_segments`        | Route Service      | Road segment definitions |
| `segment_reservations` | Conflict Detection | Capacity tracking        |
| `messages`             | Messaging Service  | Driver notifications     |
| `outbox_events`        | Booking Service    | Transactional outbox     |
| `processed_events`     | All consumers      | Idempotency tracking     |

---

## 6. Infrastructure

### 6.1 Docker Compose

| Service            | Port | Purpose              |
| ------------------ | ---- | -------------------- |
| api-gateway        | 8000 | External entry point |
| bff                | 8080 | Frontend serving     |
| driver-service     | 8081 | Authentication       |
| booking-service    | 8082 | Booking lifecycle    |
| routes-service     | 8083 | Route management     |
| conflict-detection | 8084 | Capacity checking    |
| messaging-service  | 8085 | Notifications        |
| postgres           | 5432 | Database             |
| redis              | 6379 | Streams + caching    |
| osrm               | 5555 | Routing engine       |
| pgadmin            | 5050 | PostgreSQL UI        |
| redisinsight       | 5540 | Redis UI             |

### 6.2 Kubernetes Deployment

Helm chart in `charts/` manages Kubernetes manifests. Key features:

- **Replicas:** 2+ per service for availability
- **Init Containers:** Wait for database migrations before starting
- **Liveness/Readiness Probes:** Health endpoints for orchestration
- **CloudNativePG:** Manages PostgreSQL replication and failover
- **NodePort:** API Gateway exposed on port 30080

### 6.3 CI/CD

GitHub Actions rebuilds and pushes only services whose source files changed. Images stored in GitHub
Container Registry (ghcr.io).

---

## 7. Security

### 7.1 Authentication

- JWT tokens signed with HS256
- 24-hour token expiry
- `sub` claim contains driver ID

### 7.2 Authorization Flow

```
Client ──► API Gateway (validates JWT) ──► X-Driver-ID header injected ──► Downstream services
```

### 7.3 Rate Limiting

- Redis-based counter per driver ID
- 100 requests per minute
- Fail-open: if Redis unavailable, requests pass through

### 7.4 Password Security

- bcrypt hashing with salt
- No plaintext password storage

---

## 8. Resilience Patterns

### 8.1 Replication

Kubernetes ensures 2+ replicas per service. If a pod fails, Kubernetes automatically restarts it.

### 8.2 Failure Handling

| Component       | Failure      | Behavior                                                        |
| --------------- | ------------ | --------------------------------------------------------------- |
| Redis           | Unavailable  | Rate limiting fails open; conflict detection falls back to DB   |
| Service replica | Crashed      | Kubernetes restarts; events resume from consumer group position |
| PostgreSQL      | Primary down | CloudNativePG promotes replica                                  |
| Booking Service | Crashed      | Events queue in Redis Streams; resume on restart                |

### 8.3 Transaction Isolation

Conflict Detection uses `SELECT FOR UPDATE` to prevent double-booking of the same segment slot.

### 8.4 Graceful Shutdown

All services handle SIGTERM for graceful shutdown:

- Stop accepting new requests
- Complete in-flight requests
- Close database and Redis connections

---

## 9. Testing

### 9.1 E2E Tests (Playwright)

Browser-based tests validate the full user journey:

- Registration and login flows
- Booking creation and cancellation
- Message notification delivery

Tests run via `npm test` in `e2e-tests/` against the running docker-compose stack.

### 9.2 Pre-commit Hooks

Husky + lint-staged enforce code quality on every commit:

- Python files: Ruff (lint + format)
- TypeScript files: ESLint

### 9.3 Test Reports

Playwright records traces, screenshots, and videos for every test run. Viewable via
`npm run report`.

---

## 10. Project Checklist Alignment

This documentation covers the following areas from the submission checklist:

### Overall Architecture

- Services for drivers (booking, routes, messaging)
- Requirements: performance (async events), scalability (microservices), availability (replication),
  reliability (idempotency, outbox), data consistency (transactions), data durability (PostgreSQL)

### Techniques

- **Replication:** Kubernetes replicas, CloudNativePG for PostgreSQL
- **Transactions:** `SELECT FOR UPDATE` isolation for capacity checking
- **Caching:** Redis for rate limiting and segment capacity
- **Load Balancing:** Kubernetes Service layer

### Request Handling

- Concurrent requests synchronized via Redis Streams consumer groups
- No double-spending: `SELECT FOR UPDATE` prevents concurrent booking conflicts

### Failure Handling

- Node failures: Kubernetes restarts replicas
- Communication failures: Redis queues events for retry
- Consistency: Transactional outbox guarantees event delivery

### Other Features

- Playwright E2E testing framework
- React SPA with Mapbox visualization

### Middleware

- API Gateway: reverse proxy, JWT validation, rate limiting
- Redis Streams: event messaging middleware
