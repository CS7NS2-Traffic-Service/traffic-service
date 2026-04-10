from application.conflict_service import ConflictService
from fastapi import APIRouter, Depends

from infrastructure.dependencies import get_conflict_service
from infrastructure.http.schemas import (
    SegmentUtilizationItem,
    SegmentUtilizationRequest,
    SegmentUtilizationResponse,
)

router = APIRouter()


@router.post('/utilization', response_model=SegmentUtilizationResponse)
def utilization(
    body: SegmentUtilizationRequest,
    service: ConflictService = Depends(get_conflict_service),
) -> SegmentUtilizationResponse:
    counts = service.get_segment_utilization(
        segments=[s.model_dump() for s in body.segments],
    )
    items = [
        SegmentUtilizationItem(
            segment_id=s.segment_id, active_reservations=counts.get(s.segment_id, 0)
        )
        for s in body.segments
    ]
    return SegmentUtilizationResponse(utilization=items)
