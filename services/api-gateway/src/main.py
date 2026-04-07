import logging
import os
import uuid

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from jose import JWTError, jwt
from redis.exceptions import ConnectionError as RedisConnectionError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = httpx.AsyncClient()

JWT_SECRET_KEY = os.environ.get(
    'JWT_SECRET_KEY',
    'super-secret-key-change-in-prod',
)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379')
redis_client = aioredis.from_url(
    REDIS_URL,
    decode_responses=True,
)

BFF_URL = os.getenv('BFF_URL', 'http://bff:8080')

PUBLIC_PATHS = {
    ('POST', '/api/driver/auth/login'),
    ('POST', '/api/driver/auth/register'),
}


def get_service_url(service: str) -> str | None:
    return os.getenv(f'SERVICE_{service.upper().replace("-", "_")}')


def is_public(method: str, path: str) -> bool:
    if path in {'/health', '/health/live', '/health/ready'}:
        return True
    if not path.startswith('/api/'):
        return True
    return (method, path) in PUBLIC_PATHS


async def check_rate_limit(driver_id: str) -> bool:
    try:
        key = f'rate_limit:{driver_id}'
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)
        return count <= 100
    except RedisConnectionError:
        return True


@app.middleware('http')
async def auth_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path

    if is_public(method, path):
        return await call_next(request)

    auth_header = request.headers.get('authorization', '')
    if not auth_header.startswith('Bearer '):
        return JSONResponse(
            status_code=401,
            content={'detail': 'Missing or invalid token'},
        )

    token = auth_header.removeprefix('Bearer ')
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=['HS256'],
        )
        driver_id = payload.get('sub')
        if not driver_id:
            raise JWTError('Missing sub claim')
    except JWTError:
        return JSONResponse(
            status_code=401,
            content={'detail': 'Invalid or expired token'},
        )

    if not await check_rate_limit(driver_id):
        return JSONResponse(
            status_code=429,
            content={'detail': 'Rate limit exceeded'},
        )

    request.state.driver_id = driver_id
    return await call_next(request)


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.get('/health/live')
async def health_live():
    return {'status': 'live'}


@app.get('/health/ready')
async def health_ready():
    try:
        await redis_client.ping()
    except RedisConnectionError:
        return JSONResponse(
            status_code=503,
            content={'status': 'not_ready', 'dependency': 'redis'},
        )
    return {'status': 'ready'}


STRIP_REQUEST_HEADERS = {
    'host',
    'content-length',
    'transfer-encoding',
    'connection',
}
STRIP_RESPONSE_HEADERS = {
    'content-encoding',
    'transfer-encoding',
    'content-length',
    'connection',
}


async def proxy(
    request: Request,
    target: str,
) -> StreamingResponse:
    url = target + request.url.path
    if request.url.query:
        url += f'?{request.url.query}'

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in STRIP_REQUEST_HEADERS
    }
    driver_id = getattr(request.state, 'driver_id', None)
    if driver_id:
        headers['x-driver-id'] = driver_id
    correlation_id = request.headers.get('x-correlation-id') or str(uuid.uuid4())
    headers['x-correlation-id'] = correlation_id

    resp = await client.request(
        method=request.method,
        url=url,
        headers=headers,
        content=await request.body(),
    )
    resp_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in STRIP_RESPONSE_HEADERS
    }
    resp_headers['x-correlation-id'] = correlation_id
    return StreamingResponse(
        resp.aiter_bytes(),
        status_code=resp.status_code,
        headers=resp_headers,
    )


@app.api_route(
    '/api/{service}/{_:path}',
    methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
)
async def route_to_service(
    service: str,
    _: str,
    request: Request,
):
    target = get_service_url(service)
    if not target:
        return JSONResponse(
            status_code=404,
            content={'error': f'Unknown service: {service}'},
        )
    return await proxy(request, target)


@app.api_route(
    '/{_:path}',
    methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
)
async def route_to_bff(_: str, request: Request):
    return await proxy(request, BFF_URL)
