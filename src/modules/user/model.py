# User module: SQLAlchemy model and Pydantic schemas
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base
from src.modules.role.model import Role

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nrp = Column(String(50), unique=True, nullable=False, index=True)  # employee number / username
    nama = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, default=2)  # default: user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to Role
    role = relationship("Role", back_populates="users")
    
    # Relationship to Employees (manpower)
    employees = relationship("Employee", back_populates="creator")

    # Relationship to RefreshTokens
    refresh_tokens = relationship("RefreshToken", back_populates="user")

    # Relationship to Devices (device pairing)
    devices = relationship("DevicePairing", back_populates="user")

    # Relationship to AuditLogs
    audit_logs = relationship("AuditLog", back_populates="user")

    @property
    def role_name(self) -> str:
        """Return role name for serialization."""
        return self.role.name if self.role else ""
