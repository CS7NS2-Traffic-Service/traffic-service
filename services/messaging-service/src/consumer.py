import json
import logging
import os
import time
from datetime import UTC, datetime
from threading import Event
from uuid import uuid4

import redis
from database import SessionLocal
from models.processed_event import ProcessedEvent
from services.message import create_message
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)

STREAM = 'booking.updated'
GROUP = 'messaging-service'
CONSUMER = f"messaging-consumer-{os.environ.get('HOSTNAME', str(uuid4()))}"
MAX_ATTEMPTS = 3

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


def mark_processed(event_id: str) -> bool:
    db = SessionLocal()
    try:
        db.add(
            ProcessedEvent(
                event_id=event_id,
                consumer_name=CONSUMER,
                stream_name=STREAM,
            )
        )
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
    finally:
        db.close()


def is_processed(event_id: str) -> bool:
    db = SessionLocal()
    try:
        found = (
            db.query(ProcessedEvent)
            .filter(
                ProcessedEvent.event_id == event_id,
                ProcessedEvent.consumer_name == CONSUMER,
            )
            .first()
        )
        return found is not None
    finally:
        db.close()


def parse_envelope(fields: dict, msg_id: str) -> dict:
    raw = json.loads(fields['data'])
    if isinstance(raw, dict) and raw.get('event_id') and 'data' in raw:
        return raw
    return {
        'event_id': f'{STREAM}:{msg_id}',
        'correlation_id': str(uuid4()),
        'event_type': STREAM,
        'created_at': datetime.now(UTC).isoformat(),
        'data': raw,
    }


def publish_to_dlq(msg_id: str, fields: dict, error: Exception) -> None:
    payload = {
        'stream': STREAM,
        'message_id': msg_id,
        'fields': fields,
        'error': str(error),
        'failed_at': datetime.now(UTC).isoformat(),
    }
    redis_client.xadd(f'{STREAM}.dlq', {'data': json.dumps(payload)})


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


def run_consumer(stop_event: Event | None = None) -> None:
    ensure_consumer_group()
    logger.info('Messaging consumer started on %s', STREAM)
    while not (stop_event and stop_event.is_set()):
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
                    envelope = parse_envelope(fields, msg_id)
                    if is_processed(envelope['event_id']):
                        redis_client.xack(STREAM, GROUP, msg_id)
                        continue

                    last_error = None
                    for attempt in range(1, MAX_ATTEMPTS + 1):
                        try:
                            handle_booking_updated(envelope['data'])
                            last_error = None
                            break
                        except Exception as exc:
                            last_error = exc
                            time.sleep(0.2 * (attempt**2))

                    if last_error is not None:
                        publish_to_dlq(msg_id, fields, last_error)
                        redis_client.xack(STREAM, GROUP, msg_id)
                        continue

                    if not mark_processed(envelope['event_id']):
                        logger.info(
                            'Event %s already marked processed for %s',
                            envelope['event_id'],
                            CONSUMER,
                        )
                    redis_client.xack(STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Consumer error')
            time.sleep(1)
