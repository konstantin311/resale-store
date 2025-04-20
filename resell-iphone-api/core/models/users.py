from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class UserRole(str, Enum):
    SELLER = "seller"
    BUYER = "buyer"
    ADMIN = "admin"


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleResponseModel(RoleBase):
    id: int
    created_at: str
    updated_at: str


class UserBase(BaseModel):
    username: str | None
    name: str
    contact: str | None
    telegram_id: int | None
    role_id: int


class UserResponseModel(UserBase):
    id: int
    created_at: str
    updated_at: str
    role: RoleResponseModel


class UserModel(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime


class UsersModel(BaseModel):
    users: List[UserResponseModel]
    total: int


class UserCreateModel(UserBase):
    pass


class UserUpdateModel(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    contact: Optional[str] = None
    telegram_id: Optional[int] = None
    role_id: Optional[int] = None
