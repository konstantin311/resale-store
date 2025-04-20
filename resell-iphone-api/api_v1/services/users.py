from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.db.tables import User, Role
from core.models.users import UserModel, UsersModel, UserCreateModel, UserUpdateModel, UserBase, UserResponseModel, RoleBase, RoleResponseModel
from database import db


async def create_user(data: UserBase) -> UserResponseModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Проверяем, существует ли пользователь с таким telegram_id
        query = select(User).where(User.telegram_id == data.telegram_id)
        result = await session.execute(query)
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this telegram_id already exists"
            )
        
        # Проверяем существование роли
        role_query = select(Role).where(Role.id == data.role_id)
        role_result = await session.execute(role_query)
        role = role_result.scalars().first()
        if not role:
            raise HTTPException(
                status_code=400,
                detail="Role not found"
            )
            
        user = User(**data.__dict__)
        session.add(user)
        await session.commit()
        
        # Загружаем пользователя вместе с ролью
        query = select(User).options(selectinload(User.role)).where(User.id == user.id)
        result = await session.execute(query)
        user = result.scalars().first()
        
        return UserResponseModel(
            id=user.id,
            username=user.username,
            name=user.name,
            contact=user.contact,
            telegram_id=user.telegram_id,
            role_id=user.role_id,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            role=RoleResponseModel(
                id=user.role.id,
                name=user.role.name,
                description=user.role.description,
                created_at=user.role.created_at.isoformat(),
                updated_at=user.role.updated_at.isoformat()
            )
        )


async def get_user(user_id: int) -> UserResponseModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Загружаем пользователя вместе с ролью в одном запросе
        query = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return UserResponseModel(
            id=user.id,
            username=user.username,
            name=user.name,
            contact=user.contact,
            telegram_id=user.telegram_id,
            role_id=user.role_id,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            role=RoleResponseModel(
                id=user.role.id,
                name=user.role.name,
                description=user.role.description,
                created_at=user.role.created_at.isoformat(),
                updated_at=user.role.updated_at.isoformat()
            )
        )


async def get_user_id_by_telegram_id(telegram_id: int) -> int:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.id


async def check_user_exists(telegram_id: int) -> bool:
    """
    Проверить существование пользователя по Telegram ID.

    Аргументы:
        telegram_id (int): Telegram ID пользователя.

    Возвращает:
        bool: True, если пользователь существует, False в противном случае.
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalars().first()
        return user is not None


async def create_role(data: RoleBase) -> RoleResponseModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Проверяем, существует ли роль с таким именем
        query = select(Role).where(Role.name == data.name)
        result = await session.execute(query)
        existing_role = result.scalars().first()
        if existing_role:
            raise HTTPException(
                status_code=400,
                detail="Role with this name already exists"
            )
            
        role = Role(**data.__dict__)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return RoleResponseModel(
            id=role.id,
            name=role.name,
            description=role.description,
            created_at=role.created_at.isoformat(),
            updated_at=role.updated_at.isoformat()
        )


async def get_roles() -> list[RoleResponseModel]:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(Role)
        result = await session.execute(query)
        roles = result.scalars().all()
        return [
            RoleResponseModel(
                id=role.id,
                name=role.name,
                description=role.description,
                created_at=role.created_at.isoformat(),
                updated_at=role.updated_at.isoformat()
            )
            for role in roles
        ]


async def update_user_role(user_id: int, role_id: int) -> UserResponseModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Проверяем существование пользователя
        user_query = select(User).where(User.id == user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Проверяем существование роли
        role_query = select(Role).where(Role.id == role_id)
        role_result = await session.execute(role_query)
        role = role_result.scalars().first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
            
        # Обновляем роль пользователя
        user.role_id = role_id
        await session.commit()
        
        # Загружаем пользователя вместе с ролью
        query = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalars().first()
        
        return UserResponseModel(
            id=user.id,
            username=user.username,
            name=user.name,
            contact=user.contact,
            telegram_id=user.telegram_id,
            role_id=user.role_id,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            role=RoleResponseModel(
                id=user.role.id,
                name=user.role.name,
                description=user.role.description,
                created_at=user.role.created_at.isoformat(),
                updated_at=user.role.updated_at.isoformat()
            )
        )
