import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str
    employee_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    employee_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthResponse(BaseModel):
    status: str = "ok"
    model: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
