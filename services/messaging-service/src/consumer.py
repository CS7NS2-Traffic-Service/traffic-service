import json
import logging
import os
import time

import redis
from database import SessionLocal
from services.message import create_message

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)

STREAM = 'booking.updated'
GROUP = 'messaging-service'
CONSUMER = 'messaging-consumer-1'

STATUS_MESSAGES = {
    'APPROVED': ('Your booking has been approved. Have a safe journey!'),
    'REJECTED': (
        'Your booking has been rejected due to road capacity'
        ' constraints. Please try a different departure time'
        ' or route.'
    ),
    'CANCELLED': 'Your booking has been cancelled.',
    'EXPIRED': ('Your booking has expired as the departure time has passed.'),
}


def ensure_consumer_group() -> None:
    try:
        redis_client.xgroup_create(STREAM, GROUP, id='0', mkstream=True)
    except redis.exceptions.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise


def handle_booking_updated(data: dict) -> None:
    driver_id = data['driver_id']
    booking_id = data['booking_id']
    status = data['status']

    content = STATUS_MESSAGES.get(
        status,
        f'Your booking status has been updated to {status}.',
    )

    db = SessionLocal()
    try:
        create_message(
            driver_id=driver_id,
            booking_id=booking_id,
            content=content,
            db=db,
        )
        logger.info(
            'Created message for driver %s: %s',
            driver_id,
            status,
        )
    finally:
        db.close()


def run_consumer() -> None:
    ensure_consumer_group()
    logger.info('Messaging consumer started on %s', STREAM)
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
                    handle_booking_updated(data)
                    redis_client.xack(STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Consumer error')
            time.sleep(1)
