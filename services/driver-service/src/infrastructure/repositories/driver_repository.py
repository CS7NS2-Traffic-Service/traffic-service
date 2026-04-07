from datetime import datetime

from domain.driver import Driver
from infrastructure.models.driver import Driver as DriverORM
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class PostgresDriverRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        license_number: str,
        vehicle_type: str | None,
        region: str,
    ) -> Driver | None:
        new_driver = DriverORM(
            name=name,
            email=email,
            password_hash=password_hash,
            license_number=license_number,
            vehicle_type=vehicle_type,
            region=region,
        )
        try:
            self._db.add(new_driver)
            self._db.commit()
            self._db.refresh(new_driver)
            return self._to_domain(new_driver)
        except IntegrityError:
            self._db.rollback()
            return None

    def get_by_email(self, email: str) -> Driver | None:
        row = self._db.query(DriverORM).filter(DriverORM.email == email).first()
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_id(self, driver_id: str) -> Driver | None:
        row = self._db.query(DriverORM).filter(DriverORM.driver_id == driver_id).first()
        if row is None:
            return None
        return self._to_domain(row)

    def _to_domain(self, orm: DriverORM) -> Driver:
        return Driver(
            driver_id=str(orm.driver_id),
            name=orm.name,
            email=orm.email,
            password_hash=orm.password_hash,
            license_number=orm.license_number,
            vehicle_type=orm.vehicle_type,
            region=orm.region,
            created_at=orm.created_at or datetime.now(),
        )
