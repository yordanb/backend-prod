from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from src.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    ip = Column(String(50))
    user_agent = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
