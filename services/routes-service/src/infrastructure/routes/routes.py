from application.use_cases import (
    CreateRouteUseCase,
    GetRouteSegmentsUseCase,
    GetRouteUseCase,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from infrastructure.dependencies import get_db_connection
from infrastructure.http.schemas import RouteResponse, SegmentResponse
from infrastructure.osrm.client import OSRMClient
from infrastructure.repositories.route_repository import (
    PostgresRouteRepository,
    PostgresSegmentRepository,
)
from sqlalchemy.orm import Session

router = APIRouter()


def get_route_repo(db: Session = Depends(get_db_connection)):
    return PostgresRouteRepository(db)


def get_segment_repo(db: Session = Depends(get_db_connection)):
    return PostgresSegmentRepository(db)


def get_osrm_client():
    return OSRMClient()


def get_create_route_use_case(
    db: Session = Depends(get_db_connection),
) -> CreateRouteUseCase:
    return CreateRouteUseCase(
        route_repo=PostgresRouteRepository(db),
        segment_repo=PostgresSegmentRepository(db),
        osrm_client=OSRMClient(),
    )


def get_route_use_case(db: Session = Depends(get_db_connection)) -> GetRouteUseCase:
    return GetRouteUseCase(PostgresRouteRepository(db))


def get_segments_use_case(db: Session = Depends(get_db_connection)):
    return GetRouteSegmentsUseCase(
        route_repo=PostgresRouteRepository(db),
        segment_repo=PostgresSegmentRepository(db),
    )


@router.get('', status_code=200)
def lookup_route(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lng: float = Query(..., ge=-180, le=180),
    use_case: CreateRouteUseCase = Depends(get_create_route_use_case),
) -> RouteResponse:
    route = use_case.execute(origin_lat, origin_lng, dest_lat, dest_lng)
    return RouteResponse(
        route_id=str(route.route_id),
        origin=route.origin,
        destination=route.destination,
        segment_ids=route.segment_ids,
        geometry=route.geometry,
        estimated_duration=route.estimated_duration,
        created_at=route.created_at,
    )


@router.get('/{route_id}', status_code=200)
def get_route(
    route_id: str,
    use_case: GetRouteUseCase = Depends(get_route_use_case),
) -> RouteResponse:
    route = use_case.execute(route_id)
    if route is None:
        raise HTTPException(status_code=404, detail='Route not found')
    return RouteResponse(
        route_id=str(route.route_id),
        origin=route.origin,
        destination=route.destination,
        segment_ids=route.segment_ids,
        geometry=route.geometry,
        estimated_duration=route.estimated_duration,
        created_at=route.created_at,
    )


@router.get('/{route_id}/segments', status_code=200)
def get_segments(
    route_id: str,
    use_case: GetRouteSegmentsUseCase = Depends(get_segments_use_case),
) -> list[SegmentResponse]:
    segments = use_case.execute(route_id)
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
