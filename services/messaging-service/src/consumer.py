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
CONSUMER = f'messaging-consumer-{os.environ.get("HOSTNAME", str(uuid4()))}'
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


def handle_booking_updated(
    db,
    data: dict,
    event_id: str,
) -> None:
    driver_id = data['driver_id']
    booking_id = data['booking_id']
    status = data['status']

    content = STATUS_MESSAGES.get(
        status,
        f'Your booking status has been updated to {status}.',
    )

    create_message(
        driver_id=driver_id,
        booking_id=booking_id,
        content=content,
        db=db,
    )
    db.add(
        ProcessedEvent(
            event_id=event_id,
            consumer_name=CONSUMER,
            stream_name=STREAM,
        )
    )
    db.commit()
    logger.info(
        'Created message for driver %s: %s',
        driver_id,
        status,
    )


def process_with_retry(handler, **kwargs):
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        db = SessionLocal()
        try:
            handler(db=db, **kwargs)
            return
        except IntegrityError:
            db.rollback()
            return
        except Exception as exc:
            db.rollback()
            last_err = exc
            time.sleep(0.2 * (attempt**2))
        finally:
            db.close()
    raise last_err


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
                    correlation_id = envelope.get('correlation_id', str(uuid4()))
                    logger.info(
                        'consuming message %s correlation_id=%s', msg_id, correlation_id
                    )

                    try:
                        process_with_retry(
                            handle_booking_updated,
                            data=envelope['data'],
                            event_id=envelope['event_id'],
                        )
                    except Exception as exc:
                        publish_to_dlq(msg_id, fields, exc)
                        redis_client.xack(STREAM, GROUP, msg_id)
                        continue

                    redis_client.xack(STREAM, GROUP, msg_id)
        except redis.exceptions.ResponseError as e:
            if 'NOGROUP' in str(e):
                logger.warning('Consumer group lost, recreating')
                ensure_consumer_group()
            else:
                logger.exception('Consumer error')
            time.sleep(1)
        except Exception:
            logger.exception('Consumer error')
            time.sleep(1)
