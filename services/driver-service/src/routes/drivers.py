from dependencies import get_db_connection
from fastapi import APIRouter, Depends, Header, HTTPException
from schemas import DriverResponse
from services.auth import get_driver_profile
from sqlalchemy.orm import Session

router = APIRouter()


@router.get('/me', status_code=200)
def me(
    x_driver_id: str = Header(...),
    db: Session = Depends(get_db_connection),
):
    driver = get_driver_profile(x_driver_id, db)
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
