from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, mapped_column
from app.models.base import Base, timestamp, default_uuid
from sqlalchemy.orm import relationship

from app.models.relationships import task_employee

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String(36), primary_key=True, default=default_uuid)
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    status = Column(String(255), nullable=False)
    priority = Column(String(255), nullable=False)
    billable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=timestamp)
    
    project_id = mapped_column(ForeignKey("projects.id"))
    project = relationship("Project", back_populates="tasks")
    
    employees = relationship("Employee", secondary=task_employee, back_populates="tasks")