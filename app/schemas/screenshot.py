from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ScreenshotCreateSchema(BaseModel):
    file_path: str
    file_size: Optional[str] = None
    image_format: Optional[str] = "png"
    permission_granted: bool
    capture_successful: Optional[bool] = True
    capture_error: Optional[str] = None
    captured_at: datetime
    employee_id: str
    time_entry_id: Optional[str] = None

class ScreenshotUpdateSchema(BaseModel):
    file_path: Optional[str] = None
    file_size: Optional[str] = None
    image_format: Optional[str] = None
    permission_granted: Optional[bool] = None
    capture_successful: Optional[bool] = None
    capture_error: Optional[str] = None
    captured_at: Optional[datetime] = None
    time_entry_id: Optional[str] = None

class ScreenshotSchema(BaseModel):
    id: str
    file_path: str
    file_size: Optional[str] = None
    image_format: str
    permission_granted: bool
    capture_successful: bool
    capture_error: Optional[str] = None
    captured_at: datetime
    employee_id: str
    time_entry_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional fields for convenience
    employee_name: Optional[str] = None
    time_entry_duration: Optional[str] = None

    class Config:
        from_attributes = True 