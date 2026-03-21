import json
import logging
import os
import time

import redis
from database import SessionLocal
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
    booking_id = data['booking_id']
    segments_available = data['segments_available']

    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
        if booking is None:
            logger.warning('Booking %s not found', booking_id)
            return
        if booking.status != 'PENDING':
            logger.info('Booking %s already %s', booking_id, booking.status)
            return

        booking.status = 'APPROVED' if segments_available else 'REJECTED'
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
