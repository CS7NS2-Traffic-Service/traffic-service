# API Gateway

The API Gateway is the entry point for all client requests. It handles routing, authentication, and rate limiting.

## Responsibilities

- **Reverse Proxy**: Routes incoming requests to the appropriate microservice based on URL path
- **Authentication**: Validates JWT tokens and extracts driver identity
- **Rate Limiting**: Enforces 100 requests per minute per driver using Redis
- **Health Monitoring**: Provides health check endpoints for orchestration

## API

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks Redis) |

### Routing

| Path Pattern | Target Service | Port |
|-------------|---------------|------|
| `/api/driver/*` | driver-service | 8081 |
| `/api/booking/*` | booking-service | 8082 |
| `/api/routes/*` | routes-service | 8083 |
| `/api/conflict-detection/*` | conflict-detection-service | 8084 |
| `/api/messaging/*` | messaging-service | 8085 |
| `/*` (all other) | bff | 8080 |

### Authentication

The gateway validates JWT tokens on all `/api/*` routes except:

- `POST /api/driver/auth/login`
- `POST /api/driver/auth/register`

Valid requests must include an `Authorization: Bearer <token>` header. On success, the driver ID is extracted from the token's `sub` claim and passed to downstream services via `X-Driver-ID` header.

### Rate Limiting

- Limit: 100 requests per minute per driver
- Implementation: Redis INCR with 60-second TTL
- On exceed: Returns HTTP 429

### Correlation ID

All requests receive an `X-Correlation-ID` header (generated if not provided) that is propagated to downstream services for distributed tracing.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret for JWT validation | `super-secret-key-change-in-prod` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379` |
| `BFF_URL` | URL of the BFF service | `http://bff:8080` |
| `SERVICE_DRIVER` | URL of driver-service | - |
| `SERVICE_BOOKING` | URL of booking-service | - |
| `SERVICE_ROUTES` | URL of routes-service | - |
| `SERVICE_MESSAGING` | URL of messaging-service | - |
| `SERVICE_CONFLICT_DETECTION` | URL of conflict-detection-service | - |

## Dependencies

- **Redis**: Rate limiting and health checks
- **Downstream Services**: All microservices it routes to

## Key Design Features

1. **No Business Logic**: Acts as a pure reverse proxy with cross-cutting concerns only
2. **Token Passthrough**: Original JWT is not modified; downstream services validate independently if needed
3. **Graceful Degradation**: Rate limiting allows requests through if Redis is unavailable
4. **Header Stripping**: Removes hop-by-hop headers (host, content-length, transfer-encoding, connection) before proxying