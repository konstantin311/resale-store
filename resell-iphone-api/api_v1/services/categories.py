from typing import List

from fastapi import HTTPException
from sqlalchemy import select, delete, func

from core.db.tables import Category, Item
from core.models.categories import CategoryModel, CategoriesModel, CategoryCreateModel, CategoryUpdateModel
from database import db


async def get_categories() -> List[CategoryModel]:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(Category)
        result = await session.execute(query)
        categories = result.scalars().all()

    if not categories:
        return []

    return [CategoryModel(id=category.id, name=category.name) for category in categories]


async def create_category(category_data: CategoryCreateModel) -> CategoryModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Check if category with same name already exists
        existing_category = await session.execute(
            select(Category).where(Category.name == category_data.name)
        )
        if existing_category.scalars().first():
            raise HTTPException(status_code=400, detail="Category with this name already exists")

        category = Category(name=category_data.name)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return CategoryModel(id=category.id, name=category.name)


async def update_category(category_id: int, category_data: CategoryUpdateModel) -> CategoryModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        category = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = category.scalars().first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check if new name is already taken
        if category_data.name != category.name:
            existing_category = await session.execute(
                select(Category).where(Category.name == category_data.name)
            )
            if existing_category.scalars().first():
                raise HTTPException(status_code=400, detail="Category with this name already exists")

        category.name = category_data.name
        await session.commit()
        await session.refresh(category)
        return CategoryModel(id=category.id, name=category.name)


async def delete_category(category_id: int) -> None:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Check if category exists
        category = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = category.scalars().first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Check if there are any items associated with this category
        items_count = await session.execute(
            select(func.count()).select_from(Item).where(Item.category_id == category_id)
        )
        if items_count.scalar() > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete category: there are items associated with it"
            )

        await session.execute(delete(Category).where(Category.id == category_id))
        await session.commit()
