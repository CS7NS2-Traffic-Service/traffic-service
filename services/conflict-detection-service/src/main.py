import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes.reservations import router as reservations_router
from routes.utilization import router as utilization_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from consumer import run_consumer, run_updated_consumer

    threading.Thread(target=run_consumer, daemon=True).start()
    threading.Thread(target=run_updated_consumer, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(utilization_router, prefix='/api/conflict-detection')
app.include_router(reservations_router, prefix='/api/conflict-detection')


@app.get('/health')
async def health():
    return {'status': 'ok'}
