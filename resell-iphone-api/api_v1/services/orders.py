from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy import select, func

from core.db.tables import Order, Item, User
from core.models.orders import OrderModel, OrdersModel, OrderCreateModel, OrderUpdateModel
from database import db


async def create_order(order_data: OrderCreateModel) -> OrderModel:
    """
    Создать новый заказ.
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Проверяем существование товара
        item_query = select(Item).where(Item.id == order_data.item_id)
        item_result = await session.execute(item_query)
        item = item_result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
            
        # Проверяем существование покупателя
        buyer_query = select(User).where(User.id == order_data.buyer_id)
        buyer_result = await session.execute(buyer_query)
        buyer = buyer_result.scalar_one_or_none()
        
        if not buyer:
            raise HTTPException(status_code=404, detail="Buyer not found")
            
        # Проверяем существование продавца
        seller_query = select(User).where(User.id == order_data.seller_id)
        seller_result = await session.execute(seller_query)
        seller = seller_result.scalar_one_or_none()
        
        if not seller:
            raise HTTPException(status_code=404, detail="Seller not found")
            
        # Создаем заказ
        order = Order(**order_data.dict())
        session.add(order)
        await session.commit()
        await session.refresh(order)
        
        return OrderModel.from_orm(order)


async def get_order(order_id: int) -> OrderModel:
    """
    Получить информацию о заказе по его ID.
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(Order).where(Order.id == order_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        return OrderModel.from_orm(order)


async def update_order(order_id: int, order_data: OrderUpdateModel) -> OrderModel:
    """
    Обновить информацию о заказе.
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        query = select(Order).where(Order.id == order_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        # Обновляем только указанные поля
        for field, value in order_data.dict(exclude_unset=True).items():
            setattr(order, field, value)
            
        # Если статус заказа изменен на PAID, обновляем статус товара
        if order_data.status == "PAID":
            item_query = select(Item).where(Item.id == order.item_id)
            item_result = await session.execute(item_query)
            item = item_result.scalar_one_or_none()
            
            if item:
                item.is_sold = True
            
        await session.commit()
        await session.refresh(order)
        
        return OrderModel.from_orm(order)


async def get_user_orders(user_id: int, is_buyer: bool = True) -> list[OrderModel]:
    """
    Получить список заказов пользователя (как покупателя или продавца).
    """
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        if is_buyer:
            query = select(Order).where(Order.buyer_id == user_id)
        else:
            query = select(Order).where(Order.seller_id == user_id)
            
        result = await session.execute(query)
        orders = result.scalars().all()
        
        return [OrderModel.from_orm(order) for order in orders] 