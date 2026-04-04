FROM node:22-alpine AS frontend-builder

ARG VITE_MAPBOX_TOKEN
ENV VITE_MAPBOX_TOKEN=${VITE_MAPBOX_TOKEN}

WORKDIR /app/traffic-frontend

COPY traffic-frontend/package.json traffic-frontend/package-lock.json ./
RUN npm ci

COPY traffic-frontend/ ./
RUN npm run build

FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
COPY --from=frontend-builder /app/traffic-frontend/dist ./traffic-frontend/dist

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
