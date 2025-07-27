from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.models.screenshot import Screenshot
from app.models.employee import Employee
from app.models.time_entry import TimeEntry
from app.schemas.screenshot import ScreenshotSchema, ScreenshotCreateSchema, ScreenshotUpdateSchema

router = APIRouter(prefix="/screenshots", tags=["screenshots"])

@router.post("/", response_model=ScreenshotSchema, status_code=status.HTTP_201_CREATED)
def create_screenshot(
    screenshot_data: ScreenshotCreateSchema,
    db: Session = Depends(get_db)
):
    """Create a new screenshot entry"""
    # Validate employee exists and is active
    employee = db.query(Employee).filter(Employee.id == screenshot_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if employee.deactivated:
        raise HTTPException(status_code=400, detail="Cannot create screenshot for deactivated employee")
    
    # Validate time entry if provided
    if screenshot_data.time_entry_id:
        time_entry = db.query(TimeEntry).filter(TimeEntry.id == screenshot_data.time_entry_id).first()
        if not time_entry:
            raise HTTPException(status_code=404, detail="Time entry not found")
        if time_entry.employee_id != screenshot_data.employee_id:
            raise HTTPException(status_code=400, detail="Time entry does not belong to the specified employee")
    
    screenshot = Screenshot(
        file_path=screenshot_data.file_path,
        file_size=screenshot_data.file_size,
        image_format=screenshot_data.image_format,
        permission_granted=screenshot_data.permission_granted,
        capture_successful=screenshot_data.capture_successful,
        capture_error=screenshot_data.capture_error,
        captured_at=screenshot_data.captured_at,
        employee_id=screenshot_data.employee_id,
        time_entry_id=screenshot_data.time_entry_id
    )
    
    db.add(screenshot)
    db.commit()
    db.refresh(screenshot)
    
    # Add convenience fields for response
    screenshot.employee_name = employee.name
    if screenshot.time_entry_id:
        screenshot.time_entry_duration = f"{screenshot.time_entry.duration_minutes} minutes"
    
    return ScreenshotSchema.model_validate(screenshot)

@router.get("/{screenshot_id}", response_model=ScreenshotSchema)
def get_screenshot(screenshot_id: str, db: Session = Depends(get_db)):
    """Get screenshot by ID"""
    screenshot = db.query(Screenshot).options(
        joinedload(Screenshot.employee),
        joinedload(Screenshot.time_entry)
    ).filter(Screenshot.id == screenshot_id).first()
    
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    # Add convenience fields
    screenshot.employee_name = screenshot.employee.name
    if screenshot.time_entry_id and screenshot.time_entry:
        screenshot.time_entry_duration = f"{screenshot.time_entry.duration_minutes} minutes"
    
    return ScreenshotSchema.model_validate(screenshot)

@router.get("/", response_model=List[ScreenshotSchema])
def list_screenshots(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    time_entry_id: Optional[str] = Query(None, description="Filter by time entry ID"),
    permission_granted: Optional[bool] = Query(None, description="Filter by permission status"),
    capture_successful: Optional[bool] = Query(None, description="Filter by capture success"),
    start_date: Optional[datetime] = Query(None, description="Filter by capture date (from)"),
    end_date: Optional[datetime] = Query(None, description="Filter by capture date (to)"),
    db: Session = Depends(get_db)
):
    """List screenshots with optional filtering"""
    query = db.query(Screenshot).options(
        joinedload(Screenshot.employee),
        joinedload(Screenshot.time_entry)
    )
    
    if employee_id:
        query = query.filter(Screenshot.employee_id == employee_id)
    if time_entry_id:
        query = query.filter(Screenshot.time_entry_id == time_entry_id)
    if permission_granted is not None:
        query = query.filter(Screenshot.permission_granted == permission_granted)
    if capture_successful is not None:
        query = query.filter(Screenshot.capture_successful == capture_successful)
    if start_date:
        query = query.filter(Screenshot.captured_at >= start_date)
    if end_date:
        query = query.filter(Screenshot.captured_at <= end_date)
    
    screenshots = query.order_by(Screenshot.captured_at.desc()).all()
    
    # Add convenience fields
    for screenshot in screenshots:
        screenshot.employee_name = screenshot.employee.name
        if screenshot.time_entry_id and screenshot.time_entry:
            screenshot.time_entry_duration = f"{screenshot.time_entry.duration_minutes} minutes"
    
    return [ScreenshotSchema.model_validate(screenshot) for screenshot in screenshots]

@router.patch("/{screenshot_id}", response_model=ScreenshotSchema)
def update_screenshot(
    screenshot_id: str,
    screenshot_data: ScreenshotUpdateSchema,
    db: Session = Depends(get_db)
):
    """Update screenshot"""
    screenshot = db.query(Screenshot).options(
        joinedload(Screenshot.employee),
        joinedload(Screenshot.time_entry)
    ).filter(Screenshot.id == screenshot_id).first()
    
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    # Validate time entry if being updated
    if screenshot_data.time_entry_id is not None:
        if screenshot_data.time_entry_id:
            time_entry = db.query(TimeEntry).filter(TimeEntry.id == screenshot_data.time_entry_id).first()
            if not time_entry:
                raise HTTPException(status_code=404, detail="Time entry not found")
            if time_entry.employee_id != screenshot.employee_id:
                raise HTTPException(status_code=400, detail="Time entry does not belong to the screenshot's employee")
    
    # Update fields
    update_data = screenshot_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(screenshot, key, value)
    
    db.commit()
    db.refresh(screenshot)
    
    # Add convenience fields
    screenshot.employee_name = screenshot.employee.name
    if screenshot.time_entry_id and screenshot.time_entry:
        screenshot.time_entry_duration = f"{screenshot.time_entry.duration_minutes} minutes"
    
    return ScreenshotSchema.model_validate(screenshot)

@router.delete("/{screenshot_id}", status_code=204)
def delete_screenshot(screenshot_id: str, db: Session = Depends(get_db)):
    """Delete screenshot"""
    screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    db.delete(screenshot)
    db.commit()

@router.get("/employees/{employee_id}/summary")
def get_employee_screenshot_summary(
    employee_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for summary"),
    end_date: Optional[datetime] = Query(None, description="End date for summary"),
    db: Session = Depends(get_db)
):
    """Get screenshot summary for an employee"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    query = db.query(Screenshot).filter(Screenshot.employee_id == employee_id)
    
    if start_date:
        query = query.filter(Screenshot.captured_at >= start_date)
    if end_date:
        query = query.filter(Screenshot.captured_at <= end_date)
    
    # Get total screenshots
    total_screenshots = query.count()
    
    # Get screenshots with permissions granted
    screenshots_with_permissions = query.filter(Screenshot.permission_granted == True).count()
    
    # Get successful captures
    successful_captures = query.filter(Screenshot.capture_successful == True).count()
    
    # Get failed captures
    failed_captures = query.filter(Screenshot.capture_successful == False).count()
    
    # Get permission issues (no permissions granted)
    permission_issues = query.filter(Screenshot.permission_granted == False).count()
    
    return {
        "employee_id": employee_id,
        "employee_name": employee.name,
        "total_screenshots": total_screenshots,
        "screenshots_with_permissions": screenshots_with_permissions,
        "successful_captures": successful_captures,
        "failed_captures": failed_captures,
        "permission_issues": permission_issues,
        "permission_grant_rate": round((screenshots_with_permissions / total_screenshots * 100), 2) if total_screenshots > 0 else 0,
        "capture_success_rate": round((successful_captures / total_screenshots * 100), 2) if total_screenshots > 0 else 0
    }

@router.get("/employees/{employee_id}/permission-status")
def get_employee_permission_status(
    employee_id: str,
    db: Session = Depends(get_db)
):
    """Get current permission status for an employee based on recent screenshots"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get the most recent screenshot
    latest_screenshot = db.query(Screenshot).filter(
        Screenshot.employee_id == employee_id
    ).order_by(Screenshot.captured_at.desc()).first()
    
    if not latest_screenshot:
        return {
            "employee_id": employee_id,
            "employee_name": employee.name,
            "has_screenshots": False,
            "current_permission_status": None,
            "last_screenshot_at": None,
            "recommendation": "No screenshots found. Start monitoring to check permission status."
        }
    
    # Get recent screenshots (last 24 hours) to determine current status
    from datetime import timedelta
    recent_cutoff = datetime.now() - timedelta(hours=24)
    
    recent_screenshots = db.query(Screenshot).filter(
        Screenshot.employee_id == employee_id,
        Screenshot.captured_at >= recent_cutoff
    ).all()
    
    if not recent_screenshots:
        current_status = "unknown"
        recommendation = "No recent screenshots. Permission status unknown."
    else:
        recent_with_permissions = [s for s in recent_screenshots if s.permission_granted]
        if len(recent_with_permissions) == len(recent_screenshots):
            current_status = "granted"
            recommendation = "Permissions are currently granted."
        elif len(recent_with_permissions) == 0:
            current_status = "denied"
            recommendation = "Permissions are currently denied. User needs to grant screen recording permissions."
        else:
            current_status = "partial"
            recommendation = "Mixed permission status. Some screenshots have permissions, others don't."
    
    return {
        "employee_id": employee_id,
        "employee_name": employee.name,
        "has_screenshots": True,
        "current_permission_status": current_status,
        "last_screenshot_at": latest_screenshot.captured_at,
        "recent_screenshots_count": len(recent_screenshots),
        "recent_with_permissions_count": len([s for s in recent_screenshots if s.permission_granted]),
        "recommendation": recommendation
    }

@router.get("/time-entries/{time_entry_id}/screenshots")
def get_time_entry_screenshots(
    time_entry_id: str,
    db: Session = Depends(get_db)
):
    """Get all screenshots for a specific time entry"""
    time_entry = db.query(TimeEntry).filter(TimeEntry.id == time_entry_id).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    screenshots = db.query(Screenshot).options(
        joinedload(Screenshot.employee)
    ).filter(Screenshot.time_entry_id == time_entry_id).order_by(Screenshot.captured_at).all()
    
    # Add convenience fields
    for screenshot in screenshots:
        screenshot.employee_name = screenshot.employee.name
        screenshot.time_entry_duration = f"{time_entry.duration_minutes} minutes"
    
    return [ScreenshotSchema.model_validate(screenshot) for screenshot in screenshots] 