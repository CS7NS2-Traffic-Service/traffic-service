# Implementation Plan

## Current State

**Implemented:**
- Docker Compose: all 7 services + Postgres + pgAdmin + db-migrate
- API Gateway: reverse proxy routing (no auth, no rate limiting)
- BFF: serves compiled React SPA
- Driver Service: register/login endpoints (has bugs — see below)
- Frontend: login, register, home pages with Zustand auth store
- Database: single migration (drivers table)
- K8s: overlay stubs for dev and demo
- Git hooks: Husky + lint-staged (ruff for Python, ESLint for TS)

**Critical Bugs to Fix First:**
1. Driver migration declares `password` column as `Integer` — must be `String`
2. Driver service stores passwords in plaintext — must use bcrypt
3. Driver model only has `username` — PROJECT.md specifies `name`, `email`, `license_number`, `vehicle_type`, `region`

**Boilerplate Only (no logic beyond `/health`):**
- Booking Service
- Route Service
- Conflict Detection Service
- Messaging Service

---

## Phase 1 — Foundation Fixes

Goal: fix existing bugs and add missing infrastructure so all subsequent work builds on a solid base.

### 1.1 Fix Driver Schema and Migration

- [x] Create new Alembic migration: drop and recreate `drivers` table with correct schema (`b5e8a1c3d7f9`)
  ```
  drivers
  ├── driver_id       UUID PK
  ├── name            TEXT NOT NULL
  ├── email           TEXT UNIQUE NOT NULL
  ├── password_hash   TEXT NOT NULL
  ├── license_number  TEXT NOT NULL
  ├── vehicle_type    TEXT (CAR, MOTORCYCLE, TRUCK, HGV)
  ├── region          TEXT NOT NULL
  └── created_at      TIMESTAMP
  ```
- [x] Update `services/driver-service/src/models/user.py` to match
- [x] Update `services/driver-service/src/schemas.py` with all fields
- [x] Update `services/driver-service/src/services/auth.py` to use bcrypt
- [x] Update `services/driver-service/src/routes/auth.py` to return correct response shape
- [x] Add `GET /drivers/me` endpoint (reads `X-Driver-ID` header)

### 1.2 Add Redis and OSRM to Docker Compose

- [x] Add `redis` service (Redis 7, port 6379, healthcheck)
- [x] Add `REDIS_URL` env var to booking-service, conflict-detection-service, messaging-service, api-gateway
- [x] Add `DATABASE_URL` env var to all database-backed services
- [x] Add `JWT_SECRET_KEY` env var to driver-service and api-gateway
- [x] Add `osrm` service (osrm/osrm-backend, volume mount `osrm-data/`, port 5000, behind `osrm` profile)
- [x] Add `OSRM_URL` env var to routes-service

### 1.3 Add Database Migrations for All Tables

- [x] Migration: `bookings` table (booking_id, driver_id, route_id, departure_time, estimated_arrival, status, created_at, expires_at)
- [x] Migration: `routes` table (route_id, origin, destination, segment_ids, geometry, estimated_duration, created_at)
- [x] Migration: `road_segments` table (segment_id, osm_way_id, name, region, capacity, coordinates)
- [x] Migration: `segment_reservations` table (reservation_id, booking_id, segment_id, time_window_start, time_window_end)
- [x] Migration: `messages` table (message_id, driver_id, booking_id, content, read, created_at)

All five tables created in single migration `a1b2c3d4e5f6`.

### 1.4 Update Frontend for New Driver Schema

- [x] Update `RegisterPage.tsx` to include all fields (name, email, password, license_number, vehicle_type, region)
- [x] Update `LoginPage.tsx` to use email instead of username
- [x] Update `api/auth.ts` request/response types
- [x] Update Zustand driver store to hold full driver profile
- [x] Remove unused `authStore.ts`

---

## Phase 2 — Service Happy Paths

Goal: each service implements its core endpoints and business logic. No inter-service events yet — just REST endpoints that work in isolation.

### 2.1 Booking Service

Files to create: `models/booking.py`, `schemas.py`, `routes/bookings.py`, `services/booking.py`

- [x] SQLAlchemy `Booking` model matching the schema
- [x] Pydantic schemas: `CreateBookingDto`, `BookingResponse`
- [x] `POST /bookings` — create booking with status PENDING, return 202
- [x] `GET /bookings/{booking_id}` — get single booking
- [x] `GET /bookings` — list bookings for driver (from `X-Driver-ID` header)
- [x] `DELETE /bookings/{booking_id}` — cancel booking (set status CANCELLED)
- [x] Register router in `main.py`

### 2.2 Route Service

Files to create: `models/route.py`, `models/road_segment.py`, `schemas.py`, `routes/routes.py`, `services/route.py`, `services/osrm.py`

- [x] SQLAlchemy `Route` model and `RoadSegment` model
- [x] Pydantic schemas: `RouteResponse`, `SegmentResponse`, `RouteQueryParams`
- [x] `GET /routes?origin_lat=&origin_lng=&dest_lat=&dest_lng=` — find or compute route
  - Check existing route for origin/destination pair
  - If not found, query OSRM, map way IDs to segments, store and return
- [x] `GET /routes/{route_id}` — get route with geometry
- [x] `GET /routes/{route_id}/segments` — get ordered segment list with capacity
- [x] OSRM client: `query_route(origin, destination)` → geometry + way IDs
- [x] Register router in `main.py`
- [x] Added `httpx` dependency + updated lockfile

### 2.3 Conflict Detection Service

Files to create: `models/road_segment.py`, `models/segment_reservation.py`, `schemas.py`, `services/conflict.py`

- [x] SQLAlchemy `RoadSegment` and `SegmentReservation` models
- [x] Conflict detection logic:
  - For each segment on a route, count overlapping reservations
  - Compare count against segment capacity
  - Return `segments_available: true/false`
- [x] Reservation creation (transactional — prevent race conditions)
- [x] Reservation deletion (on booking cancellation)
- [x] `assess_and_reserve` with `SELECT ... FOR UPDATE` to prevent double-booking
- [ ] Redis capacity cache (key: `segment:capacity:{segment_id}:{time_window}`, TTL 30s, fallback to DB) — deferred to Phase 3

### 2.4 Messaging Service

Files to create: `models/message.py`, `schemas.py`, `routes/messages.py`, `services/message.py`

- [x] SQLAlchemy `Message` model (with `is_read` mapped to `read` column)
- [x] Pydantic schemas: `MessageResponse`, `MessageListResponse`
- [x] `GET /messages` — list messages for driver (from `X-Driver-ID` header)
- [x] `PUT /messages/{message_id}/read` — mark message as read
- [x] Register router in `main.py`
- [x] `create_message` service function ready for Phase 3 event consumer

---

## Phase 3 — Event Integration (Redis Streams)

Goal: wire up the async event flow so the full booking lifecycle works end-to-end.

### 3.1 Redis Streams Infrastructure

- [x] `events.py` in booking-service and conflict-detection-service with `publish_event(stream, data)` using `redis.xadd()`
- [x] Consumer pattern: `xreadgroup` loop in `consumer.py` per service, started as daemon thread via FastAPI lifespan
- [x] Each consuming service creates its consumer group on startup via `xgroup_create` with `BUSYGROUP` guard

### 3.2 Booking → Conflict Detection (`booking.created`)

- [x] Booking Service: after creating a booking, publish to `booking.created` stream
  ```json
  {"booking_id": "uuid", "driver_id": "uuid", "route_id": "uuid", "departure_time": "ISO8601"}
  ```
- [x] Conflict Detection Service: `consumer.py` — listen on `booking.created`
  - Fetches route from shared `routes` table via read-only Route model
  - Runs `assess_and_reserve` (with `SELECT FOR UPDATE` locking)
  - Publishes `route.assessed` event

### 3.3 Conflict Detection → Booking (`route.assessed`)

- [x] Conflict Detection Service: publish to `route.assessed` stream
  ```json
  {"booking_id": "uuid", "route_id": "uuid", "segments_available": true/false}
  ```
- [x] Booking Service: `consumer.py` — listen on `route.assessed`
  - If `segments_available: true` → set booking status to APPROVED
  - If `segments_available: false` → set booking status to REJECTED
  - Publishes `booking.updated` event

### 3.4 Booking → Messaging (`booking.updated`)

- [x] Booking Service: publish to `booking.updated` stream after status change (approve/reject/cancel)
  ```json
  {"booking_id": "uuid", "driver_id": "uuid", "status": "APPROVED|REJECTED|CANCELLED"}
  ```
- [x] Messaging Service: `consumer.py` — listen on `booking.updated`
  - Creates a message record with human-readable content per status

### 3.5 API Gateway Auth and Rate Limiting

- [x] JWT validation middleware: verify token on all requests except public paths (`POST /api/driver/auth/login`, `POST /api/driver/auth/register`, `GET /health`, non-`/api/` paths)
- [x] Extract `driver_id` from JWT `sub` claim, inject as `X-Driver-ID` header on proxied requests
- [x] Rate limiting: Redis INCR with 60s TTL, 100 req/min per driver, 429 if exceeded, fail-open if Redis down
- [x] Fixed bug: `route_to_service` now returns `JSONResponse` instead of tuple

---

## Phase 4 — Frontend Pages

Goal: build out all remaining frontend pages so the full user journey is usable.

### 4.1 Routes Page (`/routes`)

- [x] Mapbox GL JS map component (`RouteMap.tsx`)
- [x] Origin/destination coordinate inputs
- [x] Fetch route from `GET /api/routes/routes?origin_lat=...`
- [x] Render route geometry as polyline overlay on map (`syncRouteLine()`)
- [x] Color-code road segments by capacity (`utilizationColor()`)
- [x] Display route result and segment list

### 4.2 Bookings Page (`/bookings`)

- [x] Booking creation form: route_id input, departure_time datetime picker
- [x] Submit booking via `POST /api/booking/bookings`
- [x] Display booking list from `GET /api/booking/bookings`
- [x] Show booking status with color-coded badges (PENDING=yellow, APPROVED=green, REJECTED=red, CANCELLED=gray)
- [x] Cancel button → `DELETE /api/booking/bookings/{booking_id}`
- [x] Auto-refresh every 5 seconds via useQuery refetchInterval

### 4.3 Inbox Page (`/inbox`)

- [x] Fetch messages from `GET /api/messaging/messages`
- [x] Display message list with read/unread styling (bold + left border)
- [x] Mark as read on click → `PUT /api/messaging/messages/{message_id}/read`
- [x] Unread count badge in navbar (fetches every 10s)

### 4.4 Dashboard Page (`/dashboard`)

- [x] Booking throughput metrics: total count + per-status cards
- [x] Recent bookings table (last 10)
- [x] Auto-refresh every 5 seconds
- [ ] Service health status polling — deferred

### 4.5 Navigation and Layout

- [x] Update `Navbar.tsx` with authenticated nav links (Routes, Bookings, Inbox, Dashboard)
- [x] Protected routes via `ProtectedRoute` component (redirects to `/login`)
- [x] React Router routes for `/routes`, `/bookings`, `/inbox`, `/dashboard`
- [x] Shared API client helper with auth headers (`api/client.ts`)

---

## Phase 5 — Kubernetes

Goal: deploy the full stack to minikube with proper manifests.

### 5.1 Base Manifests (`k8s/base/`)

For each service, create:
- [ ] `Deployment` (2 replicas, liveness probe on `/health`)
- [ ] `Service` (ClusterIP)
- [ ] `kustomization.yaml` listing all resources

Shared infrastructure:
- [ ] PostgreSQL `StatefulSet` + `Service` + `PersistentVolumeClaim`
- [ ] Redis `Deployment` + `Service`
- [ ] OSRM `Deployment` + `Service` + `PersistentVolumeClaim`
- [ ] db-migrate `Job`
- [ ] `ConfigMap` for shared env vars (DATABASE_URL, REDIS_URL, JWT_SECRET_KEY)
- [ ] API Gateway `Service` with `type: NodePort` (or Ingress)

### 5.2 Dev Overlay (`k8s/overlays/dev/`)

- [ ] 1 replica per service
- [ ] NodePort 30080 for api-gateway
- [ ] Lower resource limits

### 5.3 Demo Overlay (`k8s/overlays/demo/`)

- [ ] 2+ replicas per service
- [ ] Resource requests/limits (100m–500m CPU, 128Mi–512Mi memory)
- [ ] CloudNativePG for PostgreSQL HA

---

## Phase 6 — Resilience and Demo Prep

Goal: prove the system handles failures gracefully and load a realistic dataset.

### 6.1 Seed Scripts

- [ ] `scripts/seed_segments.py` — Overpass API import for Dublin road segments
- [ ] `scripts/seed_demo.py` — create demo drivers, routes, and bookings

### 6.2 Failure Scenarios

- [ ] Service replica failure: kill a pod → Kubernetes restarts, no data loss
- [ ] Redis failure: take Redis down → Conflict Detection falls back to DB, events queue up and resume
- [ ] Database failure: delete Postgres primary → CloudNativePG promotes replica
- [ ] Node failure: disconnect a k3s node → workloads reschedule
- [ ] Concurrent booking conflict: two drivers book last slot → one approved, one rejected

### 6.3 Booking Expiry

- [x] Background task in Booking Service: expire bookings where `departure_time` has passed and status is still PENDING/APPROVED
- [x] Publish `booking.updated` with status EXPIRED
- [x] Conflict Detection Service consumes `booking.updated` to release reservations on CANCELLED/EXPIRED

### 6.4 Makefile

- [ ] Verify all `make` targets work: `dev`, `down`, `down-clean`, `migrate`, `seed`, `logs`, `build`

---

## Dependency Graph

```
Phase 1.1 (fix driver schema)
Phase 1.2 (Redis + OSRM in compose)  ──┐
Phase 1.3 (all migrations)            ──┤
Phase 1.4 (frontend auth updates)      │
                                        ▼
Phase 2.1 (Booking Service)     ────► Phase 3.2 (booking.created event)
Phase 2.2 (Route Service)      ────► Phase 3.2 (conflict detection needs routes)
Phase 2.3 (Conflict Detection) ────► Phase 3.2 + 3.3 (event consumer + producer)
Phase 2.4 (Messaging Service)  ────► Phase 3.4 (booking.updated consumer)
                                        │
Phase 3.1 (Redis Streams infra) ───────┤
Phase 3.5 (Gateway auth)               │
                                        ▼
Phase 4 (Frontend pages)        ────► needs Phase 2 + 3 endpoints working
                                        │
                                        ▼
Phase 5 (Kubernetes)            ────► needs working docker-compose stack
                                        │
                                        ▼
Phase 6 (Resilience + Demo)     ────► needs Kubernetes deployed
```

---

## Suggested Build Order (Parallelizable)

Tasks that can be worked on simultaneously are grouped together.

| Step | Tasks | Blocked By |
|------|-------|------------|
| 1 | 1.1 Fix driver schema + 1.2 Add Redis/OSRM to compose + 1.3 All migrations | — |
| 2 | 1.4 Frontend auth updates + 2.1 Booking Service + 2.2 Route Service + 2.3 Conflict Detection + 2.4 Messaging Service | Step 1 |
| 3 | 3.1 Redis Streams infra + 3.5 Gateway auth/rate limit | Step 1 (Redis) |
| 4 | 3.2 booking.created flow + 3.3 route.assessed flow + 3.4 booking.updated flow | Steps 2 + 3 |
| 5 | 4.1 Routes page + 4.2 Bookings page + 4.3 Inbox page + 4.4 Dashboard + 4.5 Nav | Step 4 |
| 6 | 5.1 K8s base + 5.2 Dev overlay + 5.3 Demo overlay | Step 4 |
| 7 | 6.1 Seed scripts + 6.2 Failure scenarios + 6.3 Booking expiry + 6.4 Makefile | Steps 5 + 6 |
