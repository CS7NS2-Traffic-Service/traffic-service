# BFF (Backend for Frontend)

The BFF serves the React frontend and handles client-side routing.

## Responsibilities

- **Static Asset Serving**: Serves compiled React SPA assets from `/assets`
- **SPA Fallback**: Returns `index.html` for all routes to enable client-side routing
- **Health Monitoring**: Provides health check endpoints

## API

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks frontend assets) |

### Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve `index.html` |
| GET | `/{full_path}` | Try static file, fallback to `index.html` |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VITE_MAPBOX_TOKEN` | Mapbox API token for the frontend |

## Dependencies

- **Frontend Build**: Compiled React assets in `traffic-frontend/dist/`

## Key Design Features

1. **SPA Fallback**: Any non-existent path returns `index.html` to support client-side routing
2. **No API Logic**: Purely serves static content; all API calls are proxied through the API Gateway