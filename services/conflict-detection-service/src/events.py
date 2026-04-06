import json
import logging
import os
from datetime import UTC, datetime
from uuid import uuid4

import redis

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)


def publish_event(
    stream: str,
    data: dict,
    correlation_id: str | None = None,
) -> None:
    envelope = {
        'event_id': str(uuid4()),
        'correlation_id': correlation_id or str(uuid4()),
        'event_type': stream,
        'created_at': datetime.now(UTC).isoformat(),
        'data': data,
    }
    redis_client.xadd(stream, {'data': json.dumps(envelope)})
    logger.info(
        'Published to %s event_id=%s correlation=%s',
        stream,
        envelope['event_id'],
        envelope['correlation_id'],
    )
