from collections.abc import Generator

from database import SessionLocal
from fastapi import APIRouter, Depends
from models.segment_reservation import SegmentReservation
from schemas import ReservationItem
from sqlalchemy.orm import Session

router = APIRouter()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    '/bookings/{booking_id}/reservations',
    response_model=list[ReservationItem],
)
def get_booking_reservations(
    booking_id: str,
    db: Session = Depends(get_db),
) -> list[ReservationItem]:
    rows = (
        db.query(SegmentReservation)
        .filter(SegmentReservation.booking_id == booking_id)
        .order_by(SegmentReservation.time_window_start)
        .all()
    )
    return [
        ReservationItem(
            reservation_id=str(r.reservation_id),
            segment_id=str(r.segment_id),
            time_window_start=r.time_window_start,
            time_window_end=r.time_window_end,
        )
        for r in rows
    ]
