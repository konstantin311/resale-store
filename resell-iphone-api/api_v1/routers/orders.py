from fastapi import APIRouter, Query
from core.models.orders import OrderModel, OrderCreateModel, OrderUpdateModel
from api_v1.services import orders

router = APIRouter(tags=["Заказы"])


@router.post("/", response_model=OrderModel)
async def create_order(order_data: OrderCreateModel):
    """
    Создать новый заказ.

    Этот эндпоинт позволяет создать новый заказ с указанием всех необходимых данных.

    Аргументы:
        order_data (OrderCreateModel): Данные для создания заказа.

    Возвращает:
        OrderModel: Созданный заказ.

    Ошибки:
        404: Если товар, покупатель или продавец не найдены.
        500: Внутренняя ошибка сервера при создании заказа.
    """
    return await orders.create_order(order_data)


@router.get("/{order_id}", response_model=OrderModel)
async def get_order(order_id: int):
    """
    Получить информацию о заказе.

    Этот эндпоинт возвращает информацию о конкретном заказе по его ID.

    Аргументы:
        order_id (int): ID заказа.

    Возвращает:
        OrderModel: Информация о заказе.

    Ошибки:
        404: Заказ не найден.
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await orders.get_order(order_id)


@router.patch("/{order_id}", response_model=OrderModel)
async def update_order(order_id: int, order_data: OrderUpdateModel):
    """
    Обновить информацию о заказе.

    Этот эндпоинт позволяет обновить информацию о существующем заказе.

    Аргументы:
        order_id (int): ID заказа.
        order_data (OrderUpdateModel): Новые данные заказа.

    Возвращает:
        OrderModel: Обновленная информация о заказе.

    Ошибки:
        404: Заказ не найден.
        500: Внутренняя ошибка сервера при обновлении данных.
    """
    return await orders.update_order(order_id, order_data)


@router.get("/user/{user_id}", response_model=list[OrderModel])
async def get_user_orders(
    user_id: int,
    is_buyer: bool = Query(True, description="Получить заказы как покупателя (True) или продавца (False)")
):
    """
    Получить список заказов пользователя.

    Этот эндпоинт возвращает список заказов пользователя, где он является либо покупателем, либо продавцом.

    Аргументы:
        user_id (int): ID пользователя.
        is_buyer (bool): Флаг, указывающий, является ли пользователь покупателем (True) или продавцом (False).

    Возвращает:
        list[OrderModel]: Список заказов пользователя.

    Ошибки:
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await orders.get_user_orders(user_id, is_buyer) 