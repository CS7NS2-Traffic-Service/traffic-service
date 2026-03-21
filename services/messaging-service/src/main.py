import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes import messages

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from consumer import run_consumer

    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.get('/health')
async def health():
    return {'status': 'ok'}


app.include_router(
    messages.router,
    prefix='/api/messaging/messages',
    tags=['messages'],
)
