from dependencies import get_db_connection
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routes import routes
from sqlalchemy import text

app = FastAPI()


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


app.include_router(routes.router, prefix='/api/routes/routes', tags=['routes'])
