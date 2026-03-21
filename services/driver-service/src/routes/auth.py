from dependencies import get_db_connection
from fastapi import APIRouter, Depends, HTTPException
from schemas import DriverResponse, LoginDriverDto, RegisterDriverDto
from services.auth import login as login_driver
from services.auth import register as register_driver
from sqlalchemy.orm import Session
from utils import create_access_token

router = APIRouter()


@router.post('/register', status_code=201)
def register(dto: RegisterDriverDto, db: Session = Depends(get_db_connection)):
    driver = register_driver(
        name=dto.name,
        email=dto.email,
        password=dto.password,
        license_number=dto.license_number,
        vehicle_type=dto.vehicle_type,
        region=dto.region,
        db=db,
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
def login(dto: LoginDriverDto, db: Session = Depends(get_db_connection)):
    result = login_driver(dto.email, dto.password, db)
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
