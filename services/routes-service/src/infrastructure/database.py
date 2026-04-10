import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

connection_string = os.environ.get(
    'DATABASE_URL', 'postgresql://traffic:traffic@postgres:5432/traffic'
)
replica_string = os.environ.get('DATABASE_REPLICA_URL', connection_string)

engine = create_engine(connection_string, echo=True)
read_engine = create_engine(replica_string, echo=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
ReadSessionLocal = sessionmaker(bind=read_engine, autocommit=False, autoflush=False)

BaseDBModel = declarative_base()
