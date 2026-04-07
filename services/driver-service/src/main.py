import os
from contextlib import asynccontextmanager

from application.use_cases import RegisterDriverUseCase
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from infrastructure.dependencies import get_db_connection
from infrastructure.repositories.driver_repository import PostgresDriverRepository
from infrastructure.routes import auth, drivers
from sqlalchemy import text


def seed_test_driver():
    db = next(get_db_connection())
    use_case = RegisterDriverUseCase(PostgresDriverRepository(db))
    use_case.execute(
        name='Test Driver',
        email='test@example.com',
        password='password123',
        license_number='TEST123',
        vehicle_type='CAR',
        region='Dublin',
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if (
        os.environ.get('APP_ENV', 'development') == 'development'
        and os.environ.get('SEED_TEST_USER', 'true').lower() == 'true'
    ):
        seed_test_driver()
    yield


app = FastAPI(lifespan=lifespan)


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.get('/health/live')
async def health_live():
    return {'status': 'live'}


@app.get('/health/ready')
async def health_ready():
    db = None
    try:
        db = next(get_db_connection())
        db.execute(text('SELECT 1'))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={'status': 'not_ready', 'dependency': 'postgres'},
        )
    finally:
        if db is not None:
            db.close()
    return {'status': 'ready'}


app.include_router(auth.router, prefix='/api/driver/auth', tags=['auth'])
app.include_router(drivers.router, prefix='/api/driver/drivers', tags=['drivers'])
