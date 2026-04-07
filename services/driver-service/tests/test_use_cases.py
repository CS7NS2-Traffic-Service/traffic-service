from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from application.use_cases import (
    GetDriverProfileUseCase,
    LoginDriverUseCase,
    RegisterDriverUseCase,
    hash_password,
    verify_password,
)
from domain.driver import Driver


class TestPasswordUtils:
    def test_hash_password_returns_string(self):
        hashed = hash_password('testpassword')
        assert isinstance(hashed, str)
        assert hashed != 'testpassword'

    def test_hash_password_is_unique(self):
        hashed1 = hash_password('testpassword')
        hashed2 = hash_password('testpassword')
        assert hashed1 != hashed2

    def test_verify_password_correct(self):
        hashed = hash_password('testpassword')
        assert verify_password('testpassword', hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password('testpassword')
        assert verify_password('wrongpassword', hashed) is False


class TestRegisterDriverUseCase:
    @pytest.fixture
    def mock_driver_repo(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_driver_repo):
        return RegisterDriverUseCase(mock_driver_repo)

    def test_execute_creates_driver(self, use_case, mock_driver_repo):
        mock_driver_repo.create.return_value = Driver(
            driver_id='123e4567-e89b-12d3-a456-426614174000',
            name='John Doe',
            email='john@example.com',
            password_hash='hashed',
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute(
            name='John Doe',
            email='john@example.com',
            password='testpassword',
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
        )

        assert result is not None
        assert result.name == 'John Doe'
        mock_driver_repo.create.assert_called_once()

    def test_execute_returns_none_on_integrity_error(self, use_case, mock_driver_repo):
        mock_driver_repo.create.return_value = None

        result = use_case.execute(
            name='John Doe',
            email='john@example.com',
            password='testpassword',
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
        )

        assert result is None


class TestLoginDriverUseCase:
    @pytest.fixture
    def mock_driver_repo(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_driver_repo):
        return LoginDriverUseCase(mock_driver_repo)

    def test_execute_success(self, use_case, mock_driver_repo):
        mock_driver_repo.get_by_email.return_value = Driver(
            driver_id='123e4567-e89b-12d3-a456-426614174000',
            name='John Doe',
            email='john@example.com',
            password_hash=hash_password('testpassword'),
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute('john@example.com', 'testpassword')

        assert result is not None
        driver, token = result
        assert driver.name == 'John Doe'
        assert token is not None

    def test_execute_returns_none_when_driver_not_found(
        self, use_case, mock_driver_repo
    ):
        mock_driver_repo.get_by_email.return_value = None

        result = use_case.execute('john@example.com', 'testpassword')

        assert result is None

    def test_execute_returns_none_on_invalid_password(self, use_case, mock_driver_repo):
        mock_driver_repo.get_by_email.return_value = Driver(
            driver_id='123e4567-e89b-12d3-a456-426614174000',
            name='John Doe',
            email='john@example.com',
            password_hash=hash_password('testpassword'),
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute('john@example.com', 'wrongpassword')

        assert result is None


class TestGetDriverProfileUseCase:
    @pytest.fixture
    def mock_driver_repo(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_driver_repo):
        return GetDriverProfileUseCase(mock_driver_repo)

    def test_execute_returns_driver(self, use_case, mock_driver_repo):
        mock_driver_repo.get_by_id.return_value = Driver(
            driver_id='123e4567-e89b-12d3-a456-426614174000',
            name='John Doe',
            email='john@example.com',
            password_hash='hashed',
            license_number='DL123456',
            vehicle_type='CAR',
            region='Dublin',
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute('123e4567-e89b-12d3-a456-426614174000')

        assert result is not None
        assert result.name == 'John Doe'

    def test_execute_returns_none_when_not_found(self, use_case, mock_driver_repo):
        mock_driver_repo.get_by_id.return_value = None

        result = use_case.execute('nonexistent-id')

        assert result is None
