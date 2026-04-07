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
        segment_ids=body.segment_ids,
        window_start=body.window_start,
        window_end=body.window_end,
    )
    items = [
        SegmentUtilizationItem(segment_id=sid, active_reservations=counts.get(sid, 0))
        for sid in body.segment_ids
    ]
    return SegmentUtilizationResponse(utilization=items)
