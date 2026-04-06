import json
import logging
import os
import time
from datetime import UTC, datetime
from threading import Event
from uuid import uuid4

import redis
from database import SessionLocal
from events import publish_event
from models.processed_event import ProcessedEvent
from models.route import Route
from services.conflict import assess_and_reserve, delete_reservations
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)

CREATED_STREAM = 'booking.created'
UPDATED_STREAM = 'booking.updated'
GROUP = 'conflict-detection-service'
CONSUMER_INSTANCE = os.environ.get('HOSTNAME', str(uuid4()))
CREATED_CONSUMER = f'conflict-consumer-created-{CONSUMER_INSTANCE}'
UPDATED_CONSUMER = f'conflict-consumer-updated-{CONSUMER_INSTANCE}'
MAX_ATTEMPTS = 3


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


def parse_envelope(fields: dict, stream: str, msg_id: str) -> dict:
    raw = json.loads(fields['data'])
    if isinstance(raw, dict) and raw.get('event_id') and 'data' in raw:
        return raw

    return {
        'event_id': f'{stream}:{msg_id}',
        'correlation_id': str(uuid4()),
        'event_type': stream,
        'created_at': datetime.now(UTC).isoformat(),
        'data': raw,
    }


def publish_to_dlq(stream: str, msg_id: str, fields: dict, error: Exception) -> None:
    payload = {
        'stream': stream,
        'message_id': msg_id,
        'fields': fields,
        'error': str(error),
        'failed_at': datetime.now(UTC).isoformat(),
    }
    redis_client.xadd(f'{stream}.dlq', {'data': json.dumps(payload)})


def handle_booking_created(
    db,
    data: dict,
    event_id: str,
    consumer: str,
    stream: str,
) -> dict | None:
    booking_id = data['booking_id']
    route_id = data['route_id']
    departure_time = datetime.fromisoformat(
        data['departure_time'].replace('Z', '+00:00')
    )

    route = db.query(Route).filter(Route.route_id == route_id).first()
    if route is None:
        logger.warning('Route %s not found', route_id)
        event_payload = {
            'booking_id': booking_id,
            'route_id': route_id,
            'segments_available': False,
        }
        _mark_processed(db, event_id, consumer, stream)
        db.commit()
        return event_payload

    segment_ids = [str(sid) for sid in (route.segment_ids or [])]
    duration = route.estimated_duration or 3600

    if not segment_ids:
        event_payload = {
            'booking_id': booking_id,
            'route_id': route_id,
            'segments_available': True,
        }
        _mark_processed(db, event_id, consumer, stream)
        db.commit()
        return event_payload

    result = assess_and_reserve(
        booking_id=booking_id,
        route_id=route_id,
        segment_ids=segment_ids,
        departure_time=departure_time,
        duration_seconds=duration,
        db=db,
    )

    event_payload = {
        'booking_id': result.booking_id,
        'route_id': result.route_id,
        'segments_available': result.segments_available,
    }
    _mark_processed(db, event_id, consumer, stream)
    db.commit()
    return event_payload


def handle_booking_updated(
    db,
    data: dict,
    event_id: str,
    consumer: str,
    stream: str,
) -> None:
    booking_id = data['booking_id']
    status = data['status']

    if status in ('CANCELLED', 'EXPIRED'):
        count = delete_reservations(booking_id, db)
        logger.info(
            'Released %d reservations for %s booking %s',
            count,
            status,
            booking_id,
        )

    _mark_processed(db, event_id, consumer, stream)
    db.commit()


def _mark_processed(db, event_id: str, consumer: str, stream: str) -> None:
    db.add(
        ProcessedEvent(
            event_id=event_id,
            consumer_name=consumer,
            stream_name=stream,
        )
    )


def process_with_retry(handler, **kwargs):
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        db = SessionLocal()
        try:
            result = handler(db=db, **kwargs)
            return result
        except IntegrityError:
            db.rollback()
            return None
        except Exception as exc:
            db.rollback()
            last_err = exc
            time.sleep(0.2 * (attempt**2))
        finally:
            db.close()
    raise last_err


def run_consumer(stop_event: Event | None = None) -> None:
    ensure_consumer_group(CREATED_STREAM)
    logger.info('Conflict detection consumer started on %s', CREATED_STREAM)
    while not (stop_event and stop_event.is_set()):
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
                    envelope = parse_envelope(fields, CREATED_STREAM, msg_id)
                    correlation_id = envelope.get('correlation_id', str(uuid4()))

                    try:
                        event_payload = process_with_retry(
                            handle_booking_created,
                            data=envelope['data'],
                            event_id=envelope['event_id'],
                            consumer=CREATED_CONSUMER,
                            stream=CREATED_STREAM,
                        )
                    except Exception as exc:
                        publish_to_dlq(CREATED_STREAM, msg_id, fields, exc)
                        redis_client.xack(CREATED_STREAM, GROUP, msg_id)
                        continue

                    if event_payload is not None:
                        publish_event(
                            'route.assessed',
                            event_payload,
                            correlation_id=correlation_id,
                        )
                    redis_client.xack(CREATED_STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Consumer error')
            time.sleep(1)


def run_updated_consumer(stop_event: Event | None = None) -> None:
    ensure_consumer_group(UPDATED_STREAM)
    logger.info('Reservation cleanup consumer started on %s', UPDATED_STREAM)
    while not (stop_event and stop_event.is_set()):
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
                    envelope = parse_envelope(fields, UPDATED_STREAM, msg_id)

                    try:
                        process_with_retry(
                            handle_booking_updated,
                            data=envelope['data'],
                            event_id=envelope['event_id'],
                            consumer=UPDATED_CONSUMER,
                            stream=UPDATED_STREAM,
                        )
                    except Exception as exc:
                        publish_to_dlq(UPDATED_STREAM, msg_id, fields, exc)
                        redis_client.xack(UPDATED_STREAM, GROUP, msg_id)
                        continue

                    redis_client.xack(UPDATED_STREAM, GROUP, msg_id)
        except Exception:
            logger.exception('Updated consumer error')
            time.sleep(1)
