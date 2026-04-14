# API Gateway

Single entry point for all HTTP traffic. Every request from the frontend passes through here before reaching a downstream service.

## Responsibilities

- **JWT authentication** — all requests to `/api/...` must carry a valid `Bearer` token, except `POST /api/driver/auth/login` and `POST /api/driver/auth/register`. The token is verified using HS256 with the shared `JWT_SECRET_KEY`. The `sub` claim (driver ID) is extracted and forwarded downstream as the `X-Driver-ID` header.
- **Rate limiting** — authenticated drivers are limited to 100 requests per 60-second window. The counter is stored in Redis under `rate_limit:<driver_id>`. If Redis is unreachable, the check passes so the gateway stays operational.
- **Correlation ID propagation** — each request is assigned an `X-Correlation-ID` (from the incoming header, or a freshly generated UUID). This header is forwarded to every downstream service and echoed back in the response.
- **Dynamic reverse proxy** — routes `/api/<service>/...` to the service whose URL is stored in the `SERVICE_<SERVICE>` environment variable (e.g. `SERVICE_BOOKING=http://booking-service:8082`). No code change is needed to add a new downstream service — just add an env var. Everything outside `/api/` is forwarded to the BFF.

## What it does NOT do

The gateway contains no business logic. It does not read or write bookings, routes, or messages. It does not transform payloads. It buffers the full response body and re-emits it, stripping hop-by-hop headers (`content-encoding`, `transfer-encoding`, `content-length`, `connection`).

## Routing table

| Path pattern | Destination |
|---|---|
| `POST /api/driver/auth/login` | driver-service (public) |
| `POST /api/driver/auth/register` | driver-service (public) |
| `/api/driver/...` | driver-service |
| `/api/booking/...` | booking-service |
| `/api/routes/...` | routes-service |
| `/api/conflict-detection/...` | conflict-detection-service |
| `/api/messaging/...` | messaging-service |
| `/*` (everything else) | BFF (React SPA) |
