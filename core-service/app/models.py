import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, Text, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    admin = "admin"
    agent = "agent"
    viewer = "viewer"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    unclassified = "unclassified"  # before the AI worker has processed it


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.agent, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets = relationship("Ticket", back_populates="created_by")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    status = Column(Enum(TicketStatus), default=TicketStatus.open, nullable=False)
    severity = Column(Enum(TicketSeverity), default=TicketSeverity.unclassified, nullable=False)

    # AI-generated fields, filled in later by the ai-worker service
    ai_summary = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_processed_at = Column(DateTime, nullable=True)

    source = Column(String, default="manual")  # "manual" | "webhook:github" | etc.
    external_id = Column(String, nullable=True, index=True)  # for webhook dedup

    created_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", back_populates="tickets")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
