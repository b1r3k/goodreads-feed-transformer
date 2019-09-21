import logging
import time

from ..const import REDIS_PREFIX, MAX_LOCATION_STORAGE

logger = logging.getLogger(__name__)


async def store_event_marker(redis_pool, event_id, occured_at=None):
    timestamp = occured_at or int(time.time())
    logger.info('Storing event marker..')
    key = '{}{}'.format(REDIS_PREFIX, event_id)
    res = await redis_pool.setnx(key, timestamp)
    if res:
        await redis_pool.setex(key, MAX_LOCATION_STORAGE, timestamp)


async def remove_event_marker(redis_pool, event_id):
    key = '{}{}'.format(REDIS_PREFIX, event_id)
    with await redis_pool as redis:
        await redis.delete(key)


async def get_event_marker(redis_pool, event_id):
    key = '{}{}'.format(REDIS_PREFIX, event_id)
    with await redis_pool as redis:
        timestamp = await redis.get(key)
        return timestamp
