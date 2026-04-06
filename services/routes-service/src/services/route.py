import hashlib

from models.road_segment import RoadSegment
from models.route import Route
from sqlalchemy.orm import Session

from services.osrm import query_route


def _find_overlapping_segment(edge_ids: list[str], db: Session) -> RoadSegment | None:
    segments = db.query(RoadSegment).filter(RoadSegment.edge_ids.isnot(None)).all()
    for segment in segments:
        stored_edges = set(segment.edge_ids)
        if stored_edges & set(edge_ids):
            return segment
    return None


def _edge_hash(edge_ids: list[str]) -> str:
    raw = ','.join(sorted(edge_ids))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _find_or_create_segments(steps: list[dict], db: Session) -> list[str]:
    segment_ids = []
    seen_segment_ids = set()

    for step in steps:
        edge_ids = step['edge_ids']

        existing = _find_overlapping_segment(edge_ids, db)
        if existing:
            sid = str(existing.segment_id)
            if sid not in seen_segment_ids:
                segment_ids.append(sid)
                seen_segment_ids.add(sid)
            continue

        segment = RoadSegment(
            osm_way_id=_edge_hash(edge_ids),
            name=step.get('name') or 'unnamed',
            region='',
            capacity=5,
            edge_ids=edge_ids,
        )
        db.add(segment)
        db.flush()
        sid = str(segment.segment_id)
        segment_ids.append(sid)
        seen_segment_ids.add(sid)

    return segment_ids


def get_route_by_id(route_id: str, db: Session) -> Route | None:
    return db.query(Route).filter(Route.route_id == route_id).first()


def find_or_create_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    db: Session,
) -> Route:
    origin = f'{origin_lat},{origin_lng}'
    destination = f'{dest_lat},{dest_lng}'

    existing = (
        db.query(Route)
        .filter(Route.origin == origin, Route.destination == destination)
        .first()
    )
    if existing:
        return existing

    osrm_result = query_route(origin_lat, origin_lng, dest_lat, dest_lng)

    segment_ids = _find_or_create_segments(osrm_result['steps'], db)

    new_route = Route(
        origin=origin,
        destination=destination,
        segment_ids=segment_ids,
        geometry=osrm_result.get('geometry'),
        estimated_duration=int(osrm_result.get('duration', 0)),
    )
    db.add(new_route)
    db.commit()
    db.refresh(new_route)
    return new_route


def get_route_segments(route_id: str, db: Session) -> list[RoadSegment] | None:
    route = get_route_by_id(route_id, db)
    if route is None:
        return None

    if not route.segment_ids:
        return []

    segments = (
        db.query(RoadSegment)
        .filter(RoadSegment.segment_id.in_(route.segment_ids))
        .all()
    )

    segment_map = {str(s.segment_id): s for s in segments}
    return [
        segment_map[str(sid)] for sid in route.segment_ids if str(sid) in segment_map
    ]
