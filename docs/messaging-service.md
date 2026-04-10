# Messaging Service

The Messaging Service handles driver notifications/messages.

## Responsibilities

- **Message Retrieval**: List all messages for a driver
- **Read Status**: Mark messages as read
- **Event Consumer**: Consume booking events from Redis

## API

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks PostgreSQL + Redis) |

### Message Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/messaging/messages` | List all messages |
| PUT | `/api/messaging/messages/{message_id}/read` | Mark message as read |

## Request/Response

### List Messages

**Headers:** `X-Driver-ID: <driver_uuid>`

**Response:**
```json
{
  "messages": [
    {
      "message_id": "uuid",
      "driver_id": "uuid",
      "booking_id": "uuid",
      "content": "string",
      "is_read": false,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### Mark as Read

**Headers:** `X-Driver-ID: <driver_uuid>`

**Response:**
```json
{
  "message_id": "uuid",
  "driver_id": "uuid",
  "booking_id": "uuid",
  "content": "string",
  "is_read": true,
  "created_at": "2024-01-01T10:00:00Z"
}
```

## Background Processing

| Thread | Purpose |
|--------|---------|
| Consumer | Listens to booking events and creates messages |

## Redis Streams

| Stream | Purpose |
|--------|---------|
| `booking.created` | New booking events (creates notification) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection URL |
| `REDIS_URL` | Redis connection URL |

## Dependencies

- **PostgreSQL**: Message storage
- **Redis**: Event streaming

## Key Design Features

1. **Per-Driver Messages**: Messages are scoped to a driver
2. **Simple Read/Unread**: Boolean flag for read status
3. **Auto-Generated**: Messages created from booking events