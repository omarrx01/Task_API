
import os

import redis
from dotenv import load_dotenv

from logging_config import setup_logger

load_dotenv()

logger = setup_logger()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


def check_redis_connection():
    try:
        redis_client.ping()
        logger.info("Successfully connected to Redis")
        return True
    except redis.RedisError as error:
        logger.error("Redis connection failed: %s", error)
        return False
