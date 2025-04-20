from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"


class Order(BaseModel):
    id: int | None = None
    buyer_id: int
    seller_id: int
    item_id: int
    buyer_telegram_id: int
    seller_telegram_id: int
    buyer_phone: str
    seller_phone: str
    delivery_address: str
    status: OrderStatus
    total: float
    created_at: datetime | None = None
    updated_at: datetime | None = None 