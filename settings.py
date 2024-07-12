import redis
import os
import logging
from dotenv import load_dotenv


load_dotenv()
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

redis_client = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARN
)
logger = logging.getLogger(__name__)
