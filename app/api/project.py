from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.employee import Employee
from app.models.project import Project
from app.schemas.project import ProjectSchema, ProjectCreateSchema, ProjectUpdateSchema

router = APIRouter(prefix="/project", tags=["project"])

@router.post("/", response_model=ProjectSchema)
def create_project(
    project_data: ProjectCreateSchema,
    db: Session = Depends(get_db)
):
    # Create the Project
    project = Project(
        name=project_data.name,
        description=project_data.description,
        active=project_data.active,
        statuses=project_data.statuses,
        priorities=project_data.priorities
    )

    # Validate and add employees
    if project_data.employees:
        employees = db.query(Employee).filter(Employee.id.in_(project_data.employees)).all()
        if len(employees) != len(project_data.employees):
            raise HTTPException(status_code=400, detail="Some employee IDs are invalid.")
        
        # Check that all employees are active
        deactivated_employees = [emp for emp in employees if emp.deactivated]
        if deactivated_employees:
            deactivated_names = [emp.name for emp in deactivated_employees]
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot assign deactivated employees to project: {', '.join(deactivated_names)}"
            )
        
        project.employees.extend(employees)

    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectSchema.model_validate(project)

@router.get("/", response_model=List[ProjectSchema])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return [ProjectSchema.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectSchema)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectSchema.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectSchema)
def update_project(project_id: UUID, data: ProjectUpdateSchema, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update only provided fields
    update_data = data.dict(exclude_unset=True)
    
    if "name" in update_data:
        project.name = update_data["name"]
    if "description" in update_data:
        project.description = update_data["description"]
    if "active" in update_data:
        project.active = update_data["active"]
    if "statuses" in update_data:
        project.statuses = update_data["statuses"]
    if "priorities" in update_data:
        project.priorities = update_data["priorities"]

    if "employees" in update_data:
        employees = db.query(Employee).filter(Employee.id.in_(update_data["employees"])).all()
        if len(employees) != len(update_data["employees"]):
            raise HTTPException(status_code=400, detail="Some employee IDs are invalid.")
        
        # Check that all employees are active
        deactivated_employees = [emp for emp in employees if emp.deactivated]
        if deactivated_employees:
            deactivated_names = [emp.name for emp in deactivated_employees]
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot assign deactivated employees to project: {', '.join(deactivated_names)}"
            )
        
        project.employees = employees

    db.commit()
    db.refresh(project)
    return ProjectSchema.model_validate(project)


@router.post("/{project_id}/employees/{employee_id}")
def assign_employee_to_project(project_id: UUID, employee_id: str, db: Session = Depends(get_db)):
    """Assign a specific employee to a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if employee.deactivated:
        raise HTTPException(status_code=400, detail="Cannot assign deactivated employee to project")
    
    if employee in project.employees:
        raise HTTPException(status_code=400, detail="Employee is already assigned to this project")
    
    project.employees.append(employee)
    db.commit()
    db.refresh(project)
    return {"message": f"Employee {employee.name} assigned to project {project.name}"}


@router.delete("/{project_id}/employees/{employee_id}")
def remove_employee_from_project(project_id: UUID, employee_id: str, db: Session = Depends(get_db)):
    """Remove a specific employee from a project (offboarding)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if employee not in project.employees:
        raise HTTPException(status_code=400, detail="Employee is not assigned to this project")
    
    project.employees.remove(employee)
    db.commit()
    return {"message": f"Employee {employee.name} removed from project {project.name}"}


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()