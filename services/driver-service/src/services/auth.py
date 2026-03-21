import bcrypt
from models.user import Driver
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from utils import create_access_token


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def register(
    name: str,
    email: str,
    password: str,
    license_number: str,
    vehicle_type: str,
    region: str,
    db: Session,
) -> Driver | None:
    new_driver = Driver(
        name=name,
        email=email,
        password_hash=hash_password(password),
        license_number=license_number,
        vehicle_type=vehicle_type,
        region=region,
    )
    try:
        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)
        return new_driver
    except IntegrityError:
        db.rollback()
        return None


def login(email: str, password: str, db: Session) -> tuple[Driver, str] | None:
    driver = db.query(Driver).filter(Driver.email == email).first()
    if not driver or not verify_password(password, driver.password_hash):
        return None
    token = create_access_token(str(driver.driver_id))
    return driver, token


def get_driver_profile(driver_id: str, db: Session) -> Driver | None:
    return db.query(Driver).filter(Driver.driver_id == driver_id).first()
