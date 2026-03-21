import hashlib
import json

from models.road_segment import RoadSegment
from models.route import Route
from sqlalchemy.orm import Session

from services.osrm import query_route


def _geometry_hash(geometry: dict) -> str:
    coords = geometry.get('coordinates', [])
    rounded = [[round(c, 5) for c in point] for point in coords]
    raw = json.dumps(rounded, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _find_or_create_segments(steps: list[dict], db: Session) -> list[str]:
    segment_ids = []
    for step in steps:
        geo_hash = _geometry_hash(step['geometry'])

        existing = (
            db.query(RoadSegment).filter(RoadSegment.osm_way_id == geo_hash).first()
        )
        if existing:
            segment_ids.append(str(existing.segment_id))
            continue

        coords = step['geometry'].get('coordinates', [])
        first_coord = coords[0] if coords else [0, 0]
        region = f'{round(first_coord[1], 2)},{round(first_coord[0], 2)}'

        segment = RoadSegment(
            osm_way_id=geo_hash,
            name=step.get('name') or 'unnamed',
            region=region,
            capacity=5,
            coordinates=step['geometry'],
        )
        db.add(segment)
        db.flush()
        segment_ids.append(str(segment.segment_id))

    return segment_ids


def get_route_by_id(route_id: str, db: Session) -> Route | None:
    return db.query(Route).filter(Route.route_id == route_id).first()


async def find_or_create_route(
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

    osrm_result = await query_route(origin_lat, origin_lng, dest_lat, dest_lng)

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
