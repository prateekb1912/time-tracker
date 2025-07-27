from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, mapped_column
from app.models.base import Base, timestamp, default_uuid
from sqlalchemy.orm import relationship

class Screenshot(Base):
    __tablename__ = "screenshots"
    id = Column(String(36), primary_key=True, default=default_uuid)
    
    # Screenshot metadata
    file_path = Column(String(500), nullable=False)  # Path to screenshot file
    file_size = Column(String(50), nullable=True)    # File size in bytes
    image_format = Column(String(10), default="png") # Image format (png, jpg, etc.)
    
    # Permission and capture info
    permission_granted = Column(Boolean, nullable=False)  # Whether permissions were granted
    capture_successful = Column(Boolean, default=True)    # Whether screenshot was captured successfully
    capture_error = Column(Text, nullable=True)           # Error message if capture failed
    
    # Timestamps
    captured_at = Column(DateTime, nullable=False)        # When screenshot was taken
    created_at = Column(DateTime, default=timestamp)
    updated_at = Column(DateTime, default=timestamp, onupdate=timestamp)
    
    # Relationships
    employee_id = mapped_column(ForeignKey("employees.id"), nullable=False)
    time_entry_id = mapped_column(ForeignKey("time_entries.id"), nullable=True)  # Optional link to time entry
    
    # Relationships
    employee = relationship("Employee", back_populates="screenshots")
    time_entry = relationship("TimeEntry", back_populates="screenshots") 