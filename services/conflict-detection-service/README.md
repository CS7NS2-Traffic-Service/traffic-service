# Conflict Detection Service

Enforces road capacity limits. When a booking is created, this service checks whether all road segments along the requested route have capacity at the requested departure time. If they do, it reserves those segments for the duration of the trip and approves the booking. If any segment is full, it rejects the booking.

## Core Algorithm

On receiving a `booking.created` event:

1. **Load the route** — fetch the route by ID to get its ordered list of segment IDs and `estimated_duration`.
2. **Check capacities** — load the maximum capacity for each segment from `road_segments`.
3. **Time-window overlap check** — for each segment, compute the time window during which the vehicle occupies it:
   - `start = departure_time + (segment_index × 300s)`
   - `end = start + estimated_duration`

   The 300-second offset staggers each segment to approximate the time the vehicle actually enters that part of the route. Count how many existing reservations overlap this window. If `overlap >= capacity` for any segment, the whole route is unavailable.
4. **Atomic reservation** — only if every segment passes the capacity check are reservations created for all segments. The check-then-reserve is done in a single database transaction to prevent race conditions under concurrent bookings.
5. **Publish result** — a `route.assessed` event is written to the outbox with `segments_available: true` or `false`. The booking service will transition the booking to `APPROVED` or `REJECTED` when this event is consumed.

## Reservation Release

When a booking is `CANCELLED` or `EXPIRED`, a `booking.updated` event arrives on the `booking.updated` stream. The service deletes all segment reservations for that booking, freeing up capacity for future bookings at those time windows.

Status values other than `CANCELLED` or `EXPIRED` (e.g. `APPROVED`) are acknowledged and marked processed without any action.

## HTTP Endpoints

These are called synchronously by the frontend before the booking is submitted:

- `POST /api/conflict-detection/routes/availability` — given a list of route candidates and a departure time, returns which routes currently have capacity. Used to show availability in the UI before a booking is made.
- `GET /api/conflict-detection/reservations/booking/:booking_id` — returns active segment reservations for a booking.
- `GET /api/conflict-detection/segments/utilization` — returns current reservation counts for given segments and time windows.

## Data Owned

The `segment_reservations` table and a local read-only copy of `road_segments` and `routes` (written by the routes service, read here).

## Events

| Stream | Direction | When |
|---|---|---|
| `booking.created` | Consumed | Triggers capacity check and reservation |
| `booking.updated` | Consumed | Releases reservations on CANCELLED/EXPIRED |
| `route.assessed` | Published (via outbox) | Result of capacity check sent to booking service |
