from datetime import UTC, datetime

import pytest
from domain.route import Route
from domain.segment import RoadSegment


class TestRoute:
    def test_create_route(self):
        route = Route(
            route_id='123e4567-e89b-12d3-a456-426614174000',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=['seg-1', 'seg-2'],
            geometry={'type': 'LineString', 'coordinates': []},
            estimated_duration=3600,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )
        assert route.origin == '53.3498,-6.2603'
        assert route.destination == '53.1424,-7.6921'
        assert len(route.segment_ids) == 2

    def test_route_is_immutable(self):
        route = Route(
            route_id='123e4567-e89b-12d3-a456-426614174000',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=['seg-1'],
            geometry=None,
            estimated_duration=3600,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )
        with pytest.raises(AttributeError):
            route.origin = 'different'

    def test_route_with_null_segment_ids(self):
        route = Route(
            route_id='123e4567-e89b-12d3-a456-426614174000',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=None,
            geometry=None,
            estimated_duration=0,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )
        assert route.segment_ids is None


class TestRoadSegment:
    def test_create_segment(self):
        segment = RoadSegment(
            segment_id='123e4567-e89b-12d3-a456-426614174000',
            osm_way_id='abc123',
            name='Main Street',
            region='Dublin',
            capacity=5,
            coordinates={'type': 'Point', 'coordinates': [-6.26, 53.34]},
            edge_ids=['1-2', '2-3'],
        )
        assert segment.name == 'Main Street'
        assert segment.capacity == 5
        assert len(segment.edge_ids) == 2

    def test_segment_is_immutable(self):
        segment = RoadSegment(
            segment_id='123e4567-e89b-12d3-a456-426614174000',
            osm_way_id='abc123',
            name='Main Street',
            region='Dublin',
            capacity=5,
            coordinates=None,
            edge_ids=None,
        )
        with pytest.raises(AttributeError):
            segment.name = 'Different Street'

    def test_segment_with_null_fields(self):
        segment = RoadSegment(
            segment_id='123e4567-e89b-12d3-a456-426614174000',
            osm_way_id=None,
            name='Main Street',
            region='Dublin',
            capacity=None,
            coordinates=None,
            edge_ids=None,
        )
        assert segment.osm_way_id is None
        assert segment.capacity is None
        assert segment.edge_ids is None
