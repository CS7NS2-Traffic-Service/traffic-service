FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ ./src/
WORKDIR /app/src
EXPOSE 8085
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8085"]
