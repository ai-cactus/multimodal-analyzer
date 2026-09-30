"""
Base model utilities
"""
from datetime import datetime
from sqlalchemy import Column, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
import uuid


def generate_uuid():
    """Generate UUID for primary keys"""
    return uuid.uuid4()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UUIDMixin:
    """Mixin to add UUID primary key"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
