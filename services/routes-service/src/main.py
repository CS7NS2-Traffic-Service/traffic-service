from fastapi import FastAPI
from routes import routes

app = FastAPI()


@app.get('/health')
async def health():
    return {'status': 'ok'}


app.include_router(routes.router, prefix='/api/routes/routes', tags=['routes'])
