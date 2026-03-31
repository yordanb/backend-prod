# Role router: manage roles (admin only)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .repository import RoleRepository
from .schemas import RoleCreate, RoleUpdate, RoleResponse
from src.core.database import get_db
from src.deps import require_roles

router = APIRouter(prefix="/roles", tags=["roles"])

@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    Create a new role (admin only).
    """
    existing = await RoleRepository.get_by_name(db, role_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists"
        )

    role = await RoleRepository.create(db, role_data)
    return role

@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    List all roles (admin only).
    """
    roles = await RoleRepository.list(db)
    return roles

@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    update_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    Update a role (admin only).
    """
    role = await RoleRepository.get_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    updated = await RoleRepository.update(db, role_id, update_data)
    return updated
