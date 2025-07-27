from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ProjectSchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    active: Optional[bool] = True
    statuses: Optional[list[str]] = []
    priorities: Optional[list[str]] = []
    created_at: Optional[datetime] = None
    employees: list[str]
