import aioredis
import os


async def get_redis():
    redis_address = os.getenv('REDIS_ADDRESS')
    redis = await aioredis.from_url(redis_address, db=0)
    return redis
