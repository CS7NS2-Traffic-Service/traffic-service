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
    new_booking = Booking(
        driver_id=driver_id,
        route_id=route_id,
        departure_time=departure_time,
        estimated_arrival=estimated_arrival,
        status='PENDING',
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
    return db.query(Booking).filter(Booking.booking_id == booking_id).first()


def list_bookings(driver_id: str, db: Session) -> list[Booking]:
    return db.query(Booking).filter(Booking.driver_id == driver_id).all()


def cancel_booking(booking_id: str, driver_id: str, db: Session) -> Booking | None:
    booking = (
        db.query(Booking)
        .filter(
            Booking.booking_id == booking_id,
            Booking.driver_id == driver_id,
        )
        .first()
    )
    if booking is None:
        return None
    if booking.status == 'CANCELLED':
        return None
    booking.status = 'CANCELLED'
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
