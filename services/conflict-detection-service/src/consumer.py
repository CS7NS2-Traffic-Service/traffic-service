import json
import logging
import os
import time
from datetime import datetime

import redis
from database import SessionLocal
from events import publish_event
from models.route import Route
from services.conflict import assess_and_reserve

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)

STREAM = 'booking.created'
GROUP = 'conflict-detection-service'
CONSUMER = 'conflict-consumer-1'


def ensure_consumer_group() -> None:
    try:
        redis_client.xgroup_create(
            STREAM,
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


def run_consumer() -> None:
    ensure_consumer_group()
    logger.info(
        'Conflict detection consumer started on %s',
        STREAM,
    )
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
                    handle_booking_created(data)
                    redis_client.xack(STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Consumer error')
            time.sleep(1)
