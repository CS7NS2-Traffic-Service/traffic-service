import logging
import threading
from contextlib import asynccontextmanager

from consumer import redis_client
from database import SessionLocal
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from routes import messages
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from consumer import run_consumer

    stop_event = threading.Event()
    thread = threading.Thread(
        target=run_consumer,
        kwargs={'stop_event': stop_event},
        daemon=True,
    )
    thread.start()
    yield
    stop_event.set()
    thread.join(timeout=3)


app = FastAPI(lifespan=lifespan)


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.get('/health/live')
async def health_live():
    return {'status': 'live'}


@app.get('/health/ready')
async def health_ready():
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1'))
        redis_client.ping()
    except RedisError:
        return JSONResponse(
            status_code=503,
            content={'status': 'not_ready', 'dependency': 'redis'},
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={'status': 'not_ready', 'dependency': 'postgres'},
        )
    finally:
        db.close()
    return {'status': 'ready'}


app.include_router(
    messages.router,
    prefix='/api/messaging/messages',
    tags=['messages'],
)
