import hashlib

from application.interfaces import OSRMClient, RouteRepository, SegmentRepository
from domain.route import Route
from domain.segment import RoadSegment


def _edge_hash(edge_ids: list[str]) -> str:
    raw = ','.join(sorted(edge_ids))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class GetRouteUseCase:
    def __init__(self, route_repo: RouteRepository) -> None:
        self._route_repo = route_repo

    def execute(self, route_id: str) -> Route | None:
        return self._route_repo.get_by_id(route_id)


class CreateRouteUseCase:
    def __init__(
        self,
        route_repo: RouteRepository,
        segment_repo: SegmentRepository,
        osrm_client: OSRMClient,
    ) -> None:
        self._route_repo = route_repo
        self._segment_repo = segment_repo
        self._osrm_client = osrm_client

    def execute(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> Route:
        origin = f'{origin_lat},{origin_lng}'
        destination = f'{dest_lat},{dest_lng}'

        existing = self._route_repo.find_by_origin_destination(origin, destination)
        if existing:
            return existing

        osrm_result = self._osrm_client.query_route(
            origin_lat, origin_lng, dest_lat, dest_lng
        )

        segment_ids = self._create_segments(osrm_result['steps'])

        route = self._route_repo.create(
            origin=origin,
            destination=destination,
            segment_ids=segment_ids,
            geometry=osrm_result.get('geometry'),
            estimated_duration=int(osrm_result.get('duration', 0)),
        )

        return route

    def _create_segments(self, steps: list[dict]) -> list[str]:
        segment_ids = []
        seen_segment_ids = set()

        for step in steps:
            edge_ids = step['edge_ids']

            existing = self._segment_repo.find_overlapping(edge_ids)
            if existing:
                sid = existing.segment_id
                if sid not in seen_segment_ids:
                    segment_ids.append(sid)
                    seen_segment_ids.add(sid)
                continue

            segment = self._segment_repo.create(
                osm_way_id=_edge_hash(edge_ids),
                name=step.get('name') or 'unnamed',
                region='',
                capacity=5,
                edge_ids=edge_ids,
            )
            segment_ids.append(segment.segment_id)
            seen_segment_ids.add(segment.segment_id)

        return segment_ids


class GetRouteSegmentsUseCase:
    def __init__(
        self, route_repo: RouteRepository, segment_repo: SegmentRepository
    ) -> None:
        self._route_repo = route_repo
        self._segment_repo = segment_repo

    def execute(self, route_id: str) -> list[RoadSegment] | None:
        route = self._route_repo.get_by_id(route_id)
        if route is None:
            return None

        if not route.segment_ids:
            return []

        segments = self._segment_repo.get_by_ids(route.segment_ids)
        segment_map = {s.segment_id: s for s in segments}
        return [segment_map[sid] for sid in route.segment_ids if sid in segment_map]


def extract_steps_with_edges(leg: dict) -> list[dict]:
    annotation = leg.get('annotation', {})
    nodes = annotation.get('nodes', [])
    steps = leg.get('steps', [])

    if len(nodes) < 2:
        return []

    node_index = 0
    result = []
    for step in steps:
        num_coords = len(step.get('geometry', {}).get('coordinates', []))
        num_edges = max(num_coords - 1, 0)

        if step.get('distance', 0) > 0 and num_edges > 0:
            edge_ids = []
            for i in range(node_index, node_index + num_edges):
                if i < len(nodes) - 1:
                    a, b = nodes[i], nodes[i + 1]
                    edge_ids.append(f'{min(a, b)}-{max(a, b)}')

            if edge_ids:
                result.append(
                    {
                        'name': step.get('name', '') or 'unnamed',
                        'edge_ids': edge_ids,
                    }
                )

        if num_coords > 1:
            node_index += num_edges

    return result
