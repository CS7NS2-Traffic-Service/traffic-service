import json
import logging
import os
import time
from uuid import UUID

import redis
from database import SessionLocal
from domain import BookingStatus, parse_status, transition
from events import publish_event
from models.booking import Booking

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)

STREAM = 'route.assessed'
GROUP = 'booking-service'
CONSUMER = 'booking-consumer-1'


def ensure_consumer_group() -> None:
    try:
        redis_client.xgroup_create(STREAM, GROUP, id='0', mkstream=True)
    except redis.exceptions.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise


def handle_route_assessed(data: dict) -> None:
    booking_id = data.get('booking_id')
    segments_available = data.get('segments_available')
    if booking_id is None or segments_available is None:
        logger.warning('Invalid route.assessed payload: %s', data)
        return
    try:
        booking_uuid = UUID(str(booking_id))
    except ValueError:
        logger.warning('Invalid booking_id in route.assessed: %s', booking_id)
        return

    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.booking_id == booking_uuid).first()
        if booking is None:
            logger.warning('Booking %s not found', booking_id)
            return
        current = parse_status(booking.status)
        if current != BookingStatus.PENDING:
            logger.info('Booking %s already %s', booking_id, current)
            return

        target = (
            BookingStatus.APPROVED
            if bool(segments_available)
            else BookingStatus.REJECTED
        )
        booking.status = transition(current, target).value
        db.commit()
        db.refresh(booking)

        publish_event(
            'booking.updated',
            {
                'booking_id': str(booking.booking_id),
                'driver_id': str(booking.driver_id),
                'status': booking.status,
            },
        )
    finally:
        db.close()


def run_consumer() -> None:
    ensure_consumer_group()
    logger.info('Booking consumer started on %s', STREAM)
    while True:
        try:
            messages = redis_client.xreadgroup(
                GROUP,
                CONSUMER,
                {STREAM: '>'},
                count=10,
                block=5000,
            )
            for _, entries in messages:
                for msg_id, fields in entries:
                    data = json.loads(fields['data'])
                    handle_route_assessed(data)
                    redis_client.xack(STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Consumer error')
            time.sleep(1)
