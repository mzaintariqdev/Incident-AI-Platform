from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole, TicketStatus, TicketSeverity


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ---------- Tickets ----------

class TicketCreate(BaseModel):
    title: str
    description: str


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    severity: Optional[TicketSeverity] = None


class TicketOut(BaseModel):
    id: str
    title: str
    description: str
    status: TicketStatus
    severity: TicketSeverity
    ai_summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedTickets(BaseModel):
    items: List[TicketOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------- Analytics ----------

class SeverityBreakdown(BaseModel):
    severity: str
    count: int


class VolumePoint(BaseModel):
    date: str
    count: int


class AnalyticsSummary(BaseModel):
    total_tickets: int
    open_tickets: int
    avg_resolution_hours: Optional[float]
    severity_breakdown: List[SeverityBreakdown]
    volume_by_day: List[VolumePoint]
    avg_ai_confidence: Optional[float]


# ---------- Webhook payload (generic, GitHub-issue-shaped) ----------

class WebhookIssuePayload(BaseModel):
    external_id: str
    title: str
    description: str
    source: str = "webhook:github"
