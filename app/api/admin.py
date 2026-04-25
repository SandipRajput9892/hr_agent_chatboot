from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.db import models

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    id: str
    name: str
    department: str
    role: str
    email: str
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    join_date: str
    location: str


class LeaveBalanceUpdate(BaseModel):
    annual: int
    sick: int
    casual: int


class LeaveStatusUpdate(BaseModel):
    status: str  # approved / rejected


# ── Employee CRUD ─────────────────────────────────────────────────────────────

@router.post("/employees", summary="Add new employee")
def add_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    if db.query(models.Employee).filter(models.Employee.id == emp.id).first():
        raise HTTPException(400, f"Employee {emp.id} already exists")
    if db.query(models.Employee).filter(models.Employee.email == emp.email).first():
        raise HTTPException(400, f"Email {emp.email} already in use")

    new_emp = models.Employee(**emp.model_dump())
    db.add(new_emp)

    balance = models.LeaveBalance(employee_id=emp.id, annual=18, sick=12, casual=6)
    db.add(balance)
    db.commit()

    return {"message": f"{emp.name} added successfully", "employee_id": emp.id}


@router.get("/employees", summary="List all employees")
def list_employees(db: Session = Depends(get_db)):
    emps = db.query(models.Employee).filter(models.Employee.is_active == True).all()
    return [
        {
            "id": e.id, "name": e.name, "department": e.department,
            "role": e.role, "email": e.email, "location": e.location,
            "join_date": e.join_date, "manager_id": e.manager_id,
        }
        for e in emps
    ]


@router.delete("/employees/{employee_id}", summary="Delete employee")
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(404, f"Employee {employee_id} not found")
    emp.is_active = False
    db.commit()
    return {"message": f"{employee_id} deactivated"}


# ── Leave Balance ─────────────────────────────────────────────────────────────

@router.get("/employees/{employee_id}/leave-balance", summary="Get leave balance")
def get_leave_balance(employee_id: str, db: Session = Depends(get_db)):
    lb = db.query(models.LeaveBalance).filter(
        models.LeaveBalance.employee_id == employee_id
    ).first()
    if not lb:
        raise HTTPException(404, "Balance not found")
    return {"employee_id": employee_id, "annual": lb.annual, "sick": lb.sick, "casual": lb.casual}


@router.put("/employees/{employee_id}/leave-balance", summary="Update leave balance")
def update_leave_balance(
    employee_id: str,
    balance: LeaveBalanceUpdate,
    db: Session = Depends(get_db),
):
    lb = db.query(models.LeaveBalance).filter(
        models.LeaveBalance.employee_id == employee_id
    ).first()
    if not lb:
        raise HTTPException(404, "Balance not found")
    lb.annual = balance.annual
    lb.sick   = balance.sick
    lb.casual = balance.casual
    db.commit()
    return {"message": "Leave balance updated", "employee_id": employee_id}


# ── Leave Requests ────────────────────────────────────────────────────────────

@router.get("/leave-requests", summary="All pending leave requests")
def list_leave_requests(status: str = "pending", db: Session = Depends(get_db)):
    q = db.query(models.LeaveRequest)
    if status != "all":
        q = q.filter(models.LeaveRequest.status == status)
    reqs = q.order_by(models.LeaveRequest.created_at.desc()).all()
    return [
        {
            "id": r.id, "employee_id": r.employee_id, "employee_name": r.employee_name,
            "leave_type": r.leave_type, "start_date": r.start_date, "end_date": r.end_date,
            "days_requested": r.days_requested, "reason": r.reason, "status": r.status,
            "submitted_at": r.submitted_at,
        }
        for r in reqs
    ]


@router.put("/leave-requests/{request_id}", summary="Approve or reject leave request")
def update_leave_status(
    request_id: str,
    update: LeaveStatusUpdate,
    db: Session = Depends(get_db),
):
    if update.status not in {"approved", "rejected"}:
        raise HTTPException(400, "status must be 'approved' or 'rejected'")

    req = db.query(models.LeaveRequest).filter(models.LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Leave request not found")
    if req.status != "pending":
        raise HTTPException(400, f"Request already {req.status}")

    req.status = update.status

    # If rejected, restore the balance
    if update.status == "rejected":
        lb = db.query(models.LeaveBalance).filter(
            models.LeaveBalance.employee_id == req.employee_id
        ).first()
        if lb:
            setattr(lb, req.leave_type, getattr(lb, req.leave_type) + req.days_requested)

    db.commit()
    return {"message": f"Request {request_id} {update.status}"}
