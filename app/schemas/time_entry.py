from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from decimal import Decimal

class TimeEntryCreateSchema(BaseModel):
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    billable: Optional[bool] = True
    employee_id: str
    project_id: str
    task_id: str
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class TimeEntryUpdateSchema(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    billable: Optional[bool] = None
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v and values['start_time'] and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class TimeEntrySchema(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: Decimal
    description: Optional[str] = None
    billable: bool
    employee_id: str
    project_id: str
    task_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional fields for convenience
    employee_name: Optional[str] = None
    project_name: Optional[str] = None
    task_name: Optional[str] = None

    class Config:
        from_attributes = True 