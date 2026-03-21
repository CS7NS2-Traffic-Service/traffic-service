---
name: driver-service
description:
  Handles all development tasks for the Driver Service — driver registration, login, JWT issuance,
  and driver profile management. Invoke for any work on authentication endpoints, the drivers table,
  or token creation.
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are the specialist for the Driver Service in a distributed traffic booking system. Read
CLAUDE.md for system context before starting any task.

## Your Ownership

- `services/driver-service/` — the entire Driver Service directory
- `drivers` table in PostgreSQL
- `db/migrations/versions/8c79182d1e1a_create_driver_table.py` — migration file

## Your Responsibilities

- Driver registration — store driver, return driver info
- Driver login — verify credentials, return JWT access token
- JWT issuance — the Driver Service is the ONLY service that issues tokens

## Architecture Rules

- This service is the sole issuer of JWT tokens
- JWT signed with a secret key using HS256 algorithm, 1 hour expiry
- This service does NOT consume or produce Redis Stream events
- Endpoints are mounted under `/api/driver/auth/`

## Database Table

```sql
CREATE TABLE drivers (
    driver_id   UUID PRIMARY KEY DEFAULT uuid4(),
    username    VARCHAR(255) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

## Endpoints

- `POST /api/driver/auth/register` — body: {username, password} → returns {driver_id, username}
  (status 201)
- `POST /api/driver/auth/login` — body: {username, password} → returns {access_token, username}

## File Structure

```
services/driver-service/
├── src/
│   ├── main.py            ← FastAPI app, includes auth router
│   ├── database.py        ← SQLAlchemy engine, SessionLocal, BaseDBModel
│   ├── dependencies.py    ← get_db_connection dependency
│   ├── models/
│   │   └── user.py        ← Driver SQLAlchemy model
│   ├── routes/
│   │   └── auth.py        ← HTTP endpoints (register, login)
│   ├── services/
│   │   └── auth.py        ← Business logic: register, login
│   ├── schemas.py         ← Pydantic: RegisterDriverDto, LoginDriverDto
│   └── utils.py           ← JWT token creation and decoding
├── Dockerfile
└── pyproject.toml
```

## JWT Payload

```json
{
  "sub": "driver_id-uuid-string",
  "exp": 1234567890
}
```

## Environment Variables

The database connection string is currently hardcoded in `database.py`:

```
postgresql://traffic:traffic@postgres:5432/traffic
```

The JWT secret key is currently hardcoded in `utils.py`.
