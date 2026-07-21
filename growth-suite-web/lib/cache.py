"""
Tiny in-process TTL cache decorator — replaces Streamlit's st.cache_data
in the FastAPI port of lib/data.py.

Streamlit's st.cache_data(ttl=N) caches a function's return value per
distinct argument set for N seconds, and exposes a `.clear()` method to
invalidate everything on that function. This is a minimal stand-in with
the same two behaviors, since FastAPI has no framework-level equivalent
and a real caching layer (Redis, etc.) would be overkill for a handful
of short-TTL reads.

Not thread-safe against concurrent writers to the same key, but the
values it wraps (kill-switch flag, brand list, experiment list) are all
cheap idempotent reads, so a rare duplicate fetch on a race is harmless.
"""
import functools
import time


def ttl_cache(ttl=15):
    def decorator(fn):
        store = {}

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = store.get(key)
            if cached is not None:
                value, ts = cached
                if now - ts < ttl:
                    return value
            value = fn(*args, **kwargs)
            store[key] = (value, now)
            return value

        wrapper.clear = store.clear
        return wrapper

    return decorator
