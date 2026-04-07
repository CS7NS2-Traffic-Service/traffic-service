from typing import Protocol

from domain.driver import Driver


class DriverRepository(Protocol):
    def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        license_number: str,
        vehicle_type: str | None,
        region: str,
    ) -> Driver | None: ...

    def get_by_email(self, email: str) -> Driver | None: ...

    def get_by_id(self, driver_id: str) -> Driver | None: ...
