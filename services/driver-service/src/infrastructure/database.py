import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

connection_string = os.environ.get(
    'DATABASE_URL', 'postgresql://traffic:traffic@postgres:5432/traffic'
)

engine = create_engine(connection_string, echo=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

BaseDBModel = declarative_base()
