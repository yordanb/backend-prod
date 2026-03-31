# Rate limiting configuration
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException

limiter = Limiter(key_func=get_remote_address)

def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded: {exc.detail}"
    )
