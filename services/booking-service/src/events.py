import json
import logging
import os

import redis

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://redis:6379'),
    decode_responses=True,
)


def publish_event(stream: str, data: dict) -> None:
    redis_client.xadd(stream, {'data': json.dumps(data)})
    logger.info('Published to %s: %s', stream, data)
