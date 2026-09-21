from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Ticket, TicketStatus, TicketSeverity, User
from app.schemas import AnalyticsSummary, SeverityBreakdown, VolumePoint

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(
    days: int = 14,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status.in_([TicketStatus.open, TicketStatus.in_progress])).count()

    # average resolution time, in hours, for resolved/closed tickets
    resolved = db.query(Ticket).filter(Ticket.status.in_([TicketStatus.resolved, TicketStatus.closed])).all()
    if resolved:
        total_hours = sum((t.updated_at - t.created_at).total_seconds() / 3600 for t in resolved)
        avg_resolution_hours = round(total_hours / len(resolved), 2)
    else:
        avg_resolution_hours = None

    severity_rows = (
        db.query(Ticket.severity, func.count(Ticket.id))
        .group_by(Ticket.severity)
        .all()
    )
    severity_breakdown = [SeverityBreakdown(severity=s.value, count=c) for s, c in severity_rows]

    since = datetime.utcnow() - timedelta(days=days)
    volume_rows = (
        db.query(func.date(Ticket.created_at), func.count(Ticket.id))
        .filter(Ticket.created_at >= since)
        .group_by(func.date(Ticket.created_at))
        .order_by(func.date(Ticket.created_at))
        .all()
    )
    volume_by_day = [VolumePoint(date=str(d), count=c) for d, c in volume_rows]

    avg_conf = db.query(func.avg(Ticket.ai_confidence)).filter(Ticket.ai_confidence.isnot(None)).scalar()

    return AnalyticsSummary(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        avg_resolution_hours=avg_resolution_hours,
        severity_breakdown=severity_breakdown,
        volume_by_day=volume_by_day,
        avg_ai_confidence=round(avg_conf, 2) if avg_conf is not None else None,
    )
