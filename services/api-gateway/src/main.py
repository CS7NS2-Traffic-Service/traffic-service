import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()
client = httpx.AsyncClient()


@app.get('/health')
async def health():
    return {'status': 'ok'}


def get_service_url(service: str) -> str | None:
    return os.getenv(f'SERVICE_{service.upper()}')


BFF_URL = os.getenv('BFF_URL', 'http://bff:8080')


async def proxy(request: Request, target: str) -> StreamingResponse:
    url = target + request.url.path

    if request.url.query:
        url += f'?{request.url.query}'

    resp = await client.request(
        method=request.method,
        url=url,
        headers=dict(request.headers),
        content=await request.body(),
    )
    return StreamingResponse(
        resp.aiter_bytes(),
        status_code=resp.status_code,
        headers=dict(resp.headers),
    )


@app.api_route(
    '/api/{service}/{_:path}',
    methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
)
async def route_to_service(service: str, _: str, request: Request):
    target = get_service_url(service)

    if not target:
        return {'error': f'Unknown service: {service}'}, 404

    return await proxy(request, target)


@app.api_route('/{_:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
async def route_to_bff(_: str, request: Request):
    return await proxy(request, BFF_URL)
