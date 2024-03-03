import aioredis


async def redis_init():
    await aioredis.Redis(host='127.0.0.1', port=6379, db=0)
