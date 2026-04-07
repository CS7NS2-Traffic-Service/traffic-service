from datetime import datetime

from domain.route import Route
from domain.segment import RoadSegment
from infrastructure.models.road_segment import RoadSegment as RoadSegmentORM
from infrastructure.models.route import Route as RouteORM
from sqlalchemy.orm import Session


class PostgresRouteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, route_id: str) -> Route | None:
        row = self._db.query(RouteORM).filter(RouteORM.route_id == route_id).first()
        if row is None:
            return None
        return self._to_domain(row)

    def find_by_origin_destination(self, origin: str, destination: str) -> Route | None:
        row = (
            self._db.query(RouteORM)
            .filter(RouteORM.origin == origin, RouteORM.destination == destination)
            .first()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def create(
        self,
        origin: str,
        destination: str,
        segment_ids: list[str],
        geometry: dict | None,
        estimated_duration: int,
    ) -> Route:
        new_route = RouteORM(
            origin=origin,
            destination=destination,
            segment_ids=segment_ids,
            geometry=geometry,
            estimated_duration=estimated_duration,
        )
        self._db.add(new_route)
        self._db.commit()
        self._db.refresh(new_route)
        return self._to_domain(new_route)

    def _to_domain(self, orm: RouteORM) -> Route:
        return Route(
            route_id=str(orm.route_id),
            origin=orm.origin,
            destination=orm.destination,
            segment_ids=[str(sid) for sid in (orm.segment_ids or [])],
            geometry=orm.geometry,
            estimated_duration=orm.estimated_duration,
            created_at=orm.created_at or datetime.now(),
        )


class PostgresSegmentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, segment_id: str) -> RoadSegment | None:
        row = (
            self._db.query(RoadSegmentORM)
            .filter(RoadSegmentORM.segment_id == segment_id)
            .first()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_ids(self, segment_ids: list[str]) -> list[RoadSegment]:
        rows = (
            self._db.query(RoadSegmentORM)
            .filter(RoadSegmentORM.segment_id.in_(segment_ids))
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def find_overlapping(self, edge_ids: list[str]) -> RoadSegment | None:
        segments = (
            self._db.query(RoadSegmentORM)
            .filter(RoadSegmentORM.edge_ids.isnot(None))
            .all()
        )
        for segment in segments:
            stored_edges = set(segment.edge_ids or [])
            if stored_edges & set(edge_ids):
                return self._to_domain(segment)
        return None

    def create(
        self,
        osm_way_id: str,
        name: str,
        region: str,
        capacity: int,
        edge_ids: list[str],
    ) -> RoadSegment:
        segment = RoadSegmentORM(
            osm_way_id=osm_way_id,
            name=name,
            region=region,
            capacity=capacity,
            edge_ids=edge_ids,
        )
        self._db.add(segment)
        self._db.flush()
        return self._to_domain(segment)

    def _to_domain(self, orm: RoadSegmentORM) -> RoadSegment:
        return RoadSegment(
            segment_id=str(orm.segment_id),
            osm_way_id=orm.osm_way_id,
            name=orm.name,
            region=orm.region,
            capacity=orm.capacity,
            coordinates=orm.coordinates,
            edge_ids=orm.edge_ids,
        )
