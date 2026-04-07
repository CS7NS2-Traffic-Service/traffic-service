from application.use_cases import GetDriverProfileUseCase
from fastapi import APIRouter, Depends, Header, HTTPException
from infrastructure.dependencies import get_db_connection
from infrastructure.http.schemas import DriverResponse
from infrastructure.repositories.driver_repository import PostgresDriverRepository
from sqlalchemy.orm import Session

router = APIRouter()


def get_profile_use_case(
    db: Session = Depends(get_db_connection),
) -> GetDriverProfileUseCase:
    return GetDriverProfileUseCase(PostgresDriverRepository(db))


@router.get('/me', status_code=200)
def me(
    x_driver_id: str = Header(...),
    use_case: GetDriverProfileUseCase = Depends(get_profile_use_case),
):
    driver = use_case.execute(x_driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail='Driver not found')
    return DriverResponse(
        driver_id=str(driver.driver_id),
        name=driver.name,
        email=driver.email,
        license_number=driver.license_number,
        vehicle_type=driver.vehicle_type,
        region=driver.region,
        created_at=driver.created_at,
    )
