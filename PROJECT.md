# Traffic Booking Service — Project Specification

## Overview

A globally-accessible distributed traffic booking service where drivers must prebook every journey
before starting it. No driver may begin a journey without receiving an approval notification. The
system is designed to support millions of concurrent users worldwide.

The system is structured as 7 loosely-coupled microservices, one per group member.

### Core Architectural Principle

- **External communication** (client → system) is **synchronous** via REST/HTTP
- **Internal communication** (service → service) is **asynchronous** via Redis Streams

---

## Services

### 1. BFF (Backend for Frontend)

**Owns:** Nothing in the database

**Responsibilities:**

- Serve the React frontend as static files
- Proxy API calls from the frontend to the API Gateway
- Handle frontend routing

**Frontend pages:**

- `/login` — driver login form
- `/register` — driver registration form
- `/routes` — browse available routes with Mapbox map, segment capacity overlay (green = available,
  red = full)
- `/bookings` — submit a new booking, view booking status
- `/inbox` — driver message inbox
- `/dashboard` — admin view, live service health, booking throughput

**Tech:**

- React + Vite + TypeScript
- FastAPI serves static files
- Vite proxy during development, FastAPI static mount in production
- Mapbox GL JS for map rendering and route/segment overlays

**Dockerfile:** Multi-stage — Node builds React, Python serves output

---

### 2. API Gateway

**Owns:** Nothing in the database

**Responsibilities:**

- Single entry point for all incoming client requests
- Validate JWT tokens on every request (except public paths)
- Inject `X-Driver-ID` header after token verification
- Route requests to correct downstream service
- Rate limit requests per driver (using Redis)

**Public paths (no auth required):**

- `POST /auth/login`
- `POST /auth/register`
- `GET /health`

**Routing table:**

- `/auth/*` → Driver Service
- `/drivers/*` → Driver Service
- `/bookings/*` → Booking Service
- `/routes/*` → Route Service
- `/messages/*` → Messaging Service

**Rate limiting:**

- Max 100 requests per driver per minute
- Tracked in Redis, returns 429 if exceeded

---

### 3. Driver Service

**Owns:** `drivers` table

**Responsibilities:**

- Driver registration
- Driver login and JWT issuance
- Driver profile management

**Endpoints:**

- `POST /auth/register` — create account, return JWT
- `POST /auth/login` — verify credentials, return JWT
- `GET /drivers/me` — return current driver profile (requires `X-Driver-ID`)

**Driver entity:**

```
drivers
├── driver_id       UUID, PK
├── name            TEXT, NOT NULL
├── email           TEXT, UNIQUE, NOT NULL
├── password_hash   TEXT, NOT NULL
├── license_number  TEXT, NOT NULL
├── vehicle_type    TEXT (CAR, MOTORCYCLE, TRUCK, HGV)
├── region          TEXT, NOT NULL
└── created_at      TIMESTAMP
```

**JWT payload:**

```json
{
  "driver_id": "uuid",
  "exp": "timestamp"
}
```

**Notes:**

- Passwords hashed with bcrypt
- JWT signed with shared `JWT_SECRET_KEY` environment variable
- Token expiry: 24 hours

---

### 4. Booking Service

**Owns:** `bookings` table

**Responsibilities:**

- Create bookings (status: PENDING)
- Cancel bookings
- Update booking status based on consumed events
- Publish events to Redis Streams

**Endpoints:**

- `POST /bookings` — create booking, returns 202 Accepted immediately
- `GET /bookings/{booking_id}` — get booking status
- `GET /bookings` — list bookings for current driver
- `DELETE /bookings/{booking_id}` — cancel booking

**Booking entity:**

```
bookings
├── booking_id        UUID, PK
├── driver_id         UUID, FK → drivers
├── route_id          UUID, FK → routes
├── departure_time    TIMESTAMP, NOT NULL
├── estimated_arrival TIMESTAMP
├── status            TEXT (PENDING, APPROVED, REJECTED, CANCELLED, EXPIRED)
├── created_at        TIMESTAMP
└── expires_at        TIMESTAMP
```

**Booking status lifecycle:**

```
PENDING → APPROVED  (via route.assessed event, segments_available: true)
PENDING → REJECTED  (via route.assessed event, segments_available: false)
PENDING → EXPIRED   (if departure_time passes without resolution)
APPROVED → CANCELLED (driver cancels)
```

**Events published:**

- `booking.created` — published when booking is created
- `booking.updated` — published when status changes

**Events consumed:**

- `route.assessed` — updates booking status, publishes booking.updated

---

### 5. Route Service

**Owns:** `routes` table

**Responsibilities:**

- Route lookup by origin and destination
- Route caching (compute once, reuse)
- Road segment data management
- OSM data import via Overpass API
- Query OSRM for route geometry and way IDs
- Map OSRM way IDs to internal road segment IDs

**Endpoints:**

- `GET /routes?origin_lat=X&origin_lng=X&dest_lat=Y&dest_lng=Y` — find or compute route
- `GET /routes/{route_id}` — get route details including geometry and segments
- `GET /routes/{route_id}/segments` — get ordered segment list with capacity

**Route entity:**

```
routes
├── route_id            UUID, PK
├── origin              TEXT, NOT NULL
├── destination         TEXT, NOT NULL
├── segment_ids         UUID[], ordered list of segment IDs
├── geometry            JSONB (GeoJSON LineString for frontend rendering)
├── estimated_duration  INTEGER (seconds)
└── created_at          TIMESTAMP
```

**RoadSegment entity** (also owned by Route Service for seeding purposes):

```
road_segments
├── segment_id    UUID, PK
├── osm_way_id    TEXT    ← links to OSRM output
├── name          TEXT
├── region        TEXT
├── capacity      INTEGER
└── coordinates   JSONB
```

**Route resolution flow:**

```
1. Check if route already exists for this origin/destination pair
2. If not, query OSRM: GET http://osrm:5000/route/v1/driving/{origin};{dest}
3. OSRM returns geometry (GeoJSON) + ordered OSM way IDs
4. Map OSM way IDs to internal segment_ids via osm_way_id column
5. Store Route record with geometry and segment_ids
6. Return route to frontend
```

**Notes:**

- Routes are computed once and reused — uniqueness on (origin, destination)
- Route Service is **read-only** from the event flow perspective — it does not consume or produce
  events
- Road segment data seeded via Overpass API script (`scripts/seed_segments.py`)
- OSRM is an internal dependency of this service — no other service talks to OSRM directly

**Overpass API query (Dublin area example):**

```python
query = """
[out:json];
way["highway"~"motorway|trunk|primary"]["name"]
  (53.2,-6.4,53.4,-6.1);
out geom;
"""
```

---

### 6. Conflict Detection Service

**Owns:** `road_segments`, `segment_reservations` tables

**Responsibilities:**

- Check road segment capacity for a given route and time window
- Create segment reservations when a booking is approved
- Delete segment reservations when a booking is cancelled
- Cache segment capacity reads in Redis

**Events consumed:**

- `booking.created` — checks capacity, publishes route.assessed

**Events published:**

- `route.assessed` — contains whether all segments are available

**RoadSegment entity:**

```
road_segments
├── segment_id    UUID, PK
├── name          TEXT, NOT NULL
├── region        TEXT, NOT NULL
├── capacity      INTEGER (max vehicles per time window)
└── coordinates   JSONB (start/end lat-lng)
```

**SegmentReservation entity:**

```
segment_reservations
├── reservation_id      UUID, PK
├── booking_id          UUID, FK → bookings
├── segment_id          UUID, FK → road_segments
├── time_window_start   TIMESTAMP
└── time_window_end     TIMESTAMP
```

**Conflict detection logic:**

```
For each segment on the route:
  count = SELECT COUNT(*) FROM segment_reservations
          WHERE segment_id = X
          AND time_window_start < departure_time + estimated_duration
          AND time_window_end > departure_time

  if count >= segment.capacity:
    return segments_available: false

return segments_available: true
```

**Important:** Reservation creation must be wrapped in a database transaction to prevent race
conditions under concurrent bookings.

**Redis caching:**

- Cache key: `segment:capacity:{segment_id}:{time_window}`
- TTL: 30 seconds
- On Redis failure: fall through to database query

---

### 7. Messaging Service

**Owns:** `messages` table

**Responsibilities:**

- Consume booking status events
- Persist messages to driver inbox
- Serve inbox to frontend

**Endpoints:**

- `GET /messages` — list messages for current driver
- `PUT /messages/{message_id}/read` — mark message as read

**Events consumed:**

- `booking.updated` — creates a message record

**Message entity:**

```
messages
├── message_id   UUID, PK
├── driver_id    UUID, FK → drivers
├── booking_id   UUID, FK → bookings
├── content      TEXT
├── read         BOOLEAN, DEFAULT false
└── created_at   TIMESTAMP
```

---

## Events (Redis Streams)

### booking.created

**Producer:** Booking Service **Consumer:** Conflict Detection Service

```json
{
  "booking_id": "uuid",
  "driver_id": "uuid",
  "route_id": "uuid",
  "departure_time": "ISO8601"
}
```

### route.assessed

**Producer:** Conflict Detection Service **Consumer:** Booking Service

```json
{
  "booking_id": "uuid",
  "route_id": "uuid",
  "segments_available": true
}
```

### booking.updated

**Producer:** Booking Service **Consumer:** Messaging Service

```json
{
  "booking_id": "uuid",
  "driver_id": "uuid",
  "status": "APPROVED | REJECTED | CANCELLED"
}
```

---

## Infrastructure

### PostgreSQL

- Single instance, logically isolated schemas per service
- Managed with Alembic migrations in `db/migrations/`
- CloudNativePG operator for replication in Kubernetes

### Redis

- Handles both caching (Conflict Detection) and messaging (Redis Streams)
- All services connect via `REDIS_URL` environment variable

### Kubernetes

- Local development: minikube (single node)
- Demo: k3s multi-node cluster across team laptops
- Every service runs minimum 2 replicas
- Every service exposes `/health` endpoint for Kubernetes liveness probe

### OSRM (Open Source Routing Machine)

- Standalone routing engine, owned and operated by the Route Service
- Takes OSM road data and calculates fastest path between two coordinates
- Returns route geometry (GeoJSON) and ordered OSM way IDs
- Runs as a separate container — Route Service queries it via HTTP internally
- No other service talks to OSRM directly

**Setup:**

```bash
# Download Ireland OSM data
wget https://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf

# Pre-process (run once, output stored in osrm-data/)
docker run -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/ireland.osm.pbf
docker run -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-partition /data/ireland.osrm
docker run -v $(pwd)/osrm-data:/data osrm/osrm-backend osrm-customize /data/ireland.osrm
```

**docker-compose entry:**

```yaml
osrm:
  image: osrm/osrm-backend
  ports:
    - "5000:5000"
  volumes:
    - ./osrm-data:/data
  command: osrm-routed /data/ireland.osrm
```

- Mapbox GL JS for frontend map rendering
- Free tier: 50,000 map loads per month — sufficient for development and demo
- Requires a Mapbox API key — store in `.env`, never commit to git
- Used for: rendering road segments as polyline overlays, colour-coded by capacity
- OSM tiles served via Mapbox — consistent with road data source

---

## Project Structure

```
traffic-service/
├── services/
│   ├── bff/
│   │   ├── traffic-frontend/    ← React app
│   │   ├── src/main.py          ← FastAPI
│   │   └── Dockerfile
│   ├── api-gateway/
│   ├── driver-service/
│   ├── booking-service/
│   ├── route-service/
│   ├── conflict-detection-service/
│   └── messaging-service/
├── db/
│   ├── alembic.ini
│   └── migrations/versions/
├── k8s/
│   ├── base/
│   └── overlays/
│       ├── dev/
│       └── demo/
├── scripts/
│   ├── seed_segments.py   ← Overpass API import
│   └── seed_demo.py       ← Demo data
├── osrm-data/             ← pre-processed OSM data for OSRM (gitignored, large files)
├── docker-compose.yml
├── Makefile
└── PROJECT.md
```

---

## Cross-Service Foreign Keys

All services share one PostgreSQL database but each has its own SQLAlchemy `declarative_base()`. Do
**not** use `ForeignKey('other_table.id')` in a model when the target table is owned by a different
service — SQLAlchemy cannot resolve cross-registry references and will raise `NoReferencedTableError`.
Instead, declare the column as a plain typed column (e.g. `mapped_column(UUID(as_uuid=True),
nullable=False)`) and rely on the Alembic migration to create the actual DB-level FK constraint.

---

## Service Structure (per service)

Each service follows a consistent technical split:

```
src/
├── main.py       ← FastAPI app, router registration
├── database.py   ← SQLAlchemy engine, session dependency
├── models.py     ← SQLAlchemy table models
├── schemas.py    ← Pydantic request/response models
├── router.py     ← HTTP endpoints (thin, no business logic)
├── service.py    ← Business logic
└── consumer.py   ← Redis Streams event consumer (if applicable)
```

---

## Environment Variables (per service)

```
DATABASE_URL=postgresql://traffic:traffic@postgres:5432/traffic
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=your-secret-key
SERVICE_PORT=8000
MAPBOX_TOKEN=your-mapbox-token   # BFF / frontend only
```

---

## Failure Scenarios (for demo)

1. **Service replica failure** — `kubectl delete pod <pod>` → Kubernetes restarts automatically
2. **Redis failure** — take Redis down → Conflict Detection falls back to DB, events queue up
3. **Database failure** — delete PostgreSQL primary → CloudNativePG promotes replica
4. **Node failure** — disconnect a laptop from k3s cluster → workloads reschedule
5. **Concurrent booking conflict** — two drivers book last slot simultaneously → one approved, one
   rejected, no double booking

---

## Development Phases

1. **Foundation** — monorepo, docker-compose, shared event schemas, Alembic setup
2. **Happy path** — each service builds core functionality, all services run in docker-compose
3. **Integration** — full booking flow works end to end
4. **Kubernetes** — deploy to minikube, write k8s manifests
5. **Resilience** — failure scenarios, replicas, CloudNativePG
6. **Demo prep** — k3s multi-node, seed real OSM data, demo dashboard

---

## Make Commands

```makefile
make dev          # docker-compose up --build
make down         # docker-compose down
make down-clean   # docker-compose down -v (wipes DB)
make migrate      # run alembic migrations
make seed         # seed road segments from Overpass API
make logs         # docker-compose logs -f
make build        # docker-compose build
```
