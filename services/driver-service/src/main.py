from fastapi import FastAPI
from routes import auth

app = FastAPI()


@app.get('/health')
async def health():
    return {'status': 'ok'}


app.include_router(auth.router, prefix='/api/driver/auth', tags=['auth'])
