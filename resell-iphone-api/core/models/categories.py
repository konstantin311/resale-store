from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CategoryBase(BaseModel):
    name: str


class CategoryModel(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CategoriesModel(BaseModel):
    categories: List[CategoryModel]
    total: int


class CategoryCreateModel(CategoryBase):
    pass


class CategoryUpdateModel(BaseModel):
    name: Optional[str] = None
