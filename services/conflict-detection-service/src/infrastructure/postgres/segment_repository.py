from sqlalchemy.orm import Session

from infrastructure.postgres.models.road_segment import RoadSegment


class PostgresSegmentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_capacities(self, segment_ids: list[str]) -> dict[str, int]:
        segments = (
            self._db.query(RoadSegment)
            .filter(RoadSegment.segment_id.in_(segment_ids))
            .order_by(RoadSegment.segment_id)
            .with_for_update()
            .all()
        )
        return {str(s.segment_id): s.capacity or 0 for s in segments}
