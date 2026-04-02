from dependencies import get_db_connection
from fastapi import APIRouter, Depends
from schemas import (
    SegmentUtilizationItem,
    SegmentUtilizationRequest,
    SegmentUtilizationResponse,
)
from services.conflict import get_segment_utilization
from sqlalchemy.orm import Session

router = APIRouter()


@router.post('/utilization', response_model=SegmentUtilizationResponse)
def utilization(
    body: SegmentUtilizationRequest,
    db: Session = Depends(get_db_connection),
) -> SegmentUtilizationResponse:
    counts = get_segment_utilization(
        segment_ids=body.segment_ids,
        window_start=body.window_start,
        window_end=body.window_end,
        db=db,
    )
    items = [
        SegmentUtilizationItem(segment_id=sid, active_reservations=counts.get(sid, 0))
        for sid in body.segment_ids
    ]
    return SegmentUtilizationResponse(utilization=items)
