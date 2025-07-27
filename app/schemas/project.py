from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ProjectCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    active: Optional[bool] = True
    statuses: Optional[List[str]] = []
    priorities: Optional[List[str]] = []
    employees: Optional[List[str]] = []

class ProjectUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    statuses: Optional[List[str]] = None
    priorities: Optional[List[str]] = None
    employees: Optional[List[str]] = None

class ProjectSchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    active: Optional[bool] = True
    statuses: Optional[List[str]] = []
    priorities: Optional[List[str]] = []
    created_at: Optional[datetime] = None
    employees: List[str]

    class Config:
        from_attributes = True
