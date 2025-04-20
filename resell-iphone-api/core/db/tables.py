from sqlalchemy import Column, Integer, Text, TIMESTAMP, Float, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import TSVECTOR, BIGINT, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)

    items = relationship("Item", back_populates="category")


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    image = Column(Text, nullable=False)
    date = Column(TIMESTAMP, nullable=False)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    contact = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    user_id = Column(BIGINT, ForeignKey("users.id"), nullable=False)
    currency = Column(Text, nullable=False)
    is_sold = Column(Boolean, nullable=False, default=False)

    category = relationship("Category", back_populates="items")
    vector = relationship("ItemVector", back_populates="item", uselist=False)
    user = relationship("User", back_populates="items")
    images = relationship("Image", back_populates="item")
    orders = relationship("Order", back_populates="item")


class ItemVector(Base):
    __tablename__ = "item_vectors"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    vector = Column(TSVECTOR, nullable=False)
    item = relationship("Item", back_populates="vector")


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="role")


class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    
    item = relationship("Item", back_populates="images")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(BIGINT, ForeignKey("users.id"), nullable=False)
    seller_id = Column(BIGINT, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    buyer_telegram_id = Column(BIGINT, nullable=False)
    seller_telegram_id = Column(BIGINT, nullable=False)
    buyer_phone = Column(Text, nullable=False)
    seller_phone = Column(Text, nullable=False)
    delivery_address = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    total = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="buyer_orders")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_orders")
    item = relationship("Item", back_populates="orders")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BIGINT, unique=True)
    username = Column(Text)
    name = Column(Text, nullable=False)
    contact = Column(Text)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    role = relationship("Role", back_populates="users")
    items = relationship("Item", back_populates="user")
    buyer_orders = relationship("Order", foreign_keys=[Order.buyer_id], back_populates="buyer")
    seller_orders = relationship("Order", foreign_keys=[Order.seller_id], back_populates="seller")
