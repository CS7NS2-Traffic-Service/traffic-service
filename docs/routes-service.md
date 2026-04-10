# Routes Service

The Routes Service handles route creation and lookup using OSRM for routing.

## Responsibilities

- **Route Creation**: Generate routes from origin to destination using OSRM
- **Route Lookup**: Retrieve existing routes by ID
- **Segment Lookup**: Get road segments for a route

## API

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks PostgreSQL) |

### Route Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/routes/routes?origin_lat=&origin_lng=&dest_lat=&dest_lng=` | Lookup/create routes |
| GET | `/api/routes/routes/{route_id}` | Get route by ID |
| GET | `/api/routes/routes/{route_id}/segments` | Get segments for route |

## Request/Response

### Lookup Routes

**Query Parameters:**
- `origin_lat` (required): Origin latitude (-90 to 90)
- `origin_lng` (required): Origin longitude (-180 to 180)
- `dest_lat` (required): Destination latitude (-90 to 90)
- `dest_lng` (required): Destination longitude (-180 to 180)

**Response:**
```json
[
  {
    "route_id": "uuid",
    "origin": {"lat": 53.3498, "lng": -6.2603},
    "destination": {"lat": 53.3550, "lng": -6.2500},
    "segment_ids": ["uuid1", "uuid2"],
    "geometry": "geojson...",
    "estimated_duration": 1800,
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

### Get Route

**Response:**
```json
{
  "route_id": "uuid",
  "origin": {"lat": 53.3498, "lng": -6.2603},
  "destination": {"lat": 53.3550, "lng": -6.2500},
  "segment_ids": ["uuid1", "uuid2"],
  "geometry": "geojson...",
  "estimated_duration": 1800,
  "created_at": "2024-01-01T10:00:00Z"
}
```

### Get Segments

**Response:**
```json
[
  {
    "segment_id": "uuid",
    "osm_way_id": 12345,
    "name": "O'Connell Street",
    "region": "Dublin",
    "capacity": 2,
    "coordinates": [[lng, lat], ...]
  }
]
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection URL |
| `OSRM_URL` | OSRM service URL |

## Dependencies

- **PostgreSQL**: Route and segment storage
- **OSRM**: Open Source Routing Machine for route calculations

## Key Design Features

1. **Multi-Route Results**: Returns multiple route candidates sorted by duration
2. **GeoJSON Geometry**: Returns GeoJSON for map rendering
3. **Segment Decomposition**: Breaks routes into OSM road segments
4. **Caching**: Caches computed routes for reuse