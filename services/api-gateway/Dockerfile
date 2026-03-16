FROM python:3.13-slim
WORKDIR /app
RUN pip install fastapi uvicorn httpx
COPY src/ ./src/
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
