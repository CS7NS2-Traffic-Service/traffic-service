from dependencies import get_db_connection
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas import RouteResponse, SegmentResponse
from services.route import (
    find_or_create_route,
    get_route_by_id,
    get_route_segments,
)
from sqlalchemy.orm import Session

router = APIRouter()


@router.get('', status_code=200)
def lookup_route(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lng: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db_connection),
) -> RouteResponse:
    route = find_or_create_route(origin_lat, origin_lng, dest_lat, dest_lng, db)
    return RouteResponse(
        route_id=str(route.route_id),
        origin=route.origin,
        destination=route.destination,
        segment_ids=(
            [str(sid) for sid in route.segment_ids] if route.segment_ids else None
        ),
        geometry=route.geometry,
        estimated_duration=route.estimated_duration,
        created_at=route.created_at,
    )


@router.get('/{route_id}', status_code=200)
def get_route(
    route_id: str,
    db: Session = Depends(get_db_connection),
) -> RouteResponse:
    route = get_route_by_id(route_id, db)
    if route is None:
        raise HTTPException(status_code=404, detail='Route not found')
    return RouteResponse(
        route_id=str(route.route_id),
        origin=route.origin,
        destination=route.destination,
        segment_ids=(
            [str(sid) for sid in route.segment_ids] if route.segment_ids else None
        ),
        geometry=route.geometry,
        estimated_duration=route.estimated_duration,
        created_at=route.created_at,
    )


@router.get('/{route_id}/segments', status_code=200)
def get_segments(
    route_id: str,
    db: Session = Depends(get_db_connection),
) -> list[SegmentResponse]:
    segments = get_route_segments(route_id, db)
    if segments is None:
        raise HTTPException(status_code=404, detail='Route not found')
    return [
        SegmentResponse(
            segment_id=str(s.segment_id),
            osm_way_id=s.osm_way_id,
            name=s.name,
            region=s.region,
            capacity=s.capacity,
            coordinates=s.coordinates,
        )
        for s in segments
    ]
