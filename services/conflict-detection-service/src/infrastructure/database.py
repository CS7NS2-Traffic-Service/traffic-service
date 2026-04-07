import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://traffic:traffic@postgres:5432/traffic',
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
BaseDBModel = declarative_base()
