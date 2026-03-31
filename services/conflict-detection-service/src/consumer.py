import json
import logging
import os
import time
from datetime import datetime

import redis
from database import SessionLocal
from events import publish_event
from models.route import Route
from services.conflict import assess_and_reserve, delete_reservations

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)

CREATED_STREAM = 'booking.created'
UPDATED_STREAM = 'booking.updated'
GROUP = 'conflict-detection-service'
CREATED_CONSUMER = 'conflict-consumer-1'
UPDATED_CONSUMER = 'conflict-consumer-2'


def ensure_consumer_group(stream: str) -> None:
    try:
        redis_client.xgroup_create(
            stream,
            GROUP,
            id='0',
            mkstream=True,
        )
    except redis.exceptions.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise


def handle_booking_created(data: dict) -> None:
    booking_id = data['booking_id']
    route_id = data['route_id']
    departure_time = datetime.fromisoformat(data['departure_time'])

    db = SessionLocal()
    try:
        route = db.query(Route).filter(Route.route_id == route_id).first()
        if route is None:
            logger.warning('Route %s not found', route_id)
            publish_event(
                'route.assessed',
                {
                    'booking_id': booking_id,
                    'route_id': route_id,
                    'segments_available': False,
                },
            )
            return

        segment_ids = [str(sid) for sid in (route.segment_ids or [])]
        duration = route.estimated_duration or 3600

        if not segment_ids:
            publish_event(
                'route.assessed',
                {
                    'booking_id': booking_id,
                    'route_id': route_id,
                    'segments_available': True,
                },
            )
            return

        result = assess_and_reserve(
            booking_id=booking_id,
            route_id=route_id,
            segment_ids=segment_ids,
            departure_time=departure_time,
            duration_seconds=duration,
            db=db,
        )

        publish_event(
            'route.assessed',
            {
                'booking_id': result.booking_id,
                'route_id': result.route_id,
                'segments_available': result.segments_available,
            },
        )
    finally:
        db.close()


def handle_booking_updated(data: dict) -> None:
    booking_id = data['booking_id']
    status = data['status']

    if status not in ('CANCELLED', 'EXPIRED'):
        return

    db = SessionLocal()
    try:
        count = delete_reservations(booking_id, db)
        logger.info(
            'Released %d reservations for %s booking %s',
            count,
            status,
            booking_id,
        )
    finally:
        db.close()


def run_consumer() -> None:
    ensure_consumer_group(CREATED_STREAM)
    logger.info('Conflict detection consumer started on %s', CREATED_STREAM)
    while True:
        try:
            messages = redis_client.xreadgroup(
                GROUP,
                CREATED_CONSUMER,
                {CREATED_STREAM: '>'},
                count=10,
                block=5000,
            )
            for _, entries in messages:
                for msg_id, fields in entries:
                    data = json.loads(fields['data'])
                    handle_booking_created(data)
                    redis_client.xack(CREATED_STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Consumer error')
            time.sleep(1)


def run_updated_consumer() -> None:
    ensure_consumer_group(UPDATED_STREAM)
    logger.info('Reservation cleanup consumer started on %s', UPDATED_STREAM)
    while True:
        try:
            messages = redis_client.xreadgroup(
                GROUP,
                UPDATED_CONSUMER,
                {UPDATED_STREAM: '>'},
                count=10,
                block=5000,
            )
            for _, entries in messages:
                for msg_id, fields in entries:
                    data = json.loads(fields['data'])
                    handle_booking_updated(data)
                    redis_client.xack(UPDATED_STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Updated consumer error')
            time.sleep(1)
