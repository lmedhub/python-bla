import redis
from django.conf import settings
from django.db import DatabaseError, connection


def database_is_up() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return False
    return True


def redis_is_up() -> bool:
    client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
    try:
        return bool(client.ping())
    except redis.RedisError:
        return False
    finally:
        client.close()
