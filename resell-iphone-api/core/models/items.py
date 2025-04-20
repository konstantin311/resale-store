from datetime import datetime
from typing import Optional
from fastapi import UploadFile

from pydantic import BaseModel


class ItemBase(BaseModel):
    class Config:
        from_attributes = True

    name: str
    price: float
    currency: str
    category: str
    contact: str
    is_sold: bool = False


class ItemModel(ItemBase):
    id: int
    image: str
    date: datetime
    username: Optional[str] = None


class ItemsModel(BaseModel):
    page: int
    next_page: bool
    items: list[ItemModel]


class ItemExtendedModel(ItemModel):
    description: str
    user_id: int


class ItemCreateModel(ItemBase):
    description: str
    image: Optional[UploadFile] = None


class ItemUpdateIsSold(BaseModel):
    is_sold: bool
