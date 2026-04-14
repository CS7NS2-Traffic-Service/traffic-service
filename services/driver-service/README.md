# Driver Service

Handles driver identity: registration, authentication, and profile retrieval. Every other service identifies a driver by the UUID that this service issues.

## Business Logic

### Registration (`POST /api/driver/auth/register`)

Creates a new driver account. The password is hashed with bcrypt before storage — the plaintext password is never persisted. Each driver stores:
- `name`, `email` (unique), `license_number`, `region`
- optional `vehicle_type`
- `password_hash`

Duplicate email addresses are rejected at the database level.

### Login (`POST /api/driver/auth/login`)

Looks up the driver by email, verifies the bcrypt hash, and issues a signed HS256 JWT. The token payload contains:
- `sub`: the driver's UUID
- `exp`: expiry timestamp

The token is returned to the client and must be included as `Authorization: Bearer <token>` on every subsequent request. The API gateway validates this token and forwards the driver ID as `X-Driver-ID` to all downstream services — no downstream service needs to verify the JWT itself.

### Profile (`GET /api/driver/drivers/me`)

Returns the authenticated driver's profile. The driver ID is taken from the `X-Driver-ID` header (set by the gateway after token validation).

## Data Owned

The `drivers` table. This service is the sole writer.

## Events

Does not publish or consume any events.
