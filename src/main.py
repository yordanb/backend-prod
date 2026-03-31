# Main FastAPI application
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from src.core.limiter import limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from src.core.redis import init_redis, close_redis
from src.api.main_router import api_router
from src.core.config import settings
from src.core import models  # ⬅️ penting (trigger registration sekali)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for FastAPI.
    - Initialize Redis
    - Close Redis on shutdown
    """
    # Startup
    try:
        await init_redis()
        print("✅ Redis connection established")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

    yield

    # Shutdown
    try:
        await close_redis()
        print("✅ Redis connection closed")
    except Exception as e:
        print(f"❌ Error closing Redis: {e}")

# Create FastAPI app
app = FastAPI(
    title="MTE Full Stack API",
    description="Production-ready IoT backend with FastAPI, MySQL, Redis",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Custom rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return await _rate_limit_exceeded_handler(request, exc)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MTE Full Stack API",
        "version": "v1",
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1"
    }

# Unversioned health check (for infrastructure)
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mte-full-stack"}

# Include versioned API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=3030,
        reload=False  # Set to False in production
    )
