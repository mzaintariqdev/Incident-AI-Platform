import hashlib
import hmac
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Ticket
from app.redis_client import get_redis
from app.schemas import WebhookIssuePayload, TicketOut
from app.ws import manager

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    """GitHub-style HMAC-SHA256 signature check: 'sha256=<hexdigest>'."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(settings.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)


@router.post("/issues", response_model=TicketOut, status_code=201)
async def receive_issue_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    signature = request.headers.get("X-Signature-256", "")

    if not verify_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = WebhookIssuePayload(**json.loads(raw_body))

    # dedup: if we've already ingested this external_id, don't create a duplicate ticket
    existing = db.query(Ticket).filter(Ticket.external_id == payload.external_id).first()
    if existing:
        return existing

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        source=payload.source,
        external_id=payload.external_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    redis = get_redis()
    redis.rpush("ticket_queue", json.dumps({"ticket_id": ticket.id}))

    await manager.broadcast({"event": "ticket_created", "ticket_id": ticket.id})
    return ticket
