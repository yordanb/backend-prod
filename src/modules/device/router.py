from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.device.repository import DeviceRepository
from src.modules.device.schemas import (
    DeviceResponse,
    PaginatedDevicesResponse,
    DeviceDetailResponse,
)
from src.modules.auth.dependencies import get_current_admin

router = APIRouter(prefix="/admin/devices", tags=["admin-devices"])


@router.get("", response_model=PaginatedDevicesResponse)
def get_devices(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[dict, Depends(get_current_admin)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    repo = DeviceRepository(db)
    devices, total = repo.get_devices(page=page, limit=limit)
    # Convert Device objects to response shape
    data: list[DeviceResponse] = []
    for d in devices:
        user_dict = None
        if d.user:
            user_dict = {
                "id": d.user.id,
                "nrp": d.user.nrp,
                "nama": d.user.nama,
                "email": d.user.email,
                "role_name": d.user.role.name if d.user.role else None,
            }
        data.append(
            DeviceResponse(
                id=d.id,
                android_id=d.android_id,
                user_id=d.user_id,
                user=user_dict,
                created_at=d.created_at.isoformat() if d.created_at else None,
                last_used_at=d.last_used_at.isoformat() if d.last_used_at else None,
            )
        )
    total_pages = (total + limit - 1) // limit
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages,
    }


@router.get("/{device_id}", response_model=DeviceDetailResponse)
def get_device(
    device_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[dict, Depends(get_current_admin)],
):
    repo = DeviceRepository(db)
    device = repo.get_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    user_dict = None
    if device.user:
        user_dict = {
            "id": device.user.id,
            "nrp": device.user.nrp,
            "nama": device.user.nama,
            "email": device.user.email,
            "role_name": device.user.role.name if device.user.role else None,
        }
    return DeviceDetailResponse(
        id=device.id,
        android_id=device.android_id,
        user_id=device.user_id,
        user=user_dict,
        created_at=device.created_at,
        last_used_at=device.last_used_at,
    )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[dict, Depends(get_current_admin)],
):
    repo = DeviceRepository(db)
    device = repo.get_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    repo.delete(device)
    db.commit()
    return None
