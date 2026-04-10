from typing import Protocol

from domain.route import Route
from domain.segment import RoadSegment


class RouteRepository(Protocol):
    def get_by_id(self, route_id: str) -> Route | None: ...

    def find_by_origin_destination(
        self, origin: str, destination: str
    ) -> list[Route]: ...

    def create(
        self,
        origin: str,
        destination: str,
        segment_ids: list[str],
        geometry: dict | None,
        estimated_duration: int,
    ) -> Route | None: ...


class SegmentRepository(Protocol):
    def get_by_id(self, segment_id: str) -> RoadSegment | None: ...

    def get_by_ids(self, segment_ids: list[str]) -> list[RoadSegment]: ...

    def find_all_overlapping(self, edge_ids: list[str]) -> list[RoadSegment]: ...

    def create(
        self,
        osm_way_id: str,
        name: str,
        region: str,
        capacity: int,
        edge_ids: list[str],
    ) -> RoadSegment: ...


class OSRMClient(Protocol):
    def query_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> list[dict]: ...
