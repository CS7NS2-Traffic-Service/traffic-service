import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from routes.reservations import router as reservations_router
from routes.utilization import router as utilization_router
from sqlalchemy import text

from consumer import redis_client
from database import SessionLocal

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from consumer import run_consumer, run_updated_consumer

    stop_event = threading.Event()
    booking_thread = threading.Thread(
        target=run_consumer,
        kwargs={'stop_event': stop_event},
        daemon=True,
    )
    updated_thread = threading.Thread(
        target=run_updated_consumer,
        kwargs={'stop_event': stop_event},
        daemon=True,
    )
    booking_thread.start()
    updated_thread.start()
    yield
    stop_event.set()
    booking_thread.join(timeout=3)
    updated_thread.join(timeout=3)


app = FastAPI(lifespan=lifespan)

app.include_router(utilization_router, prefix='/api/conflict-detection')
app.include_router(reservations_router, prefix='/api/conflict-detection')


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
