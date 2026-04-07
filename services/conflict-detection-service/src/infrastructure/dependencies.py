from application.conflict_service import ConflictService
from fastapi import Depends
from sqlalchemy.orm import Session

from infrastructure.database import SessionLocal
from infrastructure.postgres.reservation_repository import PostgresReservationRepository
from infrastructure.postgres.route_repository import PostgresRouteRepository
from infrastructure.postgres.segment_repository import PostgresSegmentRepository


def get_db_connection():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_conflict_service(db: Session = Depends(get_db_connection)) -> ConflictService:
    return ConflictService(
        route_repo=PostgresRouteRepository(db),
        segment_repo=PostgresSegmentRepository(db),
        reservation_repo=PostgresReservationRepository(db),
    )
