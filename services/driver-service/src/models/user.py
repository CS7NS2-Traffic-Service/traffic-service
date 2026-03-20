from datetime import datetime
from uuid import uuid4

from database import BaseDBModel
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID


class Driver(BaseDBModel):
    __tablename__ = 'drivers'
    driver_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
