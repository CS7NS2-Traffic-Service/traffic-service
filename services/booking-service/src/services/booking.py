from uuid import UUID

from domain import BookingStatus, parse_status, to_utc, transition
from events import publish_event
from models.booking import Booking
from sqlalchemy.orm import Session


def create_booking(
    driver_id: str,
    route_id: str,
    departure_time,
    estimated_arrival,
    db: Session,
) -> Booking:
    departure_time = to_utc(departure_time)
    if estimated_arrival is not None:
        estimated_arrival = to_utc(estimated_arrival)
        if estimated_arrival < departure_time:
            raise ValueError('estimated_arrival must be >= departure_time')

    new_booking = Booking(
        driver_id=driver_id,
        route_id=route_id,
        departure_time=departure_time,
        estimated_arrival=estimated_arrival,
        status=BookingStatus.PENDING.value,
        expires_at=departure_time,
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    publish_event(
        'booking.created',
        {
            'booking_id': str(new_booking.booking_id),
            'driver_id': str(new_booking.driver_id),
            'route_id': str(new_booking.route_id),
            'departure_time': new_booking.departure_time.isoformat(),
        },
    )

    return new_booking


def get_booking(booking_id: str, db: Session) -> Booking | None:
    try:
        booking_uuid = UUID(booking_id)
    except ValueError:
        return None
    return db.query(Booking).filter(Booking.booking_id == booking_uuid).first()


def list_bookings(driver_id: str, db: Session) -> list[Booking]:
    return db.query(Booking).filter(Booking.driver_id == driver_id).all()


def cancel_booking(booking_id: str, driver_id: str, db: Session) -> Booking | None:
    try:
        booking_uuid = UUID(booking_id)
        driver_uuid = UUID(driver_id)
    except ValueError:
        return None

    booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == booking_uuid,
            Booking.driver_id == driver_uuid,
        )
        .first()
    )
    if booking is None:
        return None
    current = parse_status(booking.status)
    if current == BookingStatus.CANCELLED:
        return booking
    if current not in {BookingStatus.PENDING, BookingStatus.APPROVED}:
        raise ValueError(f'Booking cannot be cancelled when status is {current.value}')

    booking.status = transition(current, BookingStatus.CANCELLED).value
    db.commit()
    db.refresh(booking)

    publish_event(
        'booking.updated',
        {
            'booking_id': str(booking.booking_id),
            'driver_id': str(booking.driver_id),
            'status': booking.status,
        },
    )

    return booking
