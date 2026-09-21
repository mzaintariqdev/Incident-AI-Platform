import json
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Ticket, TicketStatus, TicketSeverity, User, UserRole
from app.schemas import TicketCreate, TicketOut, TicketUpdate, PaginatedTickets
from app.redis_client import get_redis
from app.ws import manager

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketOut, status_code=201)
async def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        source="manual",
        created_by_id=current_user.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # queue it for the AI worker to classify + summarize
    redis = get_redis()
    redis.rpush("ticket_queue", json.dumps({"ticket_id": ticket.id}))

    await manager.broadcast({"event": "ticket_created", "ticket_id": ticket.id})
    return ticket


@router.get("", response_model=PaginatedTickets)
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    severity: Optional[TicketSeverity] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Ticket)
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if severity:
        query = query.filter(Ticket.severity == severity)

    total = query.count()
    items = (
        query.order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedTickets(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    # only agents/admins can change ticket status/severity, not plain viewers
    current_user: User = Depends(require_role(UserRole.admin, UserRole.agent)),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket_update.status is not None:
        ticket.status = ticket_update.status
    if ticket_update.severity is not None:
        ticket.severity = ticket_update.severity

    db.commit()
    db.refresh(ticket)

    await manager.broadcast({"event": "ticket_updated", "ticket_id": ticket.id, "status": ticket.status.value})
    return ticket
