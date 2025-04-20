from pydantic import BaseModel
from typing import Optional


class ImageBase(BaseModel):
    class Config:
        from_attributes = True

    file_path: str


class ImageModel(ImageBase):
    id: int
    item_id: int
    created_at: str


class ImageCreateModel(BaseModel):
    file_path: str
    item_id: int 