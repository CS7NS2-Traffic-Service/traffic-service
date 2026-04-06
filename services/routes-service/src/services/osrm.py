import os

import httpx
from fastapi import HTTPException

OSRM_URL = os.environ.get('OSRM_URL', 'http://osrm:5555')


def _extract_steps_with_edges(leg: dict) -> list[dict]:
    annotation = leg.get('annotation', {})
    nodes = annotation.get('nodes', [])
    steps = leg.get('steps', [])

    if len(nodes) < 2:
        return []

    node_index = 0
    result = []
    for step in steps:
        num_coords = len(step.get('geometry', {}).get('coordinates', []))
        num_edges = max(num_coords - 1, 0)

        if step.get('distance', 0) > 0 and num_edges > 0:
            edge_ids = []
            for i in range(node_index, node_index + num_edges):
                if i < len(nodes) - 1:
                    a, b = nodes[i], nodes[i + 1]
                    edge_ids.append(f'{min(a, b)}-{max(a, b)}')

            if edge_ids:
                result.append(
                    {
                        'name': step.get('name', '') or 'unnamed',
                        'edge_ids': edge_ids,
                    }
                )

        if num_coords > 1:
            node_index += num_edges

    return result


def query_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> dict:
    url = (
        f'{OSRM_URL}/route/v1/driving/'
        f'{origin_lng},{origin_lat};{dest_lng},{dest_lat}'
        f'?overview=full&geometries=geojson&annotations=true&steps=true'
    )

    try:
        response = httpx.get(url, timeout=10.0)
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

    steps_with_edges = []
    for leg in osrm_route.get('legs', []):
        steps_with_edges.extend(_extract_steps_with_edges(leg))

    return {
        'geometry': osrm_route.get('geometry'),
        'duration': osrm_route.get('duration'),
        'steps': steps_with_edges,
    }
