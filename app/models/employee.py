from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    type = Column(String, default="personal")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    deactivated = Column(DateTime, default=None)
    invited = Column(DateTime, default=datetime.now(timezone.utc))

    projects = relationship("Project", secondary="project_employees", back_populates="employees")
