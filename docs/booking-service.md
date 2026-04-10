# Booking Service

The Booking Service manages driver bookings. Built in Go.

## Responsibilities

- **Booking Creation**: Create new bookings for routes
- **Booking Retrieval**: Get booking details and list all bookings
- **Booking Cancellation**: Cancel existing bookings
- **Event Consumption**: Consume booking events from Redis
- **Outbox Pattern**: Publish events via outbox table
- **Expiry**: Auto-expire pending bookings

## API

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks PostgreSQL + Redis) |

### Booking Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/booking/bookings` | List all bookings for driver |
| POST | `/api/booking/bookings` | Create a new booking |
| GET | `/api/booking/bookings/{booking_id}` | Get booking details |
| DELETE | `/api/booking/bookings/{booking_id}` | Cancel a booking |

## Request/Response

### Create Booking

**Headers:** `X-Driver-ID: <driver_uuid>`

**Request:**
```json
{
  "route_id": "uuid",
  "departure_time": "2024-01-01T10:00:00Z",
  "estimated_arrival": "2024-01-01T10:30:00Z"
}
```

**Response:** HTTP 202 Accepted
```json
{
  "booking_id": "uuid",
  "driver_id": "uuid",
  "route_id": "uuid",
  "departure_time": "2024-01-01T10:00:00Z",
  "estimated_arrival": "2024-01-01T10:30:00Z",
  "status": "PENDING",
  "created_at": "2024-01-01T09:00:00Z",
  "expires_at": "2024-01-01T10:00:00Z"
}
```

### List Bookings

**Headers:** `X-Driver-ID: <driver_uuid>`

**Response:**
```json
[
  {
    "booking_id": "uuid",
    "driver_id": "uuid",
    "route_id": "uuid",
    "departure_time": "2024-01-01T10:00:00Z",
    "estimated_arrival": "2024-01-01T10:30:00Z",
    "status": "PENDING",
    "created_at": "2024-01-01T09:00:00Z",
    "expires_at": "2024-01-01T10:00:00Z"
  }
]
```

### Cancel Booking

**Headers:** `X-Driver-ID: <driver_uuid>`

**Response:** Returns updated booking with CANCELLED status.

## Status Values

- `PENDING` - Awaiting departure
- `CONFIRMED` - Confirmed by conflict detection
- `CANCELLED` - Cancelled by driver
- `EXPIRED` - Past departure time without confirmation

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection URL |
| `REDIS_URL` | Redis connection URL |

## Dependencies

- **PostgreSQL**: Booking data storage
- **Redis**: Event streaming and consumer

## Key Design Features

1. **Outbox Pattern**: Events published via database outbox table
2. **Async Processing**: Redis consumer handles booking events
3. **Idempotency**: CreateBooking is idempotent
4. **Deadline Enforcement**: Bookings expire if not confirmed before departure