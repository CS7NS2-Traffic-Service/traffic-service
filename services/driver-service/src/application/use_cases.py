import bcrypt
from application.interfaces import DriverRepository
from domain.driver import Driver
from infrastructure.utils import create_access_token


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


class RegisterDriverUseCase:
    def __init__(self, driver_repo: DriverRepository) -> None:
        self._driver_repo = driver_repo

    def execute(
        self,
        name: str,
        email: str,
        password: str,
        license_number: str,
        vehicle_type: str | None,
        region: str,
    ) -> Driver | None:
        password_hash = hash_password(password)
        return self._driver_repo.create(
            name=name,
            email=email,
            password_hash=password_hash,
            license_number=license_number,
            vehicle_type=vehicle_type,
            region=region,
        )


class LoginDriverUseCase:
    def __init__(self, driver_repo: DriverRepository) -> None:
        self._driver_repo = driver_repo

    def execute(self, email: str, password: str) -> tuple[Driver, str] | None:
        driver = self._driver_repo.get_by_email(email)
        if driver is None:
            return None

        if not verify_password(password, driver.password_hash):
            return None

        token = create_access_token(str(driver.driver_id))
        return driver, token


class GetDriverProfileUseCase:
    def __init__(self, driver_repo: DriverRepository) -> None:
        self._driver_repo = driver_repo

    def execute(self, driver_id: str) -> Driver | None:
        return self._driver_repo.get_by_id(driver_id)
