from dependencies import get_db_connection
from domain import BookingStatus
from fastapi import APIRouter, Depends, Header, HTTPException
from schemas import BookingResponse, CreateBookingDto
from services.booking import cancel_booking, create_booking, get_booking, list_bookings
from sqlalchemy.orm import Session

router = APIRouter()


def _to_response(booking) -> BookingResponse:
    return BookingResponse(
        booking_id=str(booking.booking_id),
        driver_id=str(booking.driver_id),
        route_id=str(booking.route_id),
        departure_time=booking.departure_time,
        estimated_arrival=booking.estimated_arrival,
        status=BookingStatus(booking.status),
        created_at=booking.created_at,
        expires_at=booking.expires_at,
    )


@router.post('', status_code=202)
def create(
    dto: CreateBookingDto,
    x_driver_id: str = Header(...),
    db: Session = Depends(get_db_connection),
):
    try:
        booking = create_booking(
            driver_id=x_driver_id,
            route_id=dto.route_id,
            departure_time=dto.departure_time,
            estimated_arrival=dto.estimated_arrival,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return _to_response(booking)


@router.get('', status_code=200)
def list_all(
    x_driver_id: str = Header(...),
    db: Session = Depends(get_db_connection),
):
    bookings = list_bookings(x_driver_id, db)
    return [_to_response(b) for b in bookings]


@router.get('/{booking_id}', status_code=200)
def get_one(
    booking_id: str,
    db: Session = Depends(get_db_connection),
):
    booking = get_booking(booking_id, db)
    if booking is None:
        raise HTTPException(status_code=404, detail='Booking not found')
    return _to_response(booking)


@router.delete('/{booking_id}', status_code=200)
def cancel(
    booking_id: str,
    x_driver_id: str = Header(...),
    db: Session = Depends(get_db_connection),
):
    try:
        booking = cancel_booking(booking_id, x_driver_id, db)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    if booking is None:
        raise HTTPException(status_code=404, detail='Booking not found')
    return _to_response(booking)
