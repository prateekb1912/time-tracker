from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.employee import EmployeeSchema, EmployeeCreateSchema, EmployeeUpdateSchema

router = APIRouter(prefix="/employee", tags=["employee"])

@router.post("/", response_model=EmployeeSchema, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreateSchema, db: Session = Depends(get_db)):
    # Check if employee with same email already exists
    existing_employee = db.query(Employee).filter(Employee.email == payload.email).first()
    if existing_employee:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    
    new_emp = Employee(name=payload.name, email=payload.email, type=payload.type, invited=datetime.now(timezone.utc))
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return EmployeeSchema.model_validate(new_emp)

@router.get("/{employee_id}", response_model=EmployeeSchema)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EmployeeSchema.model_validate(employee)

@router.put("/{employee_id}", response_model=EmployeeSchema)
def update_employee(employee_id: str, payload: EmployeeUpdateSchema, db: Session = Depends(get_db)):
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if employee is deactivated
    if employee.deactivated:
        raise HTTPException(status_code=400, detail="Cannot update deactivated employee")
    
    # Check if email is being changed and if it conflicts with existing employee
    if payload.email and payload.email != employee.email:
        existing_employee = db.query(Employee).filter(Employee.email == payload.email).first()
        if existing_employee:
            raise HTTPException(status_code=400, detail="Email already in use by another employee")
    
    # Update only provided fields
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(employee, key, value)
    
    db.commit()
    db.refresh(employee)
    return EmployeeSchema.model_validate(employee)

@router.patch("/{employee_id}/name", response_model=EmployeeSchema)
def update_employee_name(employee_id: str, name: str, db: Session = Depends(get_db)):
    """Update employee name specifically"""
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if employee.deactivated:
        raise HTTPException(status_code=400, detail="Cannot update deactivated employee")
    
    employee.name = name
    db.commit()
    db.refresh(employee)
    return EmployeeSchema.model_validate(employee)

@router.delete("/{employee_id}", status_code=204)
def deactivate_employee(employee_id: str, db: Session = Depends(get_db)):
    """Deactivate employee - sets deactivated timestamp but doesn't delete the record"""
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if employee.deactivated:
        raise HTTPException(status_code=400, detail="Employee is already deactivated")
    
    # Check if employee is assigned to any active projects
    active_projects = [p for p in employee.projects if p.active]
    if active_projects:
        project_names = [p.name for p in active_projects]
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot deactivate employee. They are still assigned to active projects: {', '.join(project_names)}"
        )
    
    employee.deactivated = datetime.now(timezone.utc)
    db.commit()

@router.get("/", response_model=List[EmployeeSchema])
def list_employees(
    active_only: bool = Query(default=True, description="Return only active employees"),
    select: str = Query(default=None, description="Comma-separated list of fields to return"),
    db: Session = Depends(get_db)
):
    query = db.query(Employee)
    
    if active_only:
        query = query.filter(Employee.deactivated.is_(None))
    
    employees = query.all()

    if select:
        selected_fields = set(select.split(","))
        results = []
        for emp in employees:
            data = {}
            if "_id" in selected_fields:
                data["_id"] = emp.id
            if "name" in selected_fields:
                data["name"] = emp.name
            if "email" in selected_fields:
                data["email"] = emp.email
            if "createdAt" in selected_fields:
                data["createdAt"] = emp.created_at
            if "updatedAt" in selected_fields:
                data["updatedAt"] = emp.updated_at
            results.append(data)
        return results

    return [EmployeeSchema.model_validate(emp) for emp in employees]