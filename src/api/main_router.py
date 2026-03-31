# Main API router aggregator
from fastapi import APIRouter
from src.modules.auth.router import router as auth_router
from src.modules.user.router import router as user_router
from src.modules.role.router import router as role_router

api_router = APIRouter()

# Include all module routers
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(role_router)

# Health check endpoint
@api_router.get("/health")
async def health():
    return {"status": "healthy", "service": "mte-full-stack"}
