from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.models.base import Base, default_uuid, timestamp

class Employee(Base):
    __tablename__ = "employees"
    id = Column(String, primary_key=True, default=default_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    type = Column(String, default="personal")
    created_at = Column(DateTime, default=timestamp)
    deactivated = Column(DateTime, default=None)
    invited = Column(DateTime, default=timestamp)

    projects = relationship("Project", secondary="project_employees", back_populates="employees")
