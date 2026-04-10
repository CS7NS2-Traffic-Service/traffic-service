from application.conflict_service import ConflictService
from fastapi import APIRouter, Depends

from infrastructure.dependencies import get_conflict_service
from infrastructure.http.schemas import (
    RouteAvailabilityItem,
    RouteAvailabilityRequest,
    RouteAvailabilityResponse,
)

router = APIRouter()


@router.post('/availability', response_model=RouteAvailabilityResponse)
def availability(
    body: RouteAvailabilityRequest,
    service: ConflictService = Depends(get_conflict_service),
) -> RouteAvailabilityResponse:
    results = service.check_routes_availability(
        candidates=[
            {
                'route_id': r.route_id,
                'segment_ids': r.segment_ids,
                'estimated_duration': r.estimated_duration,
            }
            for r in body.routes
        ],
        departure_time=body.departure_time,
    )
    items = [
        RouteAvailabilityItem(route_id=rid, available=avail)
        for rid, avail in results.items()
    ]
    return RouteAvailabilityResponse(routes=items)
