# Conflict Detection Service

The Conflict Detection Service detects route conflicts and manages segment reservations.

## Responsibilities

- **Route Availability**: Check if routes have available capacity
- **Reservation Management**: Create/manage segment time-window reservations
- **Conflict Assessment**: Assess new bookings for conflicts
- **Utilization Tracking**: Track segment utilization
- **Event Processing**: Consume booking events from Redis

## API

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks PostgreSQL + Redis) |

### Availability Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/conflict-detection/availability` | Check route availability |

### Utilization Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/conflict-detection/utilization` | Get segment utilization |

### Reservation Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/conflict-detection/bookings/{booking_id}/reservations` | Get reservations for booking |

## Request/Response

### Check Availability

**Request:**
```json
{
  "routes": [
    {
      "route_id": "uuid",
      "segment_ids": ["uuid1", "uuid2"],
      "estimated_duration": 1800
    }
  ],
  "departure_time": "2024-01-01T10:00:00Z"
}
```

**Response:**
```json
{
  "routes": [
    {"route_id": "uuid", "available": true}
  ]
}
```

### Get Utilization

**Request:**
```json
{
  "segment_ids": ["uuid1", "uuid2"],
  "window_start": "2024-01-01T09:30:00Z",
  "window_end": "2024-01-01T10:30:00Z"
}
```

**Response:**
```json
{
  "utilization": [
    {"segment_id": "uuid1", "active_reservations": 1},
    {"segment_id": "uuid2", "active_reservations": 0}
  ]
}
```

### Get Reservations

**Response:**
```json
[
  {
    "reservation_id": "uuid",
    "segment_id": "uuid",
    "time_window_start": "2024-01-01T10:00:00Z",
    "time_window_end": "2024-01-01T10:30:00Z"
  }
]
```

## Background Processing

The service runs four background threads:

1. **Booking Created Consumer**: Listens to `booking.created` stream, assesses new bookings
2. **Booking Updated Consumer**: Listens to `booking.updated` stream, releases reservations on cancel/expire
3. **Outbox Relay**: Publishes processed events from outbox table to Redis
4. **Cleanup**: Cleans up old processed events

## Redis Streams

| Stream | Purpose |
|--------|---------|
| `booking.created` | New booking events |
| `booking.updated` | Booking status update events |
| `booking.created.dlq` | Dead letter queue for failed events |
| `booking.updated.dlq` | Dead letter queue for failed events |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection URL |
| `REDIS_URL` | Redis connection URL |

## Dependencies

- **PostgreSQL**: Reservations, routes, segments, events storage
- **Redis**: Event streaming and consumer

## Key Design Features

1. **Consumer Groups**: Uses Redis consumer groups for parallel processing
2. **Outbox Pattern**: Publishes events via database outbox
3. **DLQ**: Failed messages go to dead letter queues
4. **Retry with Backoff**: Exponential backoff on processing failures
5. **Idempotency**: Processed events tracked to prevent duplicate processing