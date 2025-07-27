from sqlalchemy import Column, DateTime, String, Boolean, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base, default_uuid, timestamp

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=default_uuid)
    name = Column(String, nullable=False)
    description = Column(String)
    active = Column(Boolean, default=True)
    statuses = Column(ARRAY(String), default=[])
    priorities = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=timestamp)

    employees = relationship("Employee", secondary="project_employees", back_populates="projects")
