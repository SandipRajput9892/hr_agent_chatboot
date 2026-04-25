from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.db.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id           = Column(String, primary_key=True)
    name         = Column(String, nullable=False)
    department   = Column(String)
    role         = Column(String)
    email        = Column(String, unique=True)
    manager_id   = Column(String, ForeignKey("employees.id"), nullable=True)
    manager_name = Column(String, nullable=True)
    join_date    = Column(String)
    location     = Column(String)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, server_default=func.now())


class LeaveBalance(Base):
    __tablename__ = "leave_balance"

    employee_id = Column(String, ForeignKey("employees.id"), primary_key=True)
    annual      = Column(Integer, default=18)
    sick        = Column(Integer, default=12)
    casual      = Column(Integer, default=6)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id             = Column(String, primary_key=True)
    employee_id    = Column(String, ForeignKey("employees.id"))
    employee_name  = Column(String)
    leave_type     = Column(String)
    start_date     = Column(String)
    end_date       = Column(String)
    days_requested = Column(Integer)
    reason         = Column(String)
    status         = Column(String, default="pending")
    submitted_at   = Column(String)
    created_at     = Column(DateTime, server_default=func.now())
