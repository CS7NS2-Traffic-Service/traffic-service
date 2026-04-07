from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Driver:
    driver_id: str
    name: str
    email: str
    password_hash: str
    license_number: str
    vehicle_type: str | None
    region: str
    created_at: datetime
