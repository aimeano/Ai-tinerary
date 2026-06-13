from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
import uuid
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    


class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)

    title = Column(String, nullable=False)
    profile = Column(JSON, nullable=False)

    raw_itinerary = Column(JSON, nullable=False)
    itinerary = Column(JSON, nullable=False)
    geocoded = Column(JSON, nullable=True)
    enrichment_cache = Column(JSON, nullable=True)
    itinerary_version = Column(Integer, nullable=False, default=1)
    clusters = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(
        String,
        primary_key=True,
        default=lambda: f"msg_{uuid.uuid4().hex[:8]}",
    )

    trip_id = Column(
        String,
        ForeignKey("trips.trip_id", ondelete="CASCADE"),
        nullable=False,
    )

    role = Column(String, nullable=False)
    content = Column(JSONB, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )