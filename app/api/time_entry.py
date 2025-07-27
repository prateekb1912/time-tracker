from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.models.time_entry import TimeEntry
from app.models.employee import Employee
from app.models.project import Project
from app.models.task import Task
from app.schemas.time_entry import TimeEntrySchema, TimeEntryCreateSchema, TimeEntryUpdateSchema

router = APIRouter(prefix="/time-entries", tags=["time-entries"])

@router.post("/", response_model=TimeEntrySchema, status_code=status.HTTP_201_CREATED)
def create_time_entry(
    time_entry_data: TimeEntryCreateSchema,
    db: Session = Depends(get_db)
):
    """Create a new time entry"""
    # Validate employee exists and is active
    employee = db.query(Employee).filter(Employee.id == time_entry_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.deactivated:
        raise HTTPException(status_code=400, detail="Cannot log time for deactivated employee")
    
    # Validate project exists and is active
    project = db.query(Project).filter(Project.id == time_entry_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.active:
        raise HTTPException(status_code=400, detail="Cannot log time for inactive project")
    
    # Validate task exists and belongs to the project
    task = db.query(Task).filter(Task.id == time_entry_data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.project_id != time_entry_data.project_id:
        raise HTTPException(status_code=400, detail="Task does not belong to the specified project")
    
    # Validate employee is assigned to the project
    if employee not in project.employees:
        raise HTTPException(status_code=400, detail="Employee is not assigned to this project")
    
    # Validate employee is assigned to the task
    if employee not in task.employees:
        raise HTTPException(status_code=400, detail="Employee is not assigned to this task")
    
    # Calculate duration in minutes
    duration = (time_entry_data.end_time - time_entry_data.start_time).total_seconds() / 60
    
    # Check for overlapping time entries
    overlapping_entries = db.query(TimeEntry).filter(
        TimeEntry.employee_id == time_entry_data.employee_id,
        TimeEntry.start_time < time_entry_data.end_time,
        TimeEntry.end_time > time_entry_data.start_time
    ).first()
    
    if overlapping_entries:
        raise HTTPException(
            status_code=400, 
            detail="Time entry overlaps with existing time entry for this employee"
        )
    
    time_entry = TimeEntry(
        start_time=time_entry_data.start_time,
        end_time=time_entry_data.end_time,
        duration_minutes=Decimal(str(duration)),
        description=time_entry_data.description,
        billable=time_entry_data.billable,
        employee_id=time_entry_data.employee_id,
        project_id=time_entry_data.project_id,
        task_id=time_entry_data.task_id
    )
    
    db.add(time_entry)
    db.commit()
    db.refresh(time_entry)
    
    # Add convenience fields for response
    time_entry.employee_name = employee.name
    time_entry.project_name = project.name
    time_entry.task_name = task.name
    
    return TimeEntrySchema.model_validate(time_entry)

@router.get("/{time_entry_id}", response_model=TimeEntrySchema)
def get_time_entry(time_entry_id: str, db: Session = Depends(get_db)):
    """Get time entry by ID"""
    time_entry = db.query(TimeEntry).options(
        joinedload(TimeEntry.employee),
        joinedload(TimeEntry.project),
        joinedload(TimeEntry.task)
    ).filter(TimeEntry.id == time_entry_id).first()
    
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Add convenience fields
    time_entry.employee_name = time_entry.employee.name
    time_entry.project_name = time_entry.project.name
    time_entry.task_name = time_entry.task.name
    
    return TimeEntrySchema.model_validate(time_entry)

@router.get("/", response_model=List[TimeEntrySchema])
def list_time_entries(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    billable_only: Optional[bool] = Query(None, description="Filter by billable entries only"),
    db: Session = Depends(get_db)
):
    """List time entries with optional filtering"""
    query = db.query(TimeEntry).options(
        joinedload(TimeEntry.employee),
        joinedload(TimeEntry.project),
        joinedload(TimeEntry.task)
    )
    
    if employee_id:
        query = query.filter(TimeEntry.employee_id == employee_id)
    if project_id:
        query = query.filter(TimeEntry.project_id == project_id)
    if task_id:
        query = query.filter(TimeEntry.task_id == task_id)
    if start_date:
        query = query.filter(TimeEntry.start_time >= start_date)
    if end_date:
        query = query.filter(TimeEntry.end_time <= end_date)
    if billable_only is not None:
        query = query.filter(TimeEntry.billable == billable_only)
    
    time_entries = query.order_by(TimeEntry.start_time.desc()).all()
    
    # Add convenience fields
    for entry in time_entries:
        entry.employee_name = entry.employee.name
        entry.project_name = entry.project.name
        entry.task_name = entry.task.name
    
    return [TimeEntrySchema.model_validate(entry) for entry in time_entries]

@router.patch("/{time_entry_id}", response_model=TimeEntrySchema)
def update_time_entry(
    time_entry_id: str,
    time_entry_data: TimeEntryUpdateSchema,
    db: Session = Depends(get_db)
):
    """Update time entry"""
    time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Update fields
    update_data = time_entry_data.dict(exclude_unset=True)
    
    # Recalculate duration if start_time or end_time changed
    if 'start_time' in update_data or 'end_time' in update_data:
        new_start = update_data.get('start_time', time_entry.start_time)
        new_end = update_data.get('end_time', time_entry.end_time)
        
        if new_end <= new_start:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")
        
        duration = (new_end - new_start).total_seconds() / 60
        update_data['duration_minutes'] = Decimal(str(duration))
        
        # Check for overlapping time entries (excluding current entry)
        overlapping_entries = db.query(TimeEntry).filter(
            TimeEntry.employee_id == time_entry.employee_id,
            TimeEntry.id != time_entry_id,
            TimeEntry.start_time < new_end,
            TimeEntry.end_time > new_start
        ).first()
        
        if overlapping_entries:
            raise HTTPException(
                status_code=400, 
                detail="Updated time entry overlaps with existing time entry for this employee"
            )
    
    for key, value in update_data.items():
        setattr(time_entry, key, value)
    
    db.commit()
    db.refresh(time_entry)
    
    # Add convenience fields
    time_entry.employee_name = time_entry.employee.name
    time_entry.project_name = time_entry.project.name
    time_entry.task_name = time_entry.task.name
    
    return TimeEntrySchema.model_validate(time_entry)

@router.delete("/{time_entry_id}", status_code=204)
def delete_time_entry(time_entry_id: str, db: Session = Depends(get_db)):
    """Delete time entry"""
    time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    db.delete(time_entry)
    db.commit()

@router.get("/employees/{employee_id}/summary")
def get_employee_time_summary(
    employee_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for summary"),
    end_date: Optional[datetime] = Query(None, description="End date for summary"),
    db: Session = Depends(get_db)
):
    """Get time summary for an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    query = db.query(TimeEntry).filter(TimeEntry.employee_id == employee_id)
    
    if start_date:
        query = query.filter(TimeEntry.start_time >= start_date)
    if end_date:
        query = query.filter(TimeEntry.end_time <= end_date)
    
    # Get total hours
    total_minutes = query.with_entities(func.sum(TimeEntry.duration_minutes)).scalar() or 0
    total_hours = float(total_minutes) / 60
    
    # Get billable hours
    billable_minutes = query.filter(TimeEntry.billable == True).with_entities(
        func.sum(TimeEntry.duration_minutes)
    ).scalar() or 0
    billable_hours = float(billable_minutes) / 60
    
    # Get project breakdown
    project_breakdown = db.query(
        TimeEntry.project_id,
        Project.name.label('project_name'),
        func.sum(TimeEntry.duration_minutes).label('total_minutes')
    ).join(Project).filter(
        TimeEntry.employee_id == employee_id
    ).group_by(TimeEntry.project_id, Project.name).all()
    
    return {
        "employee_id": employee_id,
        "employee_name": employee.name,
        "total_hours": round(total_hours, 2),
        "billable_hours": round(billable_hours, 2),
        "non_billable_hours": round(total_hours - billable_hours, 2),
        "project_breakdown": [
            {
                "project_id": item.project_id,
                "project_name": item.project_name,
                "hours": round(float(item.total_minutes) / 60, 2)
            }
            for item in project_breakdown
        ]
    }

@router.get("/projects/{project_id}/summary")
def get_project_time_summary(
    project_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for summary"),
    end_date: Optional[datetime] = Query(None, description="End date for summary"),
    db: Session = Depends(get_db)
):
    """Get time summary for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(TimeEntry).filter(TimeEntry.project_id == project_id)
    
    if start_date:
        query = query.filter(TimeEntry.start_time >= start_date)
    if end_date:
        query = query.filter(TimeEntry.end_time <= end_date)
    
    # Get total hours
    total_minutes = query.with_entities(func.sum(TimeEntry.duration_minutes)).scalar() or 0
    total_hours = float(total_minutes) / 60
    
    # Get billable hours
    billable_minutes = query.filter(TimeEntry.billable == True).with_entities(
        func.sum(TimeEntry.duration_minutes)
    ).scalar() or 0
    billable_hours = float(billable_minutes) / 60
    
    # Get employee breakdown
    employee_breakdown = db.query(
        TimeEntry.employee_id,
        Employee.name.label('employee_name'),
        func.sum(TimeEntry.duration_minutes).label('total_minutes')
    ).join(Employee).filter(
        TimeEntry.project_id == project_id
    ).group_by(TimeEntry.employee_id, Employee.name).all()
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_hours": round(total_hours, 2),
        "billable_hours": round(billable_hours, 2),
        "non_billable_hours": round(total_hours - billable_hours, 2),
        "employee_breakdown": [
            {
                "employee_id": item.employee_id,
                "employee_name": item.employee_name,
                "hours": round(float(item.total_minutes) / 60, 2)
            }
            for item in employee_breakdown
        ]
    } 