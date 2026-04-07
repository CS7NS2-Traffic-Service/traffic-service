from domain.route import Route
from sqlalchemy.orm import Session

from infrastructure.postgres.models.route import Route as RouteORM


class PostgresRouteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, route_id: str) -> Route | None:
        row = self._db.query(RouteORM).filter(RouteORM.route_id == route_id).first()
        if row is None:
            return None
        return Route(
            route_id=str(row.route_id),
            segment_ids=[str(sid) for sid in (row.segment_ids or [])],
            estimated_duration=row.estimated_duration or 3600,
        )
