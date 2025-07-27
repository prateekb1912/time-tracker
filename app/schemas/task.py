from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class TaskCreateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = ""
    status: Optional[str] = "active"
    priority: Optional[str] = "medium"
    billable: Optional[bool] = True
    project_id: str
    employees: Optional[List[str]] = []

class TaskUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    billable: Optional[bool] = None
    employees: Optional[List[str]] = None

class TaskSchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    status: Optional[str] = "active"
    priority: Optional[str] = "medium"
    billable: Optional[bool] = True
    project_id: str
    employees: List[str]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True