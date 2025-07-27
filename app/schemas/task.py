from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.base import timestamp

class TaskSchema(BaseModel):
    name: str
    description: Optional[str] = ""
    status: Optional[str] = ""
    priority: Optional[str] = ""
    billable: Optional[bool] = True
    project_id: Optional[str] = None
    employees: list[str]
    created_at: Optional[datetime] = timestamp