from application.use_cases import LoginDriverUseCase, RegisterDriverUseCase
from fastapi import APIRouter, Depends, HTTPException
from infrastructure.dependencies import get_db_connection
from infrastructure.http.schemas import (
    DriverResponse,
    LoginDriverDto,
    RegisterDriverDto,
)
from infrastructure.repositories.driver_repository import PostgresDriverRepository
from infrastructure.utils import create_access_token
from sqlalchemy.orm import Session

router = APIRouter()


def get_register_use_case(
    db: Session = Depends(get_db_connection),
) -> RegisterDriverUseCase:
    return RegisterDriverUseCase(PostgresDriverRepository(db))


def get_login_use_case(db: Session = Depends(get_db_connection)) -> LoginDriverUseCase:
    return LoginDriverUseCase(PostgresDriverRepository(db))


@router.post('/register', status_code=201)
def register(
    dto: RegisterDriverDto,
    use_case: RegisterDriverUseCase = Depends(get_register_use_case),
):
    driver = use_case.execute(
        name=dto.name,
        email=dto.email,
        password=dto.password,
        license_number=dto.license_number,
        vehicle_type=dto.vehicle_type,
        region=dto.region,
    )
    if driver is None:
        raise HTTPException(status_code=409, detail='Email already registered')

    token = create_access_token(str(driver.driver_id))
    return {
        'driver': DriverResponse(
            driver_id=str(driver.driver_id),
            name=driver.name,
            email=driver.email,
            license_number=driver.license_number,
            vehicle_type=driver.vehicle_type,
            region=driver.region,
            created_at=driver.created_at,
        ),
        'access_token': token,
    }


@router.post('/login', status_code=200)
def login(
    dto: LoginDriverDto,
    use_case: LoginDriverUseCase = Depends(get_login_use_case),
):
    result = use_case.execute(dto.email, dto.password)
    if result is None:
        raise HTTPException(status_code=401, detail='Invalid credentials')

    driver, token = result
    return {
        'driver': DriverResponse(
            driver_id=str(driver.driver_id),
            name=driver.name,
            email=driver.email,
            license_number=driver.license_number,
            vehicle_type=driver.vehicle_type,
            region=driver.region,
            created_at=driver.created_at,
        ),
        'access_token': token,
    }
