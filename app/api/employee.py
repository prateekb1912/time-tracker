from ast import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.employee import EmployeeSchema

router = APIRouter(prefix="/employee", tags=["employee"])

@router.post("/", response_model=EmployeeSchema, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeSchema, db: Session = Depends(get_db)):
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
def update_employee(employee_id: str, payload: EmployeeSchema, db: Session = Depends(get_db)):
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(employee, key, value)
    db.commit()
    db.refresh(employee)
    return EmployeeSchema.model_validate(employee)

@router.delete("/{employee_id}", status_code=204)
def deactivate_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee.deactivated = datetime.now(timezone.utc)
    db.commit()

@router.get("/", response_model=List[EmployeeSchema])
def list_employees(
    select: str = Query(default=None, description="Comma-separated list of fields to return"),
    db: Session = Depends(get_db)
):
    employees = db.query(Employee).all()

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

    return employees