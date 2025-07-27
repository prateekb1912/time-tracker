from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Numeric, Text, mapped_column
from app.models.base import Base, timestamp, default_uuid
from sqlalchemy.orm import relationship

class TimeEntry(Base):
    __tablename__ = "time_entries"
    id = Column(String(36), primary_key=True, default=default_uuid)
    
    # Core time tracking fields
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Numeric(10, 2), nullable=False)  # Duration in minutes
    description = Column(Text, nullable=True)
    billable = Column(Boolean, default=True)
    
    # Relationships
    employee_id = mapped_column(ForeignKey("employees.id"), nullable=False)
    project_id = mapped_column(ForeignKey("projects.id"), nullable=False)
    task_id = mapped_column(ForeignKey("tasks.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=timestamp)
    updated_at = Column(DateTime, default=timestamp, onupdate=timestamp)
    
    # Relationships
    employee = relationship("Employee", back_populates="time_entries")
    project = relationship("Project", back_populates="time_entries")
    task = relationship("Task", back_populates="time_entries")
    screenshots = relationship("Screenshot", back_populates="time_entry") 