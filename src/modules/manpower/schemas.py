from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional

class EmployeeCreate(BaseModel):
    nrp: str = Field(..., min_length=1, max_length=50)
    nama: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    section: str = Field(..., min_length=1, max_length=100)
    crew: Optional[str] = Field(None, max_length=100)
    posisi: str = Field(..., min_length=1, max_length=100)
    target_ss: Optional[int] = None
    status: Optional[str] = Field(None, max_length=20)
    jabatan: Optional[str] = Field(None, max_length=100)
    last_update: Optional[datetime] = None
    is_active: Optional[bool] = True

class EmployeeUpdate(BaseModel):
    nrp: Optional[str] = Field(None, min_length=1, max_length=50)
    nama: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    section: Optional[str] = Field(None, min_length=1, max_length=100)
    crew: Optional[str] = Field(None, max_length=100)
    posisi: Optional[str] = Field(None, min_length=1, max_length=100)
    target_ss: Optional[int] = None
    status: Optional[str] = Field(None, max_length=20)
    jabatan: Optional[str] = Field(None, max_length=100)
    last_update: Optional[datetime] = None
    is_active: Optional[bool] = None

class EmployeeResponse(BaseModel):
    id: int
    nrp: str
    nama: str
    email: Optional[str]
    section: str
    crew: Optional[str]
    posisi: str
    target_ss: Optional[int]
    status: Optional[str]
    jabatan: Optional[str]
    last_update: Optional[datetime]
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class CSVUploadResponse(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    errors: list[dict]
