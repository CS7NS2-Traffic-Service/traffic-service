from datetime import datetime, timedelta

from models.road_segment import RoadSegment
from models.segment_reservation import SegmentReservation
from schemas import AssessRouteResponse
from sqlalchemy import func
from sqlalchemy.orm import Session


def check_segments_available(
    segment_ids: list[str],
    departure_time: datetime,
    duration_seconds: int,
    db: Session,
) -> bool:
    start_time = departure_time
    end_time = departure_time + timedelta(seconds=duration_seconds)

    for segment_id in segment_ids:
        overlap_count = (
            db.query(func.count())
            .select_from(SegmentReservation)
            .filter(
                SegmentReservation.segment_id == segment_id,
                SegmentReservation.time_window_start < end_time,
                SegmentReservation.time_window_end > start_time,
            )
            .scalar()
        )

        segment = (
            db.query(RoadSegment).filter(RoadSegment.segment_id == segment_id).first()
        )

        if segment is None:
            return False

        capacity = segment.capacity or 0
        if overlap_count >= capacity:
            return False

    return True


def create_reservations(
    booking_id: str,
    segment_ids: list[str],
    departure_time: datetime,
    duration_seconds: int,
    db: Session,
) -> None:
    start_time = departure_time
    end_time = departure_time + timedelta(seconds=duration_seconds)

    nested = db.begin_nested()
    try:
        for segment_id in segment_ids:
            reservation = SegmentReservation(
                booking_id=booking_id,
                segment_id=segment_id,
                time_window_start=start_time,
                time_window_end=end_time,
            )
            db.add(reservation)
        nested.commit()
    except Exception:
        nested.rollback()
        raise


def delete_reservations(booking_id: str, db: Session) -> int:
    count = (
        db.query(SegmentReservation)
        .filter(SegmentReservation.booking_id == booking_id)
        .delete()
    )
    db.commit()
    return count


def get_segment_utilization(
    segment_ids: list[str],
    window_start: datetime,
    window_end: datetime,
    db: Session,
) -> dict[str, int]:
    rows = (
        db.query(
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


def assess_and_reserve(
    booking_id: str,
    route_id: str,
    segment_ids: list[str],
    departure_time: datetime,
    duration_seconds: int,
    db: Session,
) -> AssessRouteResponse:
    start_time = departure_time
    end_time = departure_time + timedelta(seconds=duration_seconds)

    segment_ids = sorted(segment_ids)

    capacity_by_segment_id = _calc_capcity_by_segment_id(segment_ids, db)

    if len(capacity_by_segment_id) != len(segment_ids):
        return AssessRouteResponse(
            booking_id=booking_id,
            route_id=route_id,
            segments_available=False,
        )

    for segment_id in segment_ids:
        overlap_count = (
            db.query(func.count())
            .select_from(SegmentReservation)
            .filter(
                SegmentReservation.segment_id == segment_id,
                SegmentReservation.time_window_start < end_time,
                SegmentReservation.time_window_end > start_time,
            )
            .scalar()
        )

        if overlap_count >= capacity_by_segment_id[segment_id]:
            return AssessRouteResponse(
                booking_id=booking_id,
                route_id=route_id,
                segments_available=False,
            )

    for segment_id in segment_ids:
        db.add(
            SegmentReservation(
                booking_id=booking_id,
                segment_id=segment_id,
                time_window_start=start_time,
                time_window_end=end_time,
            )
        )
    db.commit()

    return AssessRouteResponse(
        booking_id=booking_id,
        route_id=route_id,
        segments_available=True,
    )


def _calc_capcity_by_segment_id(segment_ids: list[str], db: Session):
    segments = (
        db.query(RoadSegment)
        .filter(RoadSegment.segment_id.in_(segment_ids))
        .order_by(RoadSegment.segment_id)
        .with_for_update()
        .all()
    )

    capacity_by_segment_id: dict[str, int] = {}
    for segment in segments:
        capacity_by_segment_id[str(segment.segment_id)] = segment.capacity or 0
    return capacity_by_segment_id
