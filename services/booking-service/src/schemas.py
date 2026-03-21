from datetime import datetime

from pydantic import BaseModel


class CreateBookingDto(BaseModel):
    route_id: str
    departure_time: datetime
    estimated_arrival: datetime | None = None


class BookingResponse(BaseModel):
    booking_id: str
    driver_id: str
    route_id: str
    departure_time: datetime
    estimated_arrival: datetime | None
    status: str
    created_at: datetime | None
    expires_at: datetime | None
