from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .model import Employee
from .schemas import EmployeeCreate, EmployeeUpdate
from typing import List, Optional
import csv
from io import StringIO

class EmployeeRepository:

    @staticmethod
    async def get_by_id(db: AsyncSession, employee_id: int) -> Optional[Employee]:
        result = await db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_nrp(db: AsyncSession, nrp: str) -> Optional[Employee]:
        result = await db.execute(
            select(Employee).where(Employee.nrp == nrp)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Employee]:
        result = await db.execute(
            select(Employee).where(Employee.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, employee_data: EmployeeCreate, created_by: int) -> Employee:
        db_employee = Employee(
            **employee_data.dict(),
            created_by=created_by
        )
        db.add(db_employee)
        await db.commit()
        await db.refresh(db_employee)
        return db_employee

    @staticmethod
    async def update(db: AsyncSession, employee_id: int, update_data: EmployeeUpdate) -> Optional[Employee]:
        stmt = (
            update(Employee)
            .where(Employee.id == employee_id)
            .values(**update_data.dict(exclude_unset=True))
        )
        await db.execute(stmt)
        await db.commit()
        return await EmployeeRepository.get_by_id(db, employee_id)

    @staticmethod
    async def delete(db: AsyncSession, employee_id: int) -> bool:
        stmt = (
            update(Employee)
            .where(Employee.id == employee_id)
            .values(is_active=False)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        section: Optional[str] = None,
        crew: Optional[str] = None,
        is_active: Optional[bool] = True,
        current_user_id: Optional[int] = None,
        is_admin: bool = False
    ) -> List[Employee]:
        stmt = select(Employee)
        if not is_admin:
            stmt = stmt.where(Employee.created_by == current_user_id)
        if section:
            stmt = stmt.where(Employee.section == section)
        if crew:
            stmt = stmt.where(Employee.crew == crew)
        if is_active is not None:
            stmt = stmt.where(Employee.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def bulk_create(db: AsyncSession, employees_data: list[EmployeeCreate], created_by: int) -> List[Employee]:
        db_employees = [
            Employee(**emp.dict(), created_by=created_by)
            for emp in employees_data
        ]
        db.add_all(db_employees)
        await db.commit()
        for emp in db_employees:
            await db.refresh(emp)
        return db_employees

    @staticmethod
    async def import_from_csv(
        db: AsyncSession,
        csv_content: str,
        created_by: int,
        delimiter: str = ',',
        quotechar: str = '"'
    ) -> dict:
        """
        Import employees from CSV string.
        Expected columns: NRP, Nama, Section, Crew, Posisi, TargetSS, Status, Jabatan, LastUpdate
        Returns summary: total_rows, imported, skipped, errors.
        """
        reader = csv.DictReader(StringIO(csv_content), delimiter=delimiter, quotechar=quotechar)
        total_rows = 0
        imported = 0
        skipped = 0
        errors = []

        employees_to_create = []
        row_num = 0

        for row_num, row in enumerate(reader, start=1):
            total_rows += 1
            try:
                nrp = (row.get('NRP') or '').strip()
                nama = (row.get('Nama') or '').strip()
                section = (row.get('Section') or '').strip()
                crew = (row.get('Crew') or '').strip() or None
                posisi = (row.get('Posisi') or '').strip()
                target_ss_str = (row.get('TargetSS') or '').strip()
                status = (row.get('Status') or '').strip() or None
                jabatan = (row.get('Jabatan') or '').strip() or None
                last_update_str = (row.get('LastUpdate') or '').strip() or None

                # Required fields
                if not nrp or not nama or not section or not posisi:
                    raise ValueError("Missing required fields (NRP, Nama, Section, Posisi)")

                # Duplicate check
                if await EmployeeRepository.get_by_nrp(db, nrp):
                    raise ValueError(f"NRP {nrp} already exists")

                # Parse target_ss
                target_ss = int(target_ss_str) if target_ss_str and target_ss_str.isdigit() else None

                # Parse last_update (expected format: YYYY-MM-DD HH:MM:SS)
                last_update = None
                if last_update_str:
                    try:
                        last_update = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass  # ignore invalid date

                # Determine is_active from status (case-insensitive)
                is_active = (status.lower() == 'aktif') if status else True

                employee_data = EmployeeCreate(
                    nrp=nrp,
                    nama=nama,
                    email=None,
                    section=section,
                    crew=crew,
                    posisi=posisi,
                    target_ss=target_ss,
                    status=status,
                    jabatan=jabatan,
                    last_update=last_update,
                    is_active=is_active
                )
                employees_to_create.append(employee_data)

            except Exception as e:
                skipped += 1
                errors.append({"row": row_num, "error": str(e)})

        # Bulk insert
        if employees_to_create:
            created_employees = await EmployeeRepository.bulk_create(db, employees_to_create, created_by)
            imported = len(created_employees)

        return {
            "total_rows": total_rows,
            "imported": imported,
            "skipped": skipped,
            "errors": errors
        }
