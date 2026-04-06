from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from src.core.limiter import limiter
from src.core.database import get_db
from src.modules.user.model import User
from src.modules.auth.model import DevicePairing
from src.modules.audit.repository import AuditLogRepository
from src.modules.role.repository import RoleRepository
from src.deps import require_roles
from src.modules.user.repository import UserRepository
from src.modules.auth.repository import RefreshTokenRepository
from src.modules.user.schemas import UserResponse
from src.core.security import hash_password
import secrets
import json
from typing import Optional, List

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles(["admin"]))])

# User Management
@router.get("/users")
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    """List users with pagination and optional search by nrp/email."""
    offset = (page - 1) * limit
    
    # Build base query with eager load of role
    base_query = select(User).options(selectinload(User.role))
    count_query = select(User)
    
    conditions = []
    if search:
        search_filter = or_(
            User.nrp.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        conditions.append(search_filter)
    
    if conditions:
        base_query = base_query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Count total
    total_res = await db.execute(count_query)
    total = len(total_res.scalars().all())
    
    # Pagination
    result = await db.execute(base_query.offset(offset).limit(limit))
    users = result.scalars().all()
    
    return {
        "data": [UserResponse.from_orm(u).dict() for u in users],
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) // limit,
    }

@router.post("/users")
async def create_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    nrp: str = Query(...),
    nama: str = Query(...),
    email: str = Query(...),
    password: str = Query(...),
    role_id: int = Query(2)
):
    """Create new user (admin only)."""
    # Check nrp/email uniqueness
    existing = await UserRepository.get_by_nrp(db, nrp)
    if existing:
        raise HTTPException(status_code=400, detail="NRP already exists")
    existing_email = await UserRepository.get_by_email(db, email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash password
    from src.core.security import hash_password
    password_hash = hash_password(password)
    
    # Create user
    user = User(
        nrp=nrp,
        nama=nama,
        email=email,
        password=password_hash,
        role_id=role_id,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Audit log
    await AuditLogRepository.create(
        db=db,
        user_id=user.id,
        action="user.created",
        ip_address=request.client.host if request.client else None,
        details=json.dumps({"nrp": nrp, "email": email, "role_id": role_id})
    )
    
    return UserResponse.from_orm(user)

@router.get("/users/{id}")
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID."""
    user = await UserRepository.get_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)

@router.put("/users/{id}")
async def update_user(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    nrp: Optional[str] = Query(None),
    nama: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    role_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Update user (admin only). Cannot change password here."""
    user = await UserRepository.get_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if nrp and nrp != user.nrp:
        existing = await UserRepository.get_by_nrp(db, nrp)
        if existing and existing.id != id:
            raise HTTPException(status_code=400, detail="NRP already used")
        user.nrp = nrp
    
    if nama:
        user.nama = nama
    if email and email != user.email:
        existing_email = await UserRepository.get_by_email(db, email)
        if existing_email and existing_email.id != id:
            raise HTTPException(status_code=400, detail="Email already used")
        user.email = email
    if role_id:
        # Validate role exists
        role = await RoleRepository.get_by_id(db, role_id)
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role_id = role_id
    if is_active is not None:
        user.is_active = is_active
    
    await db.commit()
    await db.refresh(user)
    
    await AuditLogRepository.create(
        db=db,
        user_id=id,
        action="user.updated",
        ip_address=request.client.host if request.client else None,
        details=json.dumps({"fields_updated": [k for k,v in locals().items() if v is not None and k not in ['request','db','id','user']]})
    )
    
    return UserResponse.from_orm(user)

@router.post("/users/{id}/reset-password")
async def reset_password(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Reset user password to a random one (admin only)."""
    user = await UserRepository.get_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate random password (12 chars)
    new_password = secrets.token_urlsafe(9)
    user.password = hash_password(new_password)
    await db.commit()
    
    # Revoke all refresh tokens for user
    await RefreshTokenRepository.revoke_all_user_tokens(db, user.id)
    
    await AuditLogRepository.create(
        db=db,
        user_id=id,
        action="user.password_reset",
        ip_address=request.client.host if request.client else None,
        details=json.dumps({"reset_by_admin": True})
    )
    
    return {"password": new_password}

@router.delete("/users/{id}")
async def delete_user(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user (soft delete)."""
    user = await UserRepository.get_by_id(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    await db.commit()
    
    # Revoke all tokens
    await RefreshTokenRepository.revoke_all_user_tokens(db, user.id)
    
    await AuditLogRepository.create(
        db=db,
        user_id=id,
        action="user.deleted",
        ip_address=request.client.host if request.client else None,
        details=json.dumps({"deactivated": True})
    )
    
    return {"message": "User deactivated"}

# Device Management
@router.get("/devices")
async def list_devices(
    db: AsyncSession = Depends(get_db)
):
    """List all device pairings."""
    result = await db.execute(
        select(DevicePairing).options(selectinload(DevicePairing.user)).order_by(DevicePairing.created_at.desc())
    )
    devices = result.scalars().all()
    
    return {
        "data": [
            {
                "id": d.id,
                "android_id": d.android_id,
                "user_id": d.user_id,
                "user": {
                    "id": d.user.id,
                    "nrp": d.user.nrp,
                    "nama": d.user.nama,
                    "email": d.user.email,
                } if d.user else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
            }
            for d in devices
        ],
        "total": len(devices)
    }

@router.delete("/devices/{android_id}")
async def delete_device(
    android_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Unpair device (remove from device_pairing)."""
    result = await db.execute(
        select(DevicePairing).where(DevicePairing.android_id == android_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await db.delete(device)
    await db.commit()
    
    await AuditLogRepository.create(
        db=db,
        user_id=device.user_id,
        action="device.unpaired",
        ip_address=request.client.host if request.client else None,
        details=json.dumps({"android_id": android_id})
    )
    
    return {"message": "Device unpaired"}

# Audit Logs
@router.get("/audit-logs")
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),  # YYYY-MM-DD
    end_date: Optional[str] = Query(None)
):
    """List audit logs with filters."""
    from sqlalchemy import select, and_
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    conditions = []
    if action:
        conditions.append(AuditLog.action == action)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if start_date:
        conditions.append(AuditLog.created_at >= datetime.fromisoformat(f"{start_date}T00:00:00"))
    if end_date:
        conditions.append(AuditLog.created_at <= datetime.fromisoformat(f"{end_date}T23:59:59"))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    logs = result.scalars().all()
    
    # Count total
    count_query = select(AuditLog)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())
    
    # Load users for these logs (optional)
    # We'll return user_id and maybe some basic info
    
    return {
        "data": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "ip_address": log.ip_address,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) // limit,
    }
