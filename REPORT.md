# CS7NS6 Exercise 2 — Report

## 1. Overall Architecture

### System Overview

The Traffic Booking Service is a distributed microservice system where drivers must pre-book every
journey before starting. The system is structured as 7 loosely-coupled services communicating through
two distinct patterns:

- **External communication** (client to system): Synchronous REST/HTTP
- **Internal communication** (service to service): Asynchronous event-driven via Redis Streams

All client traffic enters through a single API Gateway, which handles authentication, rate limiting,
and routing. Services never call each other's HTTP endpoints directly — all inter-service
coordination happens through events.

```
Client (React SPA)
  │
  ▼
API Gateway (:8000)  ─── JWT validation, rate limiting
  ├── /api/driver/*       → Driver Service (:8081)
  ├── /api/booking/*      → Booking Service (:8082)
  ├── /api/routes/*       → Routes Service (:8083)
  ├── /api/conflict-detection/* → Conflict Detection Service (:8084)
  ├── /api/messaging/*    → Messaging Service (:8085)
  └── /*                  → BFF (:8080) → React SPA

Event flows (Redis Streams):
  Booking Service ──booking.created──► Conflict Detection Service
  Conflict Detection ──route.assessed──► Booking Service
  Booking Service ──booking.updated──► Messaging Service
```

### Services Provided

**For drivers:**

- Account registration and login with JWT-based authentication
- Route lookup between any two coordinates in Ireland (powered by OSRM)
- Journey booking with automated conflict detection and approval/rejection
- Real-time road segment utilization visualization (colour-coded map overlay)
- Booking management (view status, cancel)
- Message inbox with booking status notifications

**For enforcement (partially addressed):**

- The system enforces that no journey can begin without prior approval
- Segment capacity limits are enforced through database-level reservation counting
- Concurrent booking conflicts are resolved atomically (pessimistic locking)
- Bookings automatically expire when departure time passes without resolution

The system does not currently have a dedicated enforcement dashboard or penalty point system. The
conflict detection mechanism serves as the primary enforcement layer — it prevents capacity
violations before they occur rather than detecting them after the fact.

---

## 2. Requirements

### Performance

- **API Gateway rate limiting:** 100 requests per driver per minute, tracked in Redis with
  automatic key expiry. On Redis failure, the gateway fails open (allows requests through) to
  preserve availability.
- **Booking creation returns 202 Accepted immediately.** The conflict detection happens
  asynchronously via event streams, so drivers are never blocked waiting for capacity checks.
- **Route caching:** Routes are computed once per (origin, destination) pair and stored in
  PostgreSQL. Subsequent lookups for the same coordinate pair return the cached result without
  querying OSRM again.
- **Frontend polling:** Bookings refresh every 5 seconds, inbox every 10 seconds — balancing
  responsiveness against server load.

### Scalability

- **Horizontal scaling:** Each service runs as an independent process with its own container. In
  Kubernetes, each service can be scaled independently via replica count. The Kustomize overlay
  structure supports different replica counts per environment (dev: 1 replica, production: N
  replicas).
- **Stateless services:** All application services are stateless — session state lives in JWT
  tokens, persistent state in PostgreSQL, ephemeral state in Redis. Any replica can serve any
  request.
- **Event-driven decoupling:** Redis Streams with consumer groups allow multiple instances of a
  service to share the event processing load. Each event is delivered to exactly one consumer
  within a group.

### Availability

- **Health endpoints:** Every service exposes `/health` for Kubernetes liveness probes. Failed
  services are automatically restarted.
- **Graceful degradation:** If Redis is unavailable, the API Gateway's rate limiter fails open
  (allows all traffic). The conflict detection service falls through to direct database queries
  when Redis caching is unavailable.
- **Kubernetes restart policies:** Pod failures trigger automatic restarts. The system is designed
  for minimum 2 replicas per service in production to survive single-pod failures.

### Reliability

- **Event persistence:** Redis Streams persist events to disk. If a consumer service is down, events
  accumulate in the stream and are processed when the consumer recovers. Consumer groups track
  read position, so no events are lost or double-processed.
- **Database transactions:** The conflict detection service uses nested transactions with
  `begin_nested()` (SAVEPOINTs) and pessimistic locking (`SELECT ... FOR UPDATE`) to prevent race
  conditions during concurrent capacity checks.
- **Booking expiry:** A background loop runs every 30 seconds to expire bookings whose departure
  time has passed, preventing stale reservations from permanently consuming capacity.

### Data Consistency

- **Strong consistency for reservations:** Segment reservation creation is wrapped in a database
  transaction with `FOR UPDATE` locks on the segment rows being checked. This prevents two
  concurrent bookings from both seeing available capacity and both being approved when only one
  slot remains.
- **Eventual consistency for notifications:** Booking status changes propagate asynchronously to
  the messaging service. There is a brief window where a booking status has changed but the driver
  has not yet received the notification. This is acceptable because notifications are
  informational, not transactional.
- **Single source of truth per entity:** Each table is owned by exactly one service. Cross-service
  references use plain UUID columns with database-level foreign key constraints managed by Alembic
  migrations, not SQLAlchemy ORM-level references.

### Data Durability

- **PostgreSQL with persistent volumes:** Database data is stored on a Docker volume
  (`postgres_data`) that survives container restarts. In Kubernetes, PersistentVolumeClaims ensure
  data survives pod rescheduling.
- **Write-ahead logging:** PostgreSQL's WAL ensures committed transactions survive crashes.
- **Redis persistence:** Redis Streams are persisted using Redis's default RDB snapshots + AOF,
  ensuring events survive Redis restarts.

### Specification Quality

These requirements are motivated by the system's expected load pattern: a traffic booking system
serving a metropolitan area (Dublin) where thousands of drivers submit bookings concentrated around
peak commute hours (07:00–09:00, 17:00–19:00). The 100 req/min rate limit is set to prevent
individual abuse while allowing normal booking activity. The 30-second expiry check interval
balances resource consumption against timely capacity release. The 5-second frontend polling
interval provides near-real-time status updates without overwhelming the backend during peak
periods.

---

## 3. Techniques

### Replication

**Consistency model:** The system uses a single PostgreSQL primary for all writes, providing strong
consistency (linearisable reads and writes within a single database). For Kubernetes deployment,
CloudNativePG is specified as the operator for managing PostgreSQL replication with automatic
failover.

**Update strategy:** Single-primary replication. All writes go to the primary. Read replicas (when
deployed via CloudNativePG) receive updates through streaming replication. The application services
do not currently distinguish between read and write connections, so all queries hit the primary. This
simplifies consistency guarantees at the cost of read scalability — an acceptable trade-off at the
current scale.

### Transactions

**Isolation level:** The conflict detection service is the critical section for data correctness. It
uses:

1. **Pessimistic locking** (`SELECT ... FOR UPDATE`) on road segment rows during capacity checks.
   This serialises concurrent booking attempts for overlapping segments.
2. **Nested transactions** (`SAVEPOINT` via SQLAlchemy's `begin_nested()`) so that a failed
   reservation attempt rolls back only the reservation creation, not the entire event processing
   transaction.
3. PostgreSQL's default isolation level is **Read Committed**, which combined with the explicit
   `FOR UPDATE` locks provides the necessary serialisation for capacity checks without the
   performance overhead of Serializable isolation.

The booking service uses standard Read Committed isolation for status updates, which is sufficient
because each booking's status is updated by a single consumer processing the `route.assessed` event.

### Sharding

**Exploiting locality:** The system is designed around geographic locality:

- Road segments are associated with regions (e.g., "Dublin")
- Drivers register with a region
- Routes are computed within a geographic area (Ireland, via OSRM)

While the current deployment uses a single database instance, the data model supports future
sharding by region. Each region's road segments, routes, and reservations form a natural shard
boundary — a booking in Dublin never needs to check capacity in Cork. The `region` field on both
drivers and road segments provides the shard key.

### Caching

**In-memory caching:** Redis is used as the caching layer:

- **Rate limiting:** Driver request counts are stored in Redis with 60-second TTL keys
  (`rate_limit:{driver_id}`). This is effectively an in-memory cache of request frequency.
- **Route caching:** Computed routes (OSRM query results) are persisted in PostgreSQL and reused
  for identical origin/destination pairs, avoiding repeated calls to the OSRM routing engine.

**Replacement strategy:** Rate limit keys use TTL-based expiry (60 seconds). Route cache entries are
permanent (routes don't change) — this is a write-once cache where the replacement strategy is
effectively "never evict."

The conflict detection service's segment capacity cache (described in the project specification as
Redis-cached with 30-second TTL) is not yet implemented. Currently, capacity checks query the
database directly on every booking attempt. This is correct but slower under high load — the cache
would reduce database pressure for read-heavy capacity queries.

### Load Balancing

**Kubernetes Service load balancing:** In Kubernetes, each service is fronted by a ClusterIP Service
that distributes requests across pods using round-robin. This is Layer 4 (TCP) load balancing
provided by kube-proxy.

**API Gateway as application-level router:** The API Gateway acts as a Layer 7 router, distributing
incoming requests to the correct downstream service based on URL path. Within Docker Compose,
DNS-based service discovery provides basic load balancing when services are scaled
(`docker compose up --scale booking-service=3`).

**Redis Streams consumer groups:** Event processing load is distributed across consumer group
members. When multiple instances of the conflict detection service are running, Redis delivers each
`booking.created` event to exactly one instance, providing automatic work distribution.

---

## 4. Request Handling

### Concurrent Requests Properly Synchronized

Yes. The critical path for concurrent request handling is the conflict detection service's capacity
check. When two drivers simultaneously book overlapping time windows on the same road segments:

1. Both `booking.created` events arrive at the conflict detection consumer
2. The consumer acquires `SELECT ... FOR UPDATE` locks on the relevant road segment rows
3. The first transaction to acquire the lock proceeds, counts existing reservations, and creates new
   ones if capacity allows
4. The second transaction blocks until the first commits, then sees the updated reservation count
5. If the first booking consumed the last available slot, the second booking is correctly rejected

This pessimistic locking strategy serialises conflicting operations at the database level, preventing
race conditions without requiring application-level distributed locks.

### Double Spending / Double Booking Prevention

Double booking is not possible due to the combination of:

1. **Database-level locking:** `FOR UPDATE` locks prevent two transactions from simultaneously
   reading stale capacity counts
2. **Atomic reservation creation:** All segment reservations for a booking are created within a
   single database transaction (using `begin_nested()`). Either all reservations succeed or all are
   rolled back.
3. **Idempotent event processing:** Each event is acknowledged after processing, and consumer groups
   track position, preventing duplicate processing of the same event.

### Conflicting Requests Properly Handled

When two bookings conflict (requesting the same last-available segment capacity):

1. One booking is APPROVED and receives reservations for all its segments
2. The other booking is REJECTED with `segments_available: false`
3. Both drivers receive inbox notifications of their respective outcomes
4. The REJECTED driver can retry with a different departure time or route

The staggered time window model (each segment's reservation window is offset by 300 seconds ×
segment index along the route) adds temporal realism — a driver doesn't occupy all segments
simultaneously but progresses through them over time.

---

## 5. Failure Handling

### Node Failures

**Communication failures tolerated:** Yes. The event-driven architecture inherently tolerates
communication failures:

- If a service is temporarily unreachable, events accumulate in Redis Streams
- When the service recovers, it resumes reading from its last acknowledged position
- HTTP failures at the API Gateway result in appropriate error responses to the client (502/503)
  without affecting other services

**Node/replica failure detected:** In Kubernetes, liveness probes (`/health` endpoints on every
service) detect unresponsive pods. Kubernetes automatically restarts failed pods and removes them
from the Service's endpoint list.

**Disconnected nodes/replicas:** If a service replica becomes disconnected:

- It stops receiving new HTTP requests (removed from Service endpoints)
- Its Redis Streams consumer stops receiving events (other group members pick up the work)
- Its in-flight database transactions either complete or are rolled back by PostgreSQL's
  connection timeout

**Replica recovery:** When a failed replica restarts:

- It registers with the Kubernetes Service and begins receiving traffic
- It rejoins its Redis Streams consumer group and resumes processing events from the last
  acknowledged position
- No manual intervention is required

**Total failure tolerated:** If all replicas of a service fail simultaneously:

- HTTP requests to that service return 502 from the API Gateway
- Events queue in Redis Streams (Redis persists to disk)
- When any replica recovers, all queued events are processed in order
- No data is lost; the system catches up after recovery

**Consistency maintained across failures/recoveries:** Database transactions ensure that partially
completed operations are rolled back on failure. The booking status lifecycle (PENDING → APPROVED/
REJECTED/EXPIRED) is monotonic — a booking only moves forward through states, preventing
inconsistencies from replayed events.

### Partitions

**Partition handling:** The current architecture's partition tolerance is provided by the separation
of concerns:

- Each service only depends on PostgreSQL and (optionally) Redis
- If the network partitions such that a service can reach PostgreSQL but not Redis, the service
  continues operating with degraded functionality (no rate limiting, no caching, but events queue)
- If a service cannot reach PostgreSQL, it returns errors to clients but does not corrupt state

**Partitions without majority:** In a network partition where no majority partition exists:

- Services that can reach PostgreSQL continue serving reads
- Writes are only accepted by the partition containing the PostgreSQL primary
- Redis Streams events queue on whichever side of the partition the Redis instance resides
- This follows a CP (consistency over availability) approach for writes and an AP approach for
  cached reads

**Merging of partitions:** When a partition heals:

- Kubernetes endpoints are updated and traffic resumes to all replicas
- Redis Streams consumers catch up on queued events
- No special merge logic is needed because only the partition with the PostgreSQL primary could
  accept writes — there are no conflicting writes to reconcile

**Consistency maintained across partitions/merges:** The single-primary PostgreSQL model ensures
that writes are always consistent. There is no multi-master replication that could create conflicting
state during partitions. Event processing is idempotent and ordered, so catching up after a
partition heal produces the same result as continuous processing.

---

## 6. Other Features

### Testing

The system does not currently include automated tests (no pytest, jest, or vitest test files).
Testing has been performed manually through the frontend GUI and direct API calls. For a production
system, the following would be priorities:

- **Integration tests** for the booking → conflict detection → messaging event flow
- **Concurrency tests** verifying that double-booking is prevented under parallel requests
- **API contract tests** for each service's endpoints

### GUI Interface

The system includes a full React 19 + TypeScript frontend served through the BFF:

| Page | Features |
|------|----------|
| `/login` | Email/password authentication |
| `/register` | Full driver registration (name, email, password, license, vehicle type, region) |
| `/routes` | Interactive Mapbox map, click-to-set coordinates, route visualization, segment utilization heatmap (green/yellow/red), departure time picker, direct booking |
| `/bookings` | Status summary cards, filterable booking list, expandable segment reservation details, cancel functionality, 5-second auto-refresh |
| `/inbox` | Message list with unread count badge, read/unread indicators, mark-as-read, 10-second auto-refresh |

The frontend uses Zustand for authentication state (persisted to localStorage) and TanStack React
Query for server state management with automatic refetching.

---

## 7. Middleware

### Middleware Used

1. **API Gateway (FastAPI + httpx):** Acts as a reverse proxy and middleware layer between clients
   and backend services. Implements:
   - JWT token validation and driver ID extraction on every authenticated request
   - Rate limiting (100 req/min/driver) via Redis
   - Dynamic service routing based on environment variables
   - Header injection (`X-Driver-ID`) for downstream services

2. **Redis Streams:** Serves as message-oriented middleware for asynchronous inter-service
   communication. Consumer groups provide:
   - Reliable message delivery (at-least-once semantics)
   - Load distribution across service replicas
   - Message persistence and replay capability
   - Decoupled producer/consumer lifecycle

3. **PostgreSQL (shared database):** While not traditional middleware, the shared PostgreSQL
   instance acts as an integration layer:
   - Database-level foreign key constraints enforce referential integrity across service boundaries
   - Alembic migrations provide schema evolution coordination
   - Transaction isolation provides concurrency control

### Motivation

**API Gateway:** Centralises cross-cutting concerns (auth, rate limiting) that would otherwise be
duplicated across every service. A single entry point also simplifies security auditing and
monitoring.

**Redis Streams over HTTP-based service calls:** The asynchronous event model was chosen because the
booking workflow is inherently asynchronous — a driver submits a booking and waits for a result.
Synchronous service-to-service calls would create tight coupling, cascading failures, and higher
latency. Redis Streams provide persistence (events survive restarts), ordering (FIFO within a
stream), and fan-out (consumer groups) — properties that would require significant custom code with
raw HTTP.

**Shared PostgreSQL:** Pragmatic choice for a team of 7 — operational simplicity of one database
while maintaining logical isolation through per-service table ownership. In a larger system, each
service would have its own database instance, but the current approach provides referential integrity
guarantees that are valuable during development.

---

## 8. Summary of Gaps

The following checklist items are partially or not addressed:

| Item | Status | Notes |
|------|--------|-------|
| Enforcement services | Partial | Capacity enforcement exists; no penalty/violation tracking |
| Quantitative requirements | Partial | Rate limits are quantified; SLAs not formally specified |
| Redis caching in conflict detection | Not implemented | Capacity checks always hit database |
| Sharding | Design only | Region fields exist but no actual sharding deployed |
| Kubernetes base manifests | Missing | `k8s/base/` directory referenced by overlays does not exist |
| Automated tests | Not implemented | No test files in repository |
| CloudNativePG | Not deployed | Referenced in project spec but no operator manifests |
