import os

import httpx
from fastapi import HTTPException

OSRM_URL = os.environ.get('OSRM_URL', 'http://osrm:5000')


async def query_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> dict:
    """Query OSRM for a driving route between two coordinates.

    OSRM uses longitude,latitude order in its URL format.
    Returns dict with geometry (GeoJSON), duration (seconds),
    and the raw OSRM response legs.
    """
    url = (
        f'{OSRM_URL}/route/v1/driving/'
        f'{origin_lng},{origin_lat};{dest_lng},{dest_lat}'
        f'?overview=full&geometries=geojson&annotations=true&steps=true'
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        raise HTTPException(
            status_code=503,
            detail='OSRM routing service is unavailable',
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=f'OSRM returned an error: {exc.response.status_code}',
        ) from exc

    data = response.json()

    if data.get('code') != 'Ok' or not data.get('routes'):
        raise HTTPException(
            status_code=404,
            detail='No route found between the given coordinates',
        )

    osrm_route = data['routes'][0]

    steps = []
    for leg in osrm_route.get('legs', []):
        for step in leg.get('steps', []):
            if step.get('distance', 0) > 0 and step.get('geometry'):
                steps.append(
                    {
                        'name': step.get('name', ''),
                        'geometry': step['geometry'],
                        'distance': step['distance'],
                        'duration': step.get('duration', 0),
                    }
                )

    return {
        'geometry': osrm_route.get('geometry'),
        'duration': osrm_route.get('duration'),
        'legs': osrm_route.get('legs', []),
        'steps': steps,
    }
