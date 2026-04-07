from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from application.conflict_service import SEGMENT_OFFSET_SECONDS, ConflictService
from domain.reservation import Reservation
from domain.route import Route


class TestConflictService:
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
    def service(self, mock_route_repo, mock_segment_repo, mock_reservation_repo):
        return ConflictService(
            route_repo=mock_route_repo,
            segment_repo=mock_segment_repo,
            reservation_repo=mock_reservation_repo,
        )

    def test_assess_and_reserve_route_not_found(self, service, mock_route_repo):
        mock_route_repo.get_by_id.return_value = None

        result = service.assess_and_reserve(
            booking_id='booking-123',
            route_id='nonexistent-route',
            departure_time=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        assert result.booking_id == 'booking-123'
        assert result.route_id == 'nonexistent-route'
        assert result.segments_available is False

    def test_assess_and_reserve_empty_segments(self, service, mock_route_repo):
        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            segment_ids=[],
            estimated_duration=3600,
        )

        result = service.assess_and_reserve(
            booking_id='booking-123',
            route_id='route-123',
            departure_time=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        assert result.segments_available is True

    def test_assess_and_reserve_all_segments_available(
        self, service, mock_route_repo, mock_segment_repo, mock_reservation_repo
    ):
        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            segment_ids=['seg-1', 'seg-2'],
            estimated_duration=3600,
        )
        mock_segment_repo.get_capacities.return_value = {
            'seg-1': 5,
            'seg-2': 5,
        }
        mock_reservation_repo.count_overlapping.return_value = 0

        result = service.assess_and_reserve(
            booking_id='booking-123',
            route_id='route-123',
            departure_time=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        assert result.segments_available is True
        assert mock_reservation_repo.create.call_count == 2

    def test_assess_and_reserve_segment_at_capacity(
        self, service, mock_route_repo, mock_segment_repo, mock_reservation_repo
    ):
        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            segment_ids=['seg-1', 'seg-2'],
            estimated_duration=3600,
        )
        mock_segment_repo.get_capacities.return_value = {
            'seg-1': 5,
            'seg-2': 5,
        }
        mock_reservation_repo.count_overlapping.side_effect = [5, 0]

        result = service.assess_and_reserve(
            booking_id='booking-123',
            route_id='route-123',
            departure_time=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        assert result.segments_available is False
        mock_reservation_repo.create.assert_not_called()

    def test_assess_and_reserve_partial_capacity(
        self, service, mock_route_repo, mock_segment_repo, mock_reservation_repo
    ):
        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            segment_ids=['seg-1', 'seg-2'],
            estimated_duration=3600,
        )
        mock_segment_repo.get_capacities.return_value = {
            'seg-1': 5,
            'seg-2': 5,
        }
        mock_reservation_repo.count_overlapping.side_effect = [4, 5]

        result = service.assess_and_reserve(
            booking_id='booking-123',
            route_id='route-123',
            departure_time=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
        )

        assert result.segments_available is False

    def test_assess_and_reserve_creates_reservations_with_correct_timing(
        self, service, mock_route_repo, mock_segment_repo, mock_reservation_repo
    ):
        departure_time = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)

        mock_route_repo.get_by_id.return_value = Route(
            route_id='route-123',
            segment_ids=['seg-1', 'seg-2'],
            estimated_duration=3600,
        )
        mock_segment_repo.get_capacities.return_value = {
            'seg-1': 5,
            'seg-2': 5,
        }
        mock_reservation_repo.count_overlapping.return_value = 0

        service.assess_and_reserve(
            booking_id='booking-123',
            route_id='route-123',
            departure_time=departure_time,
        )

        assert mock_reservation_repo.create.call_count == 2

        first_call = mock_reservation_repo.create.call_args_list[0]
        assert first_call[0][0] == 'booking-123'
        assert first_call[0][1] == 'seg-1'
        expected_start_1 = departure_time + timedelta(
            seconds=SEGMENT_OFFSET_SECONDS * 0
        )
        expected_end_1 = expected_start_1 + timedelta(seconds=3600)
        assert first_call[0][2] == expected_start_1
        assert first_call[0][3] == expected_end_1

        second_call = mock_reservation_repo.create.call_args_list[1]
        assert second_call[0][1] == 'seg-2'
        expected_start_2 = departure_time + timedelta(
            seconds=SEGMENT_OFFSET_SECONDS * 1
        )
        expected_end_2 = expected_start_2 + timedelta(seconds=3600)
        assert second_call[0][2] == expected_start_2
        assert second_call[0][3] == expected_end_2

    def test_release_reservations(self, service, mock_reservation_repo):
        mock_reservation_repo.delete_by_booking.return_value = 3

        count = service.release_reservations('booking-123')

        assert count == 3
        mock_reservation_repo.delete_by_booking.assert_called_once_with('booking-123')

    def test_get_segment_utilization(self, service, mock_reservation_repo):
        mock_reservation_repo.get_utilization.return_value = {
            'seg-1': 3,
            'seg-2': 1,
        }

        result = service.get_segment_utilization(
            segment_ids=['seg-1', 'seg-2'],
            window_start=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
            window_end=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        )

        assert result == {'seg-1': 3, 'seg-2': 1}

    def test_get_reservations_by_booking(self, service, mock_reservation_repo):
        reservation_id = uuid4()
        segment_id = uuid4()
        mock_reservation_repo.get_by_booking.return_value = [
            Reservation(
                reservation_id=reservation_id,
                segment_id=segment_id,
                time_window_start=datetime(2024, 1, 1, 10, 0, tzinfo=UTC),
                time_window_end=datetime(2024, 1, 1, 11, 0, tzinfo=UTC),
            )
        ]

        result = service.get_reservations_by_booking('booking-123')

        assert len(result) == 1
        assert result[0].reservation_id == reservation_id
