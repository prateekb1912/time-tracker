from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.project import Project
from app.models.employee import Employee
from app.schemas.task import TaskSchema, TaskCreateSchema, TaskUpdateSchema
from app.core.database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreateSchema,
    db: Session = Depends(get_db)
):
    """Create a new task"""
    # Validate that project exists
    if not task_data.project_id:
        raise HTTPException(status_code=400, detail="Project ID is required")
    
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project already has a default task
    existing_task = db.query(Task).filter(Task.project_id == task_data.project_id).first()
    if existing_task:
        raise HTTPException(
            status_code=400, 
            detail=f"Project already has a default task. Use the existing task ID: {existing_task.id}"
        )
    
    # Validate employees are assigned to the project
    employees = []
    if task_data.employees:
        project_employee_ids = [emp.id for emp in project.employees]
        invalid_employees = [emp_id for emp_id in task_data.employees if emp_id not in project_employee_ids]
        if invalid_employees:
            raise HTTPException(
                status_code=400, 
                detail=f"Employees {invalid_employees} are not assigned to this project"
            )
        
        # Get employee objects
        employees = db.query(Employee).filter(Employee.id.in_(task_data.employees)).all()
        
        # Check that all employees are active
        deactivated_employees = [emp for emp in employees if emp.deactivated]
        if deactivated_employees:
            deactivated_names = [emp.name for emp in deactivated_employees]
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot assign deactivated employees to task: {', '.join(deactivated_names)}"
            )
    
    task = Task(
        name=task_data.name or f"Default Task - {project.name}",
        description=task_data.description or f"Default task for project {project.name}",
        status=task_data.status or "active",
        priority=task_data.priority or "medium",
        billable=task_data.billable,
        project_id=task_data.project_id,
        employees=employees,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskSchema.model_validate(task)

@router.post("/projects/{project_id}/default", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_default_task_for_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Create a default task for a project (1:1 mapping as recommended)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project already has a default task
    existing_task = db.query(Task).filter(Task.project_id == project_id).first()
    if existing_task:
        return TaskSchema.model_validate(existing_task)
    
    # Create default task with all project employees
    task = Task(
        name=f"Default Task - {project.name}",
        description=f"Default task for project {project.name}",
        status="active",
        priority="medium",
        billable=True,
        project_id=project_id,
        employees=project.employees,  # Assign all project employees to the default task
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskSchema.model_validate(task)

@router.get("/{task_id}", response_model=TaskSchema)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get task by ID"""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskSchema.model_validate(task)

@router.get("/", response_model=List[TaskSchema])
def list_tasks(db: Session = Depends(get_db)):
    """List all tasks"""
    tasks = db.query(Task).all()
    return [TaskSchema.model_validate(task) for task in tasks]

@router.get("/projects/{project_id}/default", response_model=TaskSchema)
def get_project_default_task(project_id: str, db: Session = Depends(get_db)):
    """Get the default task for a project"""
    task = db.query(Task).filter(Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="No default task found for this project")
    return TaskSchema.model_validate(task)

@router.patch("/{task_id}", response_model=TaskSchema)
def update_task(task_id: str, task_data: TaskUpdateSchema, db: Session = Depends(get_db)):
    """Update task details"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Validate employees if being updated
    if task_data.employees is not None:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        project_employee_ids = [emp.id for emp in project.employees]
        invalid_employees = [emp_id for emp_id in task_data.employees if emp_id not in project_employee_ids]
        if invalid_employees:
            raise HTTPException(
                status_code=400, 
                detail=f"Employees {invalid_employees} are not assigned to this project"
            )
        
        # Get employee objects and validate they're active
        employees = db.query(Employee).filter(Employee.id.in_(task_data.employees)).all()
        deactivated_employees = [emp for emp in employees if emp.deactivated]
        if deactivated_employees:
            deactivated_names = [emp.name for emp in deactivated_employees]
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot assign deactivated employees to task: {', '.join(deactivated_names)}"
            )
        
        task.employees = employees
    
    # Update other fields
    update_data = task_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key != 'employees':  # Already handled above
            setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return TaskSchema.model_validate(task)

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
