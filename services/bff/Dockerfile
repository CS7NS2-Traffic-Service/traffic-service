FROM node:22-alpine AS frontend-builder

WORKDIR /app/traffic-frontend

COPY traffic-frontend/package.json traffic-frontend/package-lock.json ./
RUN npm ci

COPY traffic-frontend/ ./
RUN npm run build

FROM python:3.13-slim

WORKDIR /app

RUN pip install fastapi uvicorn aiofiles

COPY src/ ./src/
COPY --from=frontend-builder /app/traffic-frontend/dist ./traffic-frontend/dist

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
