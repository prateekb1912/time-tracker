from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class EmployeeCreateSchema(BaseModel):
    name: str
    email: EmailStr
    type: Optional[str] = "personal"

class EmployeeUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    type: Optional[str] = None

class EmployeeSchema(BaseModel):
    id: str
    name: str
    email: str
    type: Optional[str] = "personal"
    created_at: Optional[datetime] = None
    deactivated: Optional[datetime] = None
    invited: Optional[datetime] = None
    projects: Optional[List[str]] = []

    class Config:
        from_attributes = True
