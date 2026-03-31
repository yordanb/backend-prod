from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from src.core.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    nrp = Column(String(50), unique=True, nullable=False)
    nama = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    section = Column(String(100), nullable=False)
    crew = Column(String(100), nullable=True)
    posisi = Column(String(100), nullable=False)
    target_ss = Column(Integer, nullable=True)
    status = Column(String(20), nullable=True)
    jabatan = Column(String(100), nullable=True)
    last_update = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to creator (User)
    creator = relationship("User", back_populates="employees")
