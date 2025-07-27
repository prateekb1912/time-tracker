from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.employee import Employee
from app.models.project import Project
from app.schemas.project import ProjectSchema

router = APIRouter(prefix="/project", tags=["project"])

@router.post("/", response_model=ProjectSchema)
def create_project(
    project_data: ProjectSchema,
    db: Session = Depends(get_db)
):
    # Create the Project
    project = Project(name=project_data.name)

    # Validate and add employees
    employees = db.query(Employee).filter(Employee.id.in_(project_data.employees)).all()
    if len(employees) != len(project_data.employees):
        raise HTTPException(status_code=400, detail="Some employee IDs are invalid.")

    project.employees.extend(employees)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/", response_model=List[ProjectSchema])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@router.get("/{project_id}", response_model=ProjectSchema)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectSchema)
def update_project(project_id: UUID, data: ProjectSchema, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.name is not None:
        project.name = data.name

    if data.employees is not None:
        employees = db.query(Employee).filter(Employee.id.in_(data.employees)).all()
        if len(employees) != len(data.employees):
            raise HTTPException(status_code=400, detail="Some employee IDs are invalid.")
        project.employees = employees

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()