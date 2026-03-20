from models.user import Driver
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from utils import create_access_token


def register(username: str, password: str, db: Session) -> Driver | None:
    new_driver = Driver(username=username, password=password)
    try:
        db.add(new_driver)
        db.commit()
        return new_driver
    except IntegrityError:
        db.rollback()
        return None


def login(username: str, password: str, db: Session) -> str | None:
    driver = (
        db.query(Driver)
        .filter(Driver.username == username, Driver.password == password)
        .first()
    )
    if not driver:
        return None
    return create_access_token(str(driver.driver_id))
