from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from application.use_cases import (
    CreateRouteUseCase,
    GetRouteSegmentsUseCase,
    GetRouteUseCase,
    extract_steps_with_edges,
)


class TestGetRouteUseCase:
    @pytest.fixture
    def mock_route_repo(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_route_repo):
        return GetRouteUseCase(mock_route_repo)

    def test_execute_returns_route(self, use_case, mock_route_repo):
        from domain.route import Route

        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=['seg-1', 'seg-2'],
            geometry={'type': 'LineString'},
            estimated_duration=3600,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute('route-123')

        assert result is not None
        assert result.route_id == 'route-123'

    def test_execute_returns_none_when_not_found(self, use_case, mock_route_repo):
        mock_route_repo.get_by_id.return_value = None

        result = use_case.execute('nonexistent')

        assert result is None


class TestCreateRouteUseCase:
    @pytest.fixture
    def mock_route_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_segment_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_osrm_client(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_route_repo, mock_segment_repo, mock_osrm_client):
        return CreateRouteUseCase(mock_route_repo, mock_segment_repo, mock_osrm_client)

    def test_execute_returns_existing_route(
        self, use_case, mock_route_repo, mock_osrm_client
    ):
        from domain.route import Route

        mock_route_repo.find_by_origin_destination.return_value = Route(
            route_id='existing-route',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=['seg-1'],
            geometry=None,
            estimated_duration=3600,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute(53.3498, -6.2603, 53.1424, -7.6921)

        assert result.route_id == 'existing-route'
        mock_osrm_client.query_route.assert_not_called()

    def test_execute_creates_new_route(
        self, use_case, mock_route_repo, mock_segment_repo, mock_osrm_client
    ):
        from domain.route import Route
        from domain.segment import RoadSegment

        mock_route_repo.find_by_origin_destination.return_value = None
        mock_osrm_client.query_route.return_value = {
            'geometry': {'type': 'LineString'},
            'duration': 3600,
            'steps': [
                {'name': 'Main St', 'edge_ids': ['1-2', '2-3']},
            ],
        }
        mock_segment_repo.find_overlapping.return_value = None
        mock_segment_repo.create.return_value = RoadSegment(
            segment_id='seg-1',
            osm_way_id='abc123',
            name='Main St',
            region='',
            capacity=5,
            coordinates=None,
            edge_ids=['1-2', '2-3'],
        )
        mock_route_repo.create.return_value = Route(
            route_id='new-route',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=['seg-1'],
            geometry={'type': 'LineString'},
            estimated_duration=3600,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute(53.3498, -6.2603, 53.1424, -7.6921)

        assert result.route_id == 'new-route'
        mock_osrm_client.query_route.assert_called_once()


class TestGetRouteSegmentsUseCase:
    @pytest.fixture
    def mock_route_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_segment_repo(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_route_repo, mock_segment_repo):
        return GetRouteSegmentsUseCase(mock_route_repo, mock_segment_repo)

    def test_execute_returns_segments(
        self, use_case, mock_route_repo, mock_segment_repo
    ):
        from domain.route import Route
        from domain.segment import RoadSegment

        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=['seg-1', 'seg-2'],
            geometry=None,
            estimated_duration=3600,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )
        mock_segment_repo.get_by_ids.return_value = [
            RoadSegment(
                segment_id='seg-1',
                osm_way_id='abc',
                name='Street 1',
                region='Dublin',
                capacity=5,
                coordinates=None,
                edge_ids=None,
            ),
            RoadSegment(
                segment_id='seg-2',
                osm_way_id='def',
                name='Street 2',
                region='Dublin',
                capacity=3,
                coordinates=None,
                edge_ids=None,
            ),
        ]

        result = use_case.execute('route-123')

        assert len(result) == 2
        assert result[0].segment_id == 'seg-1'
        assert result[1].segment_id == 'seg-2'

    def test_execute_returns_none_when_route_not_found(self, use_case, mock_route_repo):
        mock_route_repo.get_by_id.return_value = None

        result = use_case.execute('nonexistent')

        assert result is None

    def test_execute_returns_empty_list_when_no_segments(
        self, use_case, mock_route_repo
    ):
        from domain.route import Route

        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            origin='53.3498,-6.2603',
            destination='53.1424,-7.6921',
            segment_ids=None,
            geometry=None,
            estimated_duration=3600,
            created_at=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        result = use_case.execute('route-123')

        assert result == []


class TestExtractStepsWithEdges:
    def test_single_step_produces_correct_edges(self):
        leg = {
            'annotation': {'nodes': [100, 200, 300]},
            'steps': [
                {
                    'name': 'Lime Street',
                    'distance': 100,
                    'geometry': {'coordinates': [[0, 0], [1, 1], [2, 2]]},
                }
            ],
        }
        result = extract_steps_with_edges(leg)
        assert len(result) == 1
        assert result[0]['name'] == 'Lime Street'
        assert result[0]['edge_ids'] == ['100-200', '200-300']

    def test_edge_ids_are_direction_independent(self):
        leg = {
            'annotation': {'nodes': [500, 200, 800]},
            'steps': [
                {
                    'name': 'Main Road',
                    'distance': 100,
                    'geometry': {'coordinates': [[0, 0], [1, 1], [2, 2]]},
                }
            ],
        }
        result = extract_steps_with_edges(leg)
        assert result[0]['edge_ids'] == ['200-500', '200-800']

    def test_multiple_steps_produce_separate_edge_lists(self):
        leg = {
            'annotation': {'nodes': [10, 20, 30, 40, 50]},
            'steps': [
                {
                    'name': 'First Street',
                    'distance': 100,
                    'geometry': {'coordinates': [[0, 0], [1, 1], [2, 2]]},
                },
                {
                    'name': 'Second Street',
                    'distance': 100,
                    'geometry': {'coordinates': [[2, 2], [3, 3], [4, 4]]},
                },
            ],
        }
        result = extract_steps_with_edges(leg)
        assert len(result) == 2
        assert result[0]['name'] == 'First Street'
        assert result[0]['edge_ids'] == ['10-20', '20-30']
        assert result[1]['name'] == 'Second Street'
        assert result[1]['edge_ids'] == ['30-40', '40-50']

    def test_zero_distance_step_is_skipped(self):
        leg = {
            'annotation': {'nodes': [10, 20, 30]},
            'steps': [
                {
                    'name': 'Real Road',
                    'distance': 100,
                    'geometry': {'coordinates': [[0, 0], [1, 1]]},
                },
                {
                    'name': '',
                    'distance': 0,
                    'geometry': {'coordinates': [[1, 1], [2, 2]]},
                },
            ],
        }
        result = extract_steps_with_edges(leg)
        assert len(result) == 1
        assert result[0]['name'] == 'Real Road'

    def test_empty_nodes_returns_empty(self):
        leg = {
            'annotation': {'nodes': []},
            'steps': [
                {
                    'name': 'Road',
                    'distance': 100,
                    'geometry': {'coordinates': [[0, 0], [1, 1], [2, 2]]},
                }
            ],
        }
        result = extract_steps_with_edges(leg)
        assert result == []

    def test_single_node_returns_empty(self):
        leg = {
            'annotation': {'nodes': [100]},
            'steps': [
                {'name': 'Road', 'distance': 100, 'geometry': {'coordinates': [[0, 0]]}}
            ],
        }
        result = extract_steps_with_edges(leg)
        assert result == []
