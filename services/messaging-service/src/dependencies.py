from database import ReadSessionLocal, SessionLocal


def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_db_connection():
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()
