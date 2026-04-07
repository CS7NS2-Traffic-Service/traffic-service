from datetime import datetime

from domain.reservation import Reservation
from sqlalchemy import func
from sqlalchemy.orm import Session

from infrastructure.postgres.models.segment_reservation import SegmentReservation


class PostgresReservationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def count_overlapping(self, segment_id: str, start: datetime, end: datetime) -> int:
        return (
            self._db.query(func.count())
            .select_from(SegmentReservation)
            .filter(
                SegmentReservation.segment_id == segment_id,
                SegmentReservation.time_window_start < end,
                SegmentReservation.time_window_end > start,
            )
            .scalar()
        )

    def create(
        self,
        booking_id: str,
        segment_id: str,
        start: datetime,
        end: datetime,
    ) -> None:
        self._db.add(
            SegmentReservation(
                booking_id=booking_id,
                segment_id=segment_id,
                time_window_start=start,
                time_window_end=end,
            )
        )

    def delete_by_booking(self, booking_id: str) -> int:
        return (
            self._db.query(SegmentReservation)
            .filter(SegmentReservation.booking_id == booking_id)
            .delete()
        )

    def get_by_booking(self, booking_id: str) -> list[Reservation]:
        rows = (
            self._db.query(SegmentReservation)
            .filter(SegmentReservation.booking_id == booking_id)
            .order_by(SegmentReservation.time_window_start)
            .all()
        )
        return [
            Reservation(
                reservation_id=r.reservation_id,
                segment_id=r.segment_id,
                time_window_start=r.time_window_start,
                time_window_end=r.time_window_end,
            )
            for r in rows
        ]

    def get_utilization(
        self,
        segment_ids: list[str],
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, int]:
        rows = (
            self._db.query(
                SegmentReservation.segment_id,
                func.count().label('cnt'),
            )
            .filter(
                SegmentReservation.segment_id.in_(segment_ids),
                SegmentReservation.time_window_start < window_end,
                SegmentReservation.time_window_end > window_start,
            )
            .group_by(SegmentReservation.segment_id)
            .all()
        )
        result: dict[str, int] = {sid: 0 for sid in segment_ids}
        for segment_id, cnt in rows:
            result[str(segment_id)] = cnt
        return result
