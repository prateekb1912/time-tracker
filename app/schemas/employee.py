from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class EmployeeSchema(BaseModel):
    id: str
    name: str
    email: str
    type: Optional[str] = "personal"
    created_at: datetime
    deactivated: Optional[datetime] = None
    invited: datetime
    projects: Optional[list[str]] = []
