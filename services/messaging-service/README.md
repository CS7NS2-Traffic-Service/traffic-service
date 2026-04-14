# Messaging Service

Delivers in-app notifications to drivers when their booking status changes. It maintains a persistent inbox per driver so messages are available when the driver opens the app.

## Business Logic

The service consumes the `booking.updated` Redis Stream (consumer group `messaging-service`). Each event carries a `booking_id`, `driver_id`, and `status`.

On receiving an update, the service creates an inbox message for the driver with human-readable content based on the new status:

| Status | Message |
|---|---|
| `APPROVED` | Your booking has been approved. Have a safe journey! |
| `REJECTED` | Your booking has been rejected due to road capacity constraints. Please try a different departure time or route. |
| `CANCELLED` | Your booking has been cancelled. |
| `EXPIRED` | Your booking has expired as the departure time has passed. |
| _(any other)_ | Your booking status has been updated to `<status>`. |

The message record and a `processed_events` entry are written in the same database transaction. If the same event is delivered again (e.g. after a consumer restart), the `processed_events` unique constraint causes an `IntegrityError`, which is caught and silently ignored — the message will not be duplicated.

## HTTP Endpoints

These are called by the frontend to render the driver's notification inbox:

- `GET /api/messaging/messages` — returns all messages for the authenticated driver, ordered newest first.
- `PUT /api/messaging/messages/:id/read` — marks a single message as read.

The driver ID is taken from the `X-Driver-ID` header set by the API gateway.

## Data Owned

The `messages` table and the `processed_events` table (local to this service).

## Events

| Stream | Direction | When |
|---|---|---|
| `booking.updated` | Consumed | Creates a new inbox message for the driver |
