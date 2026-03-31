# User router: CRUD operations
import json
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .repository import UserRepository
from src.modules.audit.repository import AuditLogRepository
from .schemas import UserCreate, UserUpdate, UserResponse, RoleResponse
from src.core.database import get_db
from src.deps import require_roles
from src.modules.role.repository import RoleRepository
from src.core.limiter import limiter

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    Create a new user (admin only).
    Rate limited to prevent spam user creation.
    """
    existing = await UserRepository.get_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Verify role exists
    role = await RoleRepository.get_by_id(db, user_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    new_user = await UserRepository.create(db, user_data)

    # Audit log
    await AuditLogRepository.create(
        db=db,
        user_id=user["user_id"],
        action="user.create",
        resource_type="user",
        resource_id=str(new_user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=json.dumps({"email": user_data.email, "role": role.name})
    )

    return new_user

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    List all users (admin only).
    """
    users = await UserRepository.list(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["admin", "user"]))
):
    """
    Get user by ID.
    Users can only access their own data unless admin.
    """
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users"
        )

    user = await UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    Update user (admin only).
    """
    existing = await UserRepository.get_by_id(db, user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    updated = await UserRepository.update(db, user_id, update_data)

    await AuditLogRepository.create(
        db=db,
        user_id=user["user_id"],
        action="user.update",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=request.client.host if request.client else None,
        details=json.dumps(update_data.dict(exclude_unset=True))
    )

    return updated

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    Delete user (admin only).
    Operation: soft delete by setting is_active=False.
    """
    existing = await UserRepository.get_by_id(db, user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await UserRepository.update(db, user_id, UserUpdate(is_active=False))

    await AuditLogRepository.create(
        db=db,
        user_id=user["user_id"],
        action="user.delete",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=request.client.host if request.client else None
    )

    return {"message": "User deactivated"}
