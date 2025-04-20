from datetime import timedelta
from typing import List
import os
import uuid

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from core.db.tables import Category, Item, ItemVector, User, Image
from core.models.items import ItemModel, ItemsModel, ItemExtendedModel, ItemCreateModel, ItemUpdateIsSold
from database import db
from config import settings


async def get_category_id(category: str) -> int:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(Category).where(Category.name == category)
        result = await session.execute(query)
        category = result.scalars().first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category.id


async def get_item(item_id: int) -> ItemExtendedModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = (
            select(Item, Category.name, User.username)
            .join(Category)
            .join(User)
            .where(Item.id == item_id)
            .where(Item.date >= func.now() - timedelta(days=7))
        )
        result = await session.execute(query)
        try:
            item, category_name, username = result.first()
        except TypeError:
            raise HTTPException(status_code=404, detail="Item not found")
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return ItemExtendedModel(
            id=item.id,
            name=item.name,
            image=item.image,
            date=item.date,
            price=item.price,
            currency=item.currency,
            category=category_name,
            contact=item.contact,
            description=item.description,
            user_id=item.user_id,
            username=username,
        )


async def get_items(
    page: int = 1,
    category: str = None,
    ids: List[int] = None,
    filter_type: str = None,
    filter_value: str = None,
) -> ItemsModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        limit = settings.pagination_limit
        next_page = False
        offset = (page - 1) * limit
        query = (
            select(Item, Category.name, User.username)
            .join(Category)
            .join(User)
            .where(Item.date >= func.now() - timedelta(days=7))
            .limit(limit + 1)
            .offset(offset)
        )
        if category:
            category_id = await get_category_id(category)
            query = query.where(Item.category_id == category_id)
        elif ids:
            query = query.where(Item.id.in_(ids))
        if filter_type and filter_value:
            try:
                attr = getattr(Item, filter_type)
            except AttributeError:
                raise HTTPException(
                    status_code=400, detail="Invalid filter type provided"
                )
            else:
                if filter_value == "asc":
                    query = query.order_by(attr.asc())
                elif filter_value == "desc":
                    query = query.order_by(attr.desc())
        else:
            query = query.order_by(Item.date.desc())

        result = await session.execute(query)
        items = result.all()

        if not items:
            return ItemsModel(page=page, next_page=next_page, items=[])
        elif len(items) > limit:
            items = items[:-1]
            next_page = True

        return ItemsModel(
            page=page,
            next_page=next_page,
            items=[
                ItemModel(
                    id=item.id,
                    name=item.name,
                    image=item.image,
                    date=item.date,
                    price=item.price,
                    currency=item.currency,
                    category=category_name,
                    contact=item.contact,
                    description=item.description,
                    user_id=item.user_id,
                    username=username,
                    is_sold=item.is_sold,
                )
                for item, category_name, username in items
            ],
        )


async def get_search_results(search_query: str, page: int) -> ItemsModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        ts_query = func.plainto_tsquery("russian", search_query)
        rank = func.ts_rank(ItemVector.vector, ts_query).label("rank")

        query = (
            select(Item.id)
            .join(ItemVector, Item.id == ItemVector.product_id)
            .where(ItemVector.vector.op("@@")(ts_query))
            .order_by(rank.desc())
        )

        result = await session.execute(query)
        product_ids = [id[0] for id in result.fetchall()]
        if not product_ids:
            raise HTTPException(status_code=404, detail="Products not found")

        products = await get_items(ids=product_ids, page=page)

        return products


async def save_image_file(file, upload_dir: str = "static/uploads") -> str:
    # Create uploads directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    return file_path


async def create_item(data: ItemCreateModel, user_id: int):
    async with db.sessionmaker() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user_instance = user.scalars().first()
        if not user_instance:
            raise HTTPException(status_code=404, detail="User not found")

        data_dict = data.__dict__
        image_file = data_dict.pop("image", None)

        data_dict["date"] = func.now()
        if "category" in data_dict:
            category_name = data_dict.pop("category")
            category = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            category_instance = category.scalars().first()
            if not category_instance:
                raise HTTPException(status_code=404, detail="Category not found")
            data_dict["category"] = category_instance

        # Create item without image first
        item = Item(**data_dict, user_id=user_id, image="")
        session.add(item)
        await session.flush()

        # If image was provided, save it and create image record
        if image_file:
            file_path = await save_image_file(image_file)
            image = Image(file_path=file_path, item_id=item.id)
            session.add(image)
            item.image = file_path

        # Create search vector
        item_vector = ItemVector(
            product_id=item.id,
            vector=func.to_tsvector(data_dict["name"] + " " + data_dict["description"]),
        )
        session.add(item_vector)
        await session.commit()
        return item


async def get_users_items(user_id: int, page: int) -> ItemsModel:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        limit = settings.pagination_limit
        next_page = False
        offset = (page - 1) * limit
        query = (
            select(Item, Category.name, User.username)
            .join(Category)
            .join(User)
            .where(Item.user_id == user_id)
            .where(Item.date >= func.now() - timedelta(days=7))
            .limit(limit + 1)
            .offset(offset)
        )
        result = await session.execute(query)
        items = result.all()
        if not items:
            raise HTTPException(status_code=404, detail="Items not found")
        elif len(items) > limit:
            next_page = True
            items = items[:limit]

        items = [
            ItemModel(
                id=item.Item.id,
                name=item.Item.name,
                image=item.Item.image,
                date=item.Item.date,
                price=item.Item.price,
                currency=item.Item.currency,
                category=item.name,
                contact=item.Item.contact,
                username=item.username,
                is_sold=item.Item.is_sold,
            )
            for item in items
        ]

        return ItemsModel(page=page, next_page=next_page, items=items)


async def update_item(item_id: int, data: ItemCreateModel):
    async with db.sessionmaker() as session:
        data_dict = data.__dict__
        image_file = data_dict.pop("image", None)

        # Get existing item
        query = select(Item).where(Item.id == item_id)
        result = await session.execute(query)
        item = result.scalars().first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Update category if provided
        if "category" in data_dict:
            category_name = data_dict.pop("category")
            category = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            category_instance = category.scalars().first()
            if not category_instance:
                raise HTTPException(status_code=404, detail="Category not found")
            data_dict["category_id"] = category_instance.id

        # Update other fields
        for key, value in data_dict.items():
            if value is not None:  # Only update if value is provided
                setattr(item, key, value)

        # Handle image update
        if image_file:
            # Save new image
            file_path = await save_image_file(image_file)
            
            # Create new image record
            image = Image(file_path=file_path, item_id=item_id)
            session.add(image)
            
            # Update item's main image
            item.image = file_path

        # Update search vector
        vector_query = select(ItemVector).where(ItemVector.product_id == item_id)
        vector_result = await session.execute(vector_query)
        item_vector = vector_result.scalars().first()
        
        if item_vector:
            item_vector.vector = func.to_tsvector(
                data_dict.get("name", item.name) + " " + data_dict.get("description", item.description)
            )
        else:
            item_vector = ItemVector(
                product_id=item_id,
                vector=func.to_tsvector(
                    data_dict.get("name", item.name) + " " + data_dict.get("description", item.description)
                ),
            )
            session.add(item_vector)

        await session.commit()
        return


async def delete_item(item_id: int):
    async with db.sessionmaker() as session:
        # Получаем объявление вместе с изображениями
        query = select(Item).options(selectinload(Item.images)).where(Item.id == item_id)
        result = await session.execute(query)
        item = result.scalars().first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Удаляем вектор поиска
        vector_query = select(ItemVector).where(ItemVector.product_id == item_id)
        vector_result = await session.execute(vector_query)
        item_vector = vector_result.scalars().first()
        if item_vector:
            await session.delete(item_vector)

        # Удаляем изображения
        for image in item.images:
            # Здесь можно добавить удаление файла с диска, если нужно
            await session.delete(image)

        # Удаляем само объявление
        await session.delete(item)
        await session.commit()
        return


async def get_unsold_items(
    page: int = 1,
    category: str = None,
    filter_type: str = None,
    filter_value: str = None,
) -> ItemsModel:
    """
    Получить список непроданных товаров с возможностью фильтрации и разбиения на страницы.
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        limit = settings.pagination_limit
        next_page = False
        offset = (page - 1) * limit
        query = (
            select(Item, Category.name, User.username)
            .join(Category)
            .join(User)
            .where(Item.is_sold == False)
            .where(Item.date >= func.now() - timedelta(days=7))
            .limit(limit + 1)
            .offset(offset)
        )
        
        if category:
            category_id = await get_category_id(category)
            query = query.where(Item.category_id == category_id)
            
        if filter_type and filter_value:
            try:
                attr = getattr(Item, filter_type)
            except AttributeError:
                raise HTTPException(
                    status_code=400, detail="Invalid filter type provided"
                )
            else:
                if filter_value == "asc":
                    query = query.order_by(attr.asc())
                elif filter_value == "desc":
                    query = query.order_by(attr.desc())
        else:
            query = query.order_by(Item.date.desc())

        result = await session.execute(query)
        items = result.all()

        if not items:
            return ItemsModel(page=page, next_page=next_page, items=[])
        elif len(items) > limit:
            items = items[:-1]
            next_page = True

        return ItemsModel(
            page=page,
            next_page=next_page,
            items=[
                ItemModel(
                    id=item.id,
                    name=item.name,
                    image=item.image,
                    date=item.date,
                    price=item.price,
                    currency=item.currency,
                    category=category_name,
                    contact=item.contact,
                    description=item.description,
                    user_id=item.user_id,
                    username=username,
                    is_sold=item.is_sold,
                )
                for item, category_name, username in items
            ],
        )


async def get_users_unsold_items(user_id: int, page: int) -> ItemsModel:
    """
    Получить список непроданных товаров конкретного пользователя.
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        limit = settings.pagination_limit
        next_page = False
        offset = (page - 1) * limit
        query = (
            select(Item, Category.name, User.username)
            .join(Category)
            .join(User)
            .where(Item.user_id == user_id)
            .where(Item.is_sold == False)
            .where(Item.date >= func.now() - timedelta(days=7))
            .limit(limit + 1)
            .offset(offset)
        )
        result = await session.execute(query)
        items = result.all()
        if not items:
            raise HTTPException(status_code=404, detail="Items not found")
        elif len(items) > limit:
            next_page = True
            items = items[:limit]

        items = [
            ItemModel(
                id=item.Item.id,
                name=item.Item.name,
                image=item.Item.image,
                date=item.Item.date,
                price=item.Item.price,
                currency=item.Item.currency,
                category=item.name,
                contact=item.Item.contact,
                username=item.username,
                is_sold=item.Item.is_sold,
            )
            for item in items
        ]

        return ItemsModel(page=page, next_page=next_page, items=items)


async def update_item_is_sold(item_id: int, is_sold_data: ItemUpdateIsSold) -> ItemModel:
    """
    Обновляет статус is_sold для товара.
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(Item).where(Item.id == item_id)
        result = await session.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Товар не найден")
            
        item.is_sold = is_sold_data.is_sold
        await session.commit()
        await session.refresh(item)
        
        # Получаем категорию и имя пользователя
        category_query = select(Category.name).where(Category.id == item.category_id)
        category_result = await session.execute(category_query)
        category_name = category_result.scalar_one()
        
        user_query = select(User.username).where(User.id == item.user_id)
        user_result = await session.execute(user_query)
        username = user_result.scalar_one()
        
        return ItemModel(
            id=item.id,
            name=item.name,
            image=item.image,
            date=item.date,
            price=item.price,
            currency=item.currency,
            category=category_name,
            contact=item.contact,
            description=item.description,
            user_id=item.user_id,
            username=username,
            is_sold=item.is_sold,
        )
