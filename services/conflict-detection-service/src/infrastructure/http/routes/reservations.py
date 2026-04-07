from application.conflict_service import ConflictService
from fastapi import APIRouter, Depends

from infrastructure.dependencies import get_conflict_service
from infrastructure.http.schemas import ReservationItem

router = APIRouter()


@router.get(
    '/bookings/{booking_id}/reservations',
    response_model=list[ReservationItem],
)
def get_booking_reservations(
    booking_id: str,
    service: ConflictService = Depends(get_conflict_service),
) -> list[ReservationItem]:
    reservations = service.get_reservations_by_booking(booking_id)
    return [
        ReservationItem(
            reservation_id=str(r.reservation_id),
            segment_id=str(r.segment_id),
            time_window_start=r.time_window_start,
            time_window_end=r.time_window_end,
        )
        for r in reservations
    ]
