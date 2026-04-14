# Booking Service

Manages the full lifecycle of a route booking, from creation through to approval, rejection, cancellation, or expiry. Written in Go.

## Booking State Machine

```
                  ┌─────────────┐
       create     │   PENDING   │
  ─────────────►  │             │
                  └──────┬──────┘
                         │  route.assessed event received
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      APPROVED        REJECTED      (driver cancels)
          │                          CANCELLED
          │
  departure_time passes
          │
       EXPIRED
```

Valid transitions:
- `PENDING` → `APPROVED`, `REJECTED`, `CANCELLED`, `EXPIRED`
- `APPROVED` → `CANCELLED`, `EXPIRED`
- All terminal states (`REJECTED`, `CANCELLED`, `EXPIRED`) are final.

## Business Logic

### Creating a booking (`POST /api/booking/bookings`)

A booking is created in `PENDING` status. The request must supply a `route_id`, `departure_time` (must be in the future), and optionally `estimated_arrival`. A `booking.created` event is written atomically to the outbox alongside the booking row — both succeed or both fail.

`expires_at` is set to `estimated_arrival` when provided, otherwise to `departure_time`. The expiry loop uses this field to decide when to expire a booking.

### Outbox relay

A background goroutine polls the `outbox` table every 500 ms for unpublished events and publishes them to Redis Streams in batches of up to 50. Once published, they are marked in the database. Published events older than 7 days are cleaned up hourly.

This decouples booking persistence from Redis availability — a booking is safely recorded even if Redis is temporarily down.

### Conflict detection response (consumer)

The service consumes the `route.assessed` Redis Stream (consumer group `booking-service`). When a `route.assessed` event arrives:
- `segments_available: true` → booking transitions to `APPROVED`
- `segments_available: false` → booking transitions to `REJECTED`

The status update and a new `booking.updated` outbox event are written in a single transaction. Idempotency is enforced: `processed_events` is checked before handling, and the event is marked processed after.

The consumer runs in a supervised goroutine (`Start` → `run`). If it exits unexpectedly it restarts after 2 seconds. If the consumer group is lost (e.g. Redis wiped), it is automatically recreated via `ensureConsumerGroup`.

### Expiry loop

A background goroutine runs every 30 seconds. It queries for all `PENDING` or `APPROVED` bookings whose `departure_time` is in the past and transitions each to `EXPIRED`, emitting a `booking.updated` event via the outbox.

### Cancellation (`DELETE /api/booking/bookings/:id`)

A driver can cancel any booking that is still `PENDING` or `APPROVED`. Cancellation is rejected with `409 Conflict` for terminal-state bookings. A `booking.updated` event is written transactionally.

## Data Owned

The `bookings` table, the `outbox` table, and the `processed_events` table.

## Events

| Stream | Direction | When |
|---|---|---|
| `booking.created` | Published | Booking row created |
| `booking.updated` | Published | Status changes to APPROVED, REJECTED, CANCELLED, or EXPIRED |
| `route.assessed` | Consumed | Conflict detection result arrives |
