# Routes Service

Computes driving routes between two coordinates, decomposes them into road segments, and persists the results for reuse by the conflict detection service.

## Business Logic

### Route computation (`POST /api/routes/routes`)

Given an origin and destination (lat/lng pairs), the service first checks whether a route for that origin–destination pair already exists in the database. If so, it returns the cached result immediately.

If no cached route exists, it queries OSRM (Open Source Routing Machine) for the best route(s). OSRM returns turn-by-turn steps with node annotations. The service processes each step to:

1. Extract **edge IDs** — each edge is a directed pair of OSM node IDs represented as `min(a,b)-max(a,b)`, making them undirected and stable.
2. Map edges onto **road segments** — a road segment is a named stretch of road with a capacity (default: 5 simultaneous vehicles). When edges from a step already belong to an existing segment, that segment is reused. Remaining unmapped edges are grouped into a new segment whose ID is a 16-character SHA-256 hash of its sorted edge IDs.

The route is then persisted with:
- `origin`, `destination` as `"lat,lng"` strings
- `segment_ids` — ordered list of segment UUIDs along the route
- `estimated_duration` — seconds from OSRM
- `geometry` — GeoJSON LineString for map rendering

### Route lookup (`GET /api/routes/routes/:id`)

Returns a previously computed route by ID.

### Segment inspection (`GET /api/routes/routes/:id/segments`)

Returns the full segment objects for a route, preserving route order. The conflict detection service uses this to check whether a route's segments have capacity at a given departure time.

## Data Owned

The `routes` table and `road_segments` table. Road segments are shared read-only by the conflict detection service — the routes service is the sole writer.

## Events

Does not publish or consume any events.
