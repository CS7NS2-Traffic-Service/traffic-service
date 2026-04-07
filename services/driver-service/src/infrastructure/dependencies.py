from infrastructure.database import SessionLocal


def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
