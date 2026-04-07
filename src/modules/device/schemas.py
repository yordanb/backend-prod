from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    android_id: str
    user_id: Optional[int] = None


class DeviceResponse(BaseModel):
    id: int
    android_id: str
    user_id: Optional[int] = None
    user: Optional[dict] = None  # { id, nrp, nama, email, role_name }
    created_at: str
    last_used_at: Optional[str] = None

    class Config:
        from_attributes = True


class DeviceDetailResponse(BaseModel):
    id: int
    android_id: str
    user_id: Optional[int] = None
    user: Optional[dict] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedDevicesResponse(BaseModel):
    data: list[DeviceResponse]
    total: int
    page: int
    limit: int
    totalPages: int
