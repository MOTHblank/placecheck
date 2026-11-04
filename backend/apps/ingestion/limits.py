from django.core.cache import cache

from .exceptions import SourceRateLimitExceeded


def check_source_rate_limit(source):
    key = f"placecheck:source-rate:{source.pk}"
    try:
        if cache.add(key, 1, timeout=60):
            current = 1
        else:
            current = cache.incr(key)
    except ValueError:
        current = 1
        cache.set(key, current, timeout=60)
    if current > source.rate_limit_per_minute:
        raise SourceRateLimitExceeded(f"Rate limit atingido para source={source.pk}")
