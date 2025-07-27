from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskSchema
from app.core.database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskSchema)
def create_task(
    task_data: TaskSchema,
    db: Session = Depends(get_db)
):
    task = Task(
        name=task_data.name,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        billable=task_data.billable,
        project_id=task_data.project_id,
        employees=task_data.employees,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskSchema.model_validate(task)

@router.get("/{task_id}", response_model=TaskSchema)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskSchema.model_validate(task)

@router.get("/", response_model=List[TaskSchema])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return [TaskSchema.model_validate(task) for task in tasks]


@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return TaskSchema.model_validate(task)
