from datetime import UTC, datetime

import pytest
from domain.assessment import AssessmentResult
from domain.reservation import Reservation
from domain.route import Route


class TestAssessmentResult:
    def test_create_assessment_result(self):
        result = AssessmentResult(
            booking_id='booking-123',
            route_id='route-456',
            segments_available=True,
        )
        assert result.booking_id == 'booking-123'
        assert result.route_id == 'route-456'
        assert result.segments_available is True

    def test_assessment_result_is_immutable(self):
        result = AssessmentResult(
            booking_id='booking-123',
            route_id='route-456',
            segments_available=True,
        )
        with pytest.raises(AttributeError):
            result.segments_available = False


class TestRoute:
    def test_create_route(self):
        route = Route(
            route_id='route-123',
            segment_ids=['seg-1', 'seg-2', 'seg-3'],
            estimated_duration=3600,
        )
        assert route.route_id == 'route-123'
        assert route.segment_ids == ['seg-1', 'seg-2', 'seg-3']
        assert route.estimated_duration == 3600

    def test_route_with_empty_segments(self):
        route = Route(
            route_id='route-123',
            segment_ids=[],
            estimated_duration=0,
        )
        assert route.segment_ids == []
        assert route.estimated_duration == 0


class TestReservation:
    def test_create_reservation(self):
        from uuid import uuid4

        reservation_id = uuid4()
        segment_id = uuid4()
        start = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
        end = datetime(2024, 1, 1, 11, 0, tzinfo=UTC)

        reservation = Reservation(
            reservation_id=reservation_id,
            segment_id=segment_id,
            time_window_start=start,
            time_window_end=end,
        )
        assert reservation.reservation_id == reservation_id
        assert reservation.segment_id == segment_id
        assert reservation.time_window_start == start
        assert reservation.time_window_end == end
