from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

connection_string = 'postgresql://traffic:traffic@postgres:5432/traffic'

engine = create_engine(connection_string, echo=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

BaseDBModel = declarative_base()
