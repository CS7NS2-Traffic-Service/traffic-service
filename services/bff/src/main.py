import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount(
    '/assets', StaticFiles(directory='traffic-frontend/dist/assets'), name='assets'
)


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.get('/health/live')
async def health_live():
    return {'status': 'live'}


@app.get('/health/ready')
async def health_ready():
    if not os.path.isfile('traffic-frontend/dist/index.html'):
        return JSONResponse(
            status_code=503,
            content={'status': 'not_ready', 'dependency': 'frontend_assets'},
        )
    return {'status': 'ready'}


@app.get('/')
async def serve_index():
    return FileResponse('traffic-frontend/dist/index.html')


@app.get('/{full_path:path}')
async def serve_frontend(full_path: str):
    file_path = f'traffic-frontend/dist/{full_path}'
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse('traffic-frontend/dist/index.html')
