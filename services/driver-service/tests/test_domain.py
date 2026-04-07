from datetime import UTC, datetime

import pytest
from domain.driver import Driver


class TestDriver:
    def test_create_driver(self):
        driver = Driver(
            driver_id='123e4567-e89b-12d3-a456-426614174000',
            name='John Doe',
            email='john@example.com',
            password_hash='hashed_password',
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )
        assert driver.name == 'John Doe'
        assert driver.email == 'john@example.com'
        assert driver.vehicle_type == 'CAR'

    def test_driver_is_immutable(self):
        driver = Driver(
            driver_id='123e4567-e89b-12d3-a456-426614174000',
            name='John Doe',
            email='john@example.com',
            password_hash='hashed_password',
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )
        with pytest.raises(AttributeError):
            driver.name = 'Jane Doe'

    def test_driver_with_null_vehicle_type(self):
        driver = Driver(
            driver_id='123e4567-e89b-12d3-a456-426614174000',
            name='John Doe',
            email='john@example.com',
            password_hash='hashed_password',
            license_number='DL123456',
            vehicle_type=None,
            region='Dublin',
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )
        assert driver.vehicle_type is None
