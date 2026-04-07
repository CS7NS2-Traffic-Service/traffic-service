import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from threading import Event

import redis
from database import SessionLocal
from models.outbox_event import OutboxEvent

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)

POLL_INTERVAL = 0.5
BATCH_SIZE = 50
CLEANUP_DAYS = 7


def run_relay(stop_event: Event | None = None) -> None:
    logger.info('Outbox relay started')
    while not (stop_event and stop_event.is_set()):
        try:
            _publish_batch()
        except Exception:
            logger.exception('Outbox relay error')
        time.sleep(POLL_INTERVAL)


def _publish_batch() -> None:
    db = SessionLocal()
    try:
        events = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.published == False)  # noqa: E712
            .order_by(OutboxEvent.id)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
            .all()
        )
        if not events:
            return
        for event in events:
            redis_client.xadd(event.stream, {'data': json.dumps(event.payload)})
            event.published = True
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_cleanup(stop_event: Event | None = None) -> None:
    logger.info('Outbox cleanup started')
    while not (stop_event and stop_event.is_set()):
        try:
            _cleanup_published()
        except Exception:
            logger.exception('Outbox cleanup error')
        time.sleep(3600)


def _cleanup_published() -> None:
    db = SessionLocal()
    try:
        cutoff = datetime.now(UTC) - timedelta(days=CLEANUP_DAYS)
        db.query(OutboxEvent).filter(
            OutboxEvent.published == True,  # noqa: E712
            OutboxEvent.created_at < cutoff,
        ).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
