from dependencies import get_db_connection
from fastapi import APIRouter, Depends, HTTPException
from schemas import LoginDriverDto, RegisterDriverDto
from services.auth import login as login_driver
from services.auth import register as register_driver
from sqlalchemy.orm import Session

router = APIRouter()


@router.post('/register', status_code=201)
def register(dto: RegisterDriverDto, db: Session = Depends(get_db_connection)):
    new_driver = register_driver(dto.username, dto.password, db)
    if new_driver is None:
        raise HTTPException(status_code=409, detail='Error while creating user')
    return {'driver_id': str(new_driver.driver_id), 'username': new_driver.username}


@router.post('/login', status_code=200)
def login(dto: LoginDriverDto, db: Session = Depends(get_db_connection)):
    access_token = login_driver(dto.username, dto.password, db)
    if access_token is None:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return {'access_token': access_token, 'username': dto.username}
