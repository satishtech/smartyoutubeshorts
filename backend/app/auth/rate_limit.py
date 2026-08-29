"""In-memory rate limiting for sensitive endpoints (no Redis in this MVP)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
