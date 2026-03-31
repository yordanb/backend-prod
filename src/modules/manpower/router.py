from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.core.database import get_db
from src.deps import require_roles
from .repository import EmployeeRepository
from .schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse, CSVUploadResponse

router = APIRouter(prefix="/manpower", tags=["manpower"])

@router.get("/", response_model=List[EmployeeResponse])
async def list_employees(
    skip: int = 0,
    limit: int = 100,
    section: Optional[str] = None,
    crew: Optional[str] = None,
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin", "user"]))
):
    """
    List employees.
    - Admin: can see all employees.
    - User: can only see employees they created.
    """
    is_admin = user["role"] == "admin"
    employees = await EmployeeRepository.list_employees(
        db=db,
        skip=skip,
        limit=limit,
        section=section,
        crew=crew,
        is_active=is_active,
        current_user_id=user["user_id"],
        is_admin=is_admin
    )
    return employees

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin", "user"]))
):
    """Get employee by ID."""
    employee = await EmployeeRepository.get_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    
    # Permission: admin can access any; user can only access their own created employees
    if user["role"] != "admin" and employee.created_by != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    return employee

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """Create new employee (admin only)."""
    # Check duplicate NRP
    if await EmployeeRepository.get_by_nrp(db, employee_data.nrp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NRP {employee_data.nrp} already exists"
        )
    # Check duplicate email if provided
    if employee_data.email and await EmployeeRepository.get_by_email(db, employee_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email {employee_data.email} already exists"
        )
    
    employee = await EmployeeRepository.create(db, employee_data, created_by=user["user_id"])
    
    # TODO: AuditLogRepository.create(...)
    
    return employee

@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    update_data: EmployeeUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """Update employee (admin only)."""
    existing = await EmployeeRepository.get_by_id(db, employee_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    
    # Check duplicate NRP if changed
    if update_data.nrp and update_data.nrp != existing.nrp:
        if await EmployeeRepository.get_by_nrp(db, update_data.nrp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NRP {update_data.nrp} already exists"
            )
    # Check duplicate email if changed and provided
    if update_data.email and update_data.email != existing.email:
        if await EmployeeRepository.get_by_email(db, update_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {update_data.email} already exists"
            )
    
    employee = await EmployeeRepository.update(db, employee_id, update_data)
    return employee

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """Soft delete employee (set is_active=False) (admin only)."""
    existing = await EmployeeRepository.get_by_id(db, employee_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    
    success = await EmployeeRepository.delete(db, employee_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delete failed")
    
    # TODO: AuditLogRepository.create(...)
    
    return {"message": "Employee deactivated successfully"}

@router.post("/import", response_model=CSVUploadResponse)
async def import_employees_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_roles(["admin"]))
):
    """
    Import employees from CSV file.
    Expected columns (case-sensitive):
      NRP, Nama, Section, Crew, Posisi, TargetSS, Status, Jabatan, LastUpdate
    Returns import summary.
    """
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    content_bytes = await file.read()
    try:
        content = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding must be UTF-8"
        )
    
    result = await EmployeeRepository.import_from_csv(db, content, created_by=user["user_id"])
    return CSVUploadResponse(**result)
