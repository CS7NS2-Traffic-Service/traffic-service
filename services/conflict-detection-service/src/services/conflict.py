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
    """Check whether all segments have capacity for the requested window.

    For each segment, counts overlapping reservations and compares
    against the segment's capacity. Returns False as soon as any
    segment is at capacity.
    """
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
    """Create a reservation on every segment for the given booking.

    All reservations are inserted inside a savepoint so they either
    all succeed or all roll back.
    """
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
    """Delete all reservations tied to a booking. Returns delete count."""
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
    """Count overlapping reservations per segment for the given time window."""
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
    """Atomically check capacity and create reservations.

    Uses SELECT ... FOR UPDATE on the relevant road_segments rows to
    serialise concurrent assessments that share any segment, preventing
    double-booking race conditions.
    """
    start_time = departure_time
    end_time = departure_time + timedelta(seconds=duration_seconds)

    # Lock the relevant road_segments rows in a consistent order to
    # avoid deadlocks (sorted by segment_id).
    sorted_ids = sorted(segment_ids)

    segments = (
        db.query(RoadSegment)
        .filter(RoadSegment.segment_id.in_(sorted_ids))
        .order_by(RoadSegment.segment_id)
        .with_for_update()
        .all()
    )

    # Build a lookup for capacity
    capacity_map: dict[str, int] = {}
    for seg in segments:
        capacity_map[str(seg.segment_id)] = seg.capacity or 0

    # If any requested segment is missing from the database, reject.
    if len(capacity_map) != len(sorted_ids):
        return AssessRouteResponse(
            booking_id=booking_id,
            route_id=route_id,
            segments_available=False,
        )

    # Count overlapping reservations per segment
    for sid in sorted_ids:
        overlap_count = (
            db.query(func.count())
            .select_from(SegmentReservation)
            .filter(
                SegmentReservation.segment_id == sid,
                SegmentReservation.time_window_start < end_time,
                SegmentReservation.time_window_end > start_time,
            )
            .scalar()
        )

        if overlap_count >= capacity_map[sid]:
            return AssessRouteResponse(
                booking_id=booking_id,
                route_id=route_id,
                segments_available=False,
            )

    # All segments have capacity -- create reservations
    for sid in sorted_ids:
        db.add(
            SegmentReservation(
                booking_id=booking_id,
                segment_id=sid,
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
