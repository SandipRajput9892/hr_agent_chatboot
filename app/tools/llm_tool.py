import uuid
from datetime import date

from app.core.logger import get_logger

logger = get_logger(__name__)


def _get_db():
    from app.db.database import SessionLocal
    return SessionLocal()


# ── Employee Tools ────────────────────────────────────────────────────────────

def get_employee_info(employee_id: str) -> dict:
    from app.db import models
    db = _get_db()
    try:
        emp = db.query(models.Employee).filter(
            models.Employee.id == employee_id.upper(),
            models.Employee.is_active == True,
        ).first()
        if not emp:
            return {"found": False, "message": f"Employee '{employee_id}' not found"}

        manager_name = emp.manager_name
        if emp.manager_id:
            manager = db.query(models.Employee).filter(
                models.Employee.id == emp.manager_id
            ).first()
            if manager:
                manager_name = manager.name

        return {
            "found": True,
            "employee": {
                "id": emp.id,
                "name": emp.name,
                "department": emp.department,
                "role": emp.role,
                "email": emp.email,
                "manager_id": emp.manager_id,
                "manager_name": manager_name,
                "join_date": emp.join_date,
                "location": emp.location,
            },
        }
    finally:
        db.close()


def get_employee_name(employee_id: str) -> str:
    result = get_employee_info(employee_id)
    if result.get("found"):
        return result["employee"]["name"]
    return employee_id or "Guest"


# ── Leave Tools ───────────────────────────────────────────────────────────────

def get_leave_balance(employee_id: str) -> dict:
    from app.db import models
    db = _get_db()
    try:
        eid = employee_id.upper()
        emp = db.query(models.Employee).filter(
            models.Employee.id == eid, models.Employee.is_active == True
        ).first()
        if not emp:
            return {"found": False, "message": f"Employee '{employee_id}' not found"}

        lb = db.query(models.LeaveBalance).filter(
            models.LeaveBalance.employee_id == eid
        ).first()
        return {
            "found": True,
            "employee_id": eid,
            "employee_name": emp.name,
            "leave_balance": {
                "annual": lb.annual if lb else 0,
                "sick": lb.sick if lb else 0,
                "casual": lb.casual if lb else 0,
            },
        }
    finally:
        db.close()


def submit_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
) -> dict:
    from app.tools.calculator import calculate_working_days
    from app.db import models
    db = _get_db()
    try:
        eid = employee_id.upper()
        emp = db.query(models.Employee).filter(
            models.Employee.id == eid, models.Employee.is_active == True
        ).first()
        if not emp:
            return {"success": False, "message": f"Employee '{employee_id}' not found"}

        if leave_type not in {"annual", "sick", "casual"}:
            return {"success": False, "message": "leave_type must be 'annual', 'sick', or 'casual'"}

        days_result = calculate_working_days(start_date, end_date)
        if "error" in days_result:
            return {"success": False, "message": days_result["error"]}

        days_requested = days_result["working_days"]

        lb = db.query(models.LeaveBalance).filter(
            models.LeaveBalance.employee_id == eid
        ).first()
        available = getattr(lb, leave_type, 0) if lb else 0

        if days_requested > available:
            return {
                "success": False,
                "message": (
                    f"Insufficient {leave_type} leave. "
                    f"Requested: {days_requested} day(s), Available: {available} day(s)."
                ),
            }

        request_id = f"LR{uuid.uuid4().hex[:6].upper()}"
        record = models.LeaveRequest(
            id=request_id,
            employee_id=eid,
            employee_name=emp.name,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=reason,
            status="pending",
            submitted_at=date.today().isoformat(),
        )
        db.add(record)

        # Deduct balance immediately (admin can reject to restore)
        setattr(lb, leave_type, available - days_requested)
        db.commit()

        logger.info(f"Leave request {request_id} submitted for {eid}")
        return {
            "success": True,
            "request_id": request_id,
            "message": (
                f"Leave request {request_id} submitted. "
                f"{days_requested} {leave_type} day(s) from {start_date} to {end_date}."
            ),
            "days_requested": days_requested,
            "remaining_balance": available - days_requested,
        }
    finally:
        db.close()


def get_leave_requests(employee_id: str, status: str = "all") -> dict:
    from app.db import models
    db = _get_db()
    try:
        eid = employee_id.upper()
        emp = db.query(models.Employee).filter(models.Employee.id == eid).first()
        if not emp:
            return {"found": False, "message": f"Employee '{employee_id}' not found"}

        q = db.query(models.LeaveRequest).filter(models.LeaveRequest.employee_id == eid)
        if status != "all":
            q = q.filter(models.LeaveRequest.status == status)
        reqs = q.order_by(models.LeaveRequest.created_at.desc()).all()

        return {
            "found": True,
            "employee_id": eid,
            "total": len(reqs),
            "requests": [
                {
                    "request_id": r.id,
                    "leave_type": r.leave_type,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "days_requested": r.days_requested,
                    "reason": r.reason,
                    "status": r.status,
                    "submitted_at": r.submitted_at,
                }
                for r in reqs
            ],
        }
    finally:
        db.close()
