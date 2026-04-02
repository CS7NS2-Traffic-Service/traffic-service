from contextlib import asynccontextmanager

from dependencies import get_db_connection
from fastapi import FastAPI
from routes import auth, drivers
from services.auth import register


def seed_test_driver():
    db = next(get_db_connection())
    register(
        name='Test Driver',
        email='test@example.com',
        password='password123',
        license_number='TEST123',
        vehicle_type='CAR',
        region='Dublin',
        db=db,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_test_driver()
    yield


app = FastAPI(lifespan=lifespan)


@app.get('/health')
async def health():
    return {'status': 'ok'}


app.include_router(auth.router, prefix='/api/driver/auth', tags=['auth'])
app.include_router(drivers.router, prefix='/api/driver/drivers', tags=['drivers'])
