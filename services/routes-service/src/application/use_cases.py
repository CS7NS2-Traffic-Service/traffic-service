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
    ) -> list[Route]:
        origin = f'{origin_lat},{origin_lng}'
        destination = f'{dest_lat},{dest_lng}'

        existing = self._route_repo.find_by_origin_destination(origin, destination)
        if existing:
            return existing

        osrm_results = self._osrm_client.query_route(
            origin_lat, origin_lng, dest_lat, dest_lng
        )

        routes = []
        for osrm_result in osrm_results:
            segment_ids = self._create_segments(osrm_result['steps'])
            route = self._route_repo.create(
                origin=origin,
                destination=destination,
                segment_ids=segment_ids,
                geometry=osrm_result.get('geometry'),
                estimated_duration=int(osrm_result.get('duration', 0)),
            )
            routes.append(route)

        return routes

    def _create_segments(self, steps: list[dict]) -> list[str]:
        segment_ids: list[str] = []
        seen: set[str] = set()

        for step in steps:
            step_edges = set(step['edge_ids'])
            overlapping = self._segment_repo.find_all_overlapping(list(step_edges))

            for seg in overlapping:
                if seg.segment_id not in seen:
                    segment_ids.append(seg.segment_id)
                    seen.add(seg.segment_id)
                step_edges -= set(seg.edge_ids or [])

            if step_edges:
                new_seg = self._segment_repo.create(
                    osm_way_id=_edge_hash(sorted(step_edges)),
                    name=step.get('name') or 'unnamed',
                    region='',
                    capacity=5,
                    edge_ids=sorted(step_edges),
                )
                segment_ids.append(new_seg.segment_id)
                seen.add(new_seg.segment_id)

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
