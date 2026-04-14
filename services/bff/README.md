# BFF (Backend for Frontend)

Serves the compiled React single-page application to the browser. This service has no business logic.

## How it works

The React app is compiled into static files (`index.html` + assets) during the Docker build and embedded into the image. At runtime, the FastAPI server:

- Serves `/assets/...` as static files directly from `traffic-frontend/dist/assets/`.
- For any other path, returns `index.html` if a matching file exists in `dist/`, otherwise falls back to `index.html`. This supports client-side routing — the browser receives `index.html` for every deep-link URL and React Router takes over.

The readiness probe fails if `dist/index.html` does not exist, catching a broken build before traffic is routed to the pod.

All API calls from the frontend go to `/api/...`, which the API gateway intercepts before they reach this service.

## Frontend pages

| Page | Path | Purpose |
|---|---|---|
| Login | `/login` | Driver login, stores JWT in memory |
| Register | `/register` | New driver registration |
| Home | `/` | Landing page |
| Book Route | `/book` | Map-based route planner — pick origin/destination, see available routes with capacity status, submit booking |
| Bookings | `/bookings` | List of the driver's bookings and their current statuses |
| Inbox | `/inbox` | Driver notification inbox — messages about booking status changes |

## Development

In development, run the Vite dev server (`npm run dev` inside `traffic-frontend/`). Vite proxies `/api` requests to `localhost:8000` (the API gateway), so the BFF Python server is not needed locally.
