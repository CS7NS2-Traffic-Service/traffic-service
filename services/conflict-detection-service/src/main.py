import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from infrastructure.consumer.consumer import redis_client
from infrastructure.database import SessionLocal
from infrastructure.http.routes.reservations import router as reservations_router
from infrastructure.http.routes.utilization import router as utilization_router
from redis.exceptions import RedisError
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from infrastructure.consumer.consumer import run_consumer, run_updated_consumer
    from infrastructure.outbox_relay.relay import run_cleanup, run_relay

    stop_event = threading.Event()
    kwargs = {'stop_event': stop_event}
    threads = [
        threading.Thread(target=run_consumer, kwargs=kwargs, daemon=True),
        threading.Thread(target=run_updated_consumer, kwargs=kwargs, daemon=True),
        threading.Thread(target=run_relay, kwargs=kwargs, daemon=True),
        threading.Thread(target=run_cleanup, kwargs=kwargs, daemon=True),
    ]
    for t in threads:
        t.start()
    yield
    stop_event.set()
    for t in threads:
        t.join(timeout=3)


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
