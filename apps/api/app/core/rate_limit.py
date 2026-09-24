"""
Simple fixed-window rate limiter. Uses Redis if configured; otherwise falls
back to an in-process dict so the app still runs (with weaker guarantees)
when Redis is unavailable in local development.
"""

import time
from collections import defaultdict

from app.core.config import get_settings

settings = get_settings()

_local_counters: dict[str, list[float]] = defaultdict(list)
_redis_client = None

if settings.REDIS_URL:
    try:
        import redis

        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        _redis_client = None


def reset_rate_limits() -> None:
    """Test-only helper to clear in-process rate limit state between test cases."""
    _local_counters.clear()


def is_rate_limited(key: str, max_requests: int, window_seconds: int = 60) -> bool:
    now = time.time()

    if _redis_client:
        try:
            pipe = _redis_client.pipeline()
            redis_key = f"ratelimit:{key}"
            pipe.incr(redis_key, 1)
            pipe.expire(redis_key, window_seconds)
            count, _ = pipe.execute()
            return int(count) > max_requests
        except Exception:
            pass  # fall through to local fallback if Redis call fails

    window_start = now - window_seconds
    _local_counters[key] = [t for t in _local_counters[key] if t > window_start]
    _local_counters[key].append(now)
    return len(_local_counters[key]) > max_requests
