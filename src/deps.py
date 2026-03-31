# FastAPI dependencies: authentication, RBAC
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.security import decode_token
from src.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Extract and validate JWT token from Authorization header.
    Returns decoded payload with user info.
    """
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Optionally, fetch user from DB here to verify existence
        # For now, return payload
        return {"user_id": int(user_id), "role": role, **payload}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

def require_roles(allowed_roles: list[str]):
    """
    Dependency factory that checks if user has one of the allowed roles.
    Usage: Depends(require_roles(["admin", "user"]))
    """
    def role_checker(user: Dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker
