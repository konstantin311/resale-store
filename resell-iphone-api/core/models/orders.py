from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OrderBase(BaseModel):
    class Config:
        from_attributes = True

    buyer_id: int
    seller_id: int
    item_id: int
    buyer_telegram_id: int
    seller_telegram_id: int
    buyer_phone: str
    seller_phone: str
    delivery_address: str
    status: str
    total: float


class OrderModel(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime


class OrdersModel(BaseModel):
    orders: List[OrderModel]
    total: int


class OrderCreateModel(OrderBase):
    pass


class OrderUpdateModel(BaseModel):
    status: Optional[str] = None
    delivery_address: Optional[str] = None 