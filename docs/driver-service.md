# Driver Service

The Driver Service handles driver authentication and profile management.

## Responsibilities

- **Authentication**: Driver registration and login with JWT token issuance
- **Profile Management**: Driver profile retrieval

## API

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks PostgreSQL) |

### Authentication Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/driver/auth/register` | Register a new driver |
| POST | `/api/driver/auth/login` | Login and receive JWT token |

### Driver Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/driver/drivers/me` | Get current driver profile |

## Request/Response

### Register

**Request:**
```json
{
  "name": "string",
  "email": "string",
  "password": "string",
  "license_number": "string",
  "vehicle_type": "CAR",
  "region": "Dublin"
}
```

**Response:**
```json
{
  "driver": {
    "driver_id": "uuid",
    "name": "string",
    "email": "string",
    "license_number": "string",
    "vehicle_type": "CAR",
    "region": "string",
    "created_at": "datetime"
  },
  "access_token": "jwt"
}
```

### Login

**Request:**
```json
{
  "email": "string",
  "password": "string"
}
```

### Get Profile

**Headers:** `X-Driver-ID: <driver_uuid>`

**Response:**
```json
{
  "driver_id": "uuid",
  "name": "string",
  "email": "string",
  "license_number": "string",
  "vehicle_type": "CAR",
  "region": "string",
  "created_at": "datetime"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | - |
| `JWT_SECRET_KEY` | Secret for JWT signing | `super-secret-key-change-in-prod` |
| `APP_ENV` | Environment | `development` |
| `SEED_TEST_USER` | Seed test driver in dev | `true` |

## Dependencies

- **PostgreSQL**: Driver data storage

## Key Design Features

1. **Stateless JWT**: Tokens are self-contained with driver_id in `sub` claim
2. **Dev Auto-Seeding**: In development, seeds a test driver automatically
3. **Authenticated via Header**: Profile endpoint uses `X-Driver-ID` header set by API Gateway