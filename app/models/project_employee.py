from sqlalchemy import Column, String, ForeignKey, Table
from app.models.base import Base

project_employees = Table(
    "project_employees", Base.metadata,
    Column("employee_id", String(36), ForeignKey("employees.id")),
    Column("project_id", String(36), ForeignKey("projects.id"))
)