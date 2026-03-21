from datetime import datetime

from pydantic import BaseModel


class RegisterDriverDto(BaseModel):
    name: str
    email: str
    password: str
    license_number: str
    vehicle_type: str
    region: str


class LoginDriverDto(BaseModel):
    email: str
    password: str


class DriverResponse(BaseModel):
    driver_id: str
    name: str
    email: str
    license_number: str
    vehicle_type: str | None
    region: str
    created_at: datetime
