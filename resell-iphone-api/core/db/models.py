"""import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    BOOLEAN,
    TIMESTAMP,
    TEXT,
    UUID,
    Float,
    func,
    Text,
    ForeignKey,
    Integer,
)
from sqlalchemy.dialects.postgresql import BIGINT, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    username = Column(TEXT, nullable=False)
    password = Column(TEXT, nullable=False)
    email = Column(TEXT, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    is_admin = Column(BOOLEAN, default=False, nullable=False)
    telegram_id = Column(BIGINT, nullable=True)


class Phone(Base):
    __tablename__ = "phones"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.id"), nullable=False)
    name: Mapped[Text] = Column(Text, nullable=False)
    model: Mapped[Text] = Column(Text, nullable=False)
    price: Mapped[Float] = Column(Float, nullable=False)
    description: Mapped[Text] = Column(Text, nullable=False)
    parameters: Mapped[JSONB] = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    is_active = Column(BOOLEAN, default=True, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, nullable=False
    )
    user_id = Column(BIGINT)
    phone_id = Column(BIGINT)
    payment_link = Column(Text)
    is_paid = Column(BOOLEAN, default=False)
    quantity = Column(Integer)
"""