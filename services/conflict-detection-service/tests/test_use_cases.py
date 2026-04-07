from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from application.use_cases import (AssessRouteUseCase,
                                   ReleaseReservationsUseCase)
from domain.assessment import AssessmentResult


class TestAssessRouteUseCase:
    @pytest.fixture
    def mock_route_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_segment_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_reservation_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_processed_event_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_outbox_repo(self):
        return MagicMock()

    @pytest.fixture
    def use_case(
        self,
        mock_route_repo,
        mock_segment_repo,
        mock_reservation_repo,
        mock_processed_event_repo,
        mock_outbox_repo,
    ):
        return AssessRouteUseCase(
            route_repo=mock_route_repo,
            segment_repo=mock_segment_repo,
            reservation_repo=mock_reservation_repo,
            processed_event_repo=mock_processed_event_repo,
            outbox_repo=mock_outbox_repo,
        )

    def test_execute_calls_all_dependencies(
        self,
        use_case,
        mock_route_repo,
        mock_segment_repo,
        mock_reservation_repo,
        mock_processed_event_repo,
        mock_outbox_repo,
    ):
        from domain.route import Route

        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            segment_ids=['seg-1'],
            estimated_duration=3600,
        )
        mock_segment_repo.get_capacities.return_value = {'seg-1': 5}
        mock_reservation_repo.count_overlapping.return_value = 0

        result = use_case.execute(
            booking_id='booking-123',
            route_id='route-123',
            departure_time=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
            event_id='event-456',
            consumer_name='consumer-1',
            stream_name='booking.created',
            correlation_id='corr-789',
        )

        assert result.booking_id == 'booking-123'
        mock_processed_event_repo.mark_processed.assert_called_once_with(
            'event-456', 'consumer-1', 'booking.created'
        )
        mock_outbox_repo.enqueue.assert_called_once_with(
            'route.assessed',
            {
                'booking_id': 'booking-123',
                'route_id': 'route-123',
                'segments_available': True,
            },
            'corr-789',
        )

    def test_execute_returns_assessment_result(
        self,
        use_case,
        mock_route_repo,
        mock_segment_repo,
        mock_reservation_repo,
    ):
        from domain.route import Route

        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            segment_ids=['seg-1'],
            estimated_duration=3600,
        )
        mock_segment_repo.get_capacities.return_value = {'seg-1': 5}
        mock_reservation_repo.count_overlapping.return_value = 0

        result = use_case.execute(
            booking_id='booking-123',
            route_id='route-123',
            departure_time=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
            event_id='event-456',
            consumer_name='consumer-1',
            stream_name='booking.created',
            correlation_id='corr-789',
        )

        assert isinstance(result, AssessmentResult)
        assert result.segments_available is True


class TestReleaseReservationsUseCase:
    @pytest.fixture
    def mock_reservation_repo(self):
        return MagicMock()

    @pytest.fixture
    def mock_processed_event_repo(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_reservation_repo, mock_processed_event_repo):
        return ReleaseReservationsUseCase(
            reservation_repo=mock_reservation_repo,
            processed_event_repo=mock_processed_event_repo,
        )

    def test_execute_releases_and_marks_processed(
        self, use_case, mock_reservation_repo, mock_processed_event_repo
    ):
        mock_reservation_repo.delete_by_booking.return_value = 5

        count = use_case.execute(
            booking_id='booking-123',
            event_id='event-456',
            consumer_name='consumer-1',
            stream_name='booking.updated',
        )

        assert count == 5
        mock_reservation_repo.delete_by_booking.assert_called_once_with('booking-123')
        mock_processed_event_repo.mark_processed.assert_called_once_with(
            'event-456', 'consumer-1', 'booking.updated'
        )

    def test_execute_returns_zero_when_no_reservations(
        self, use_case, mock_reservation_repo, mock_processed_event_repo
    ):
        mock_reservation_repo.delete_by_booking.return_value = 0

        count = use_case.execute(
            booking_id='booking-123',
            event_id='event-456',
            consumer_name='consumer-1',
            stream_name='booking.updated',
        )

        assert count == 0
