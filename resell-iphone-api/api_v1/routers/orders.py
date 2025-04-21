from fastapi import APIRouter, Query
from core.models.orders import OrderModel, OrderCreateModel, OrderUpdateModel
from api_v1.services import orders

router = APIRouter(tags=["Заказы"])


@router.post(
    "/",
    response_model=OrderModel,
    summary="Создать новый заказ",
    description="""
    Создает новый заказ в системе.
    
    - Проверяет существование товара, покупателя и продавца
    - Автоматически устанавливает дату создания
    - Создает связь между товаром и участниками сделки
    """,
    responses={
        200: {
            "description": "Заказ успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "item_id": 1,
                        "buyer_id": 2,
                        "seller_id": 3,
                        "status": "created",
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Товар, покупатель или продавец не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Item, buyer or seller not found"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    }
)
async def create_order(order_data: OrderCreateModel):
    """
    Создает новый заказ в системе.
    
    Args:
        order_data (OrderCreateModel): Данные для создания заказа
        
    Returns:
        OrderModel: Созданный заказ с полной информацией
        
    Raises:
        HTTPException: 404 если товар, покупатель или продавец не найдены
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await orders.create_order(order_data)


@router.get(
    "/{order_id}",
    response_model=OrderModel,
    summary="Получить информацию о заказе",
    description="""
    Получает полную информацию о заказе по его ID.
    
    - Возвращает все данные заказа
    - Включает информацию о товаре, покупателе и продавце
    - Возвращает текущий статус заказа
    """,
    responses={
        200: {
            "description": "Информация о заказе успешно получена",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "item_id": 1,
                        "buyer_id": 2,
                        "seller_id": 3,
                        "status": "created",
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Заказ не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Order not found"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    }
)
async def get_order(order_id: int):
    """
    Получает информацию о заказе по его ID.
    
    Args:
        order_id (int): ID заказа
        
    Returns:
        OrderModel: Полная информация о заказе
        
    Raises:
        HTTPException: 404 если заказ не найден
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await orders.get_order(order_id)


@router.patch(
    "/{order_id}",
    response_model=OrderModel,
    summary="Обновить информацию о заказе",
    description="""
    Обновляет информацию о существующем заказе.
    
    - Позволяет изменить статус заказа
    - Обновляет дату последнего изменения
    - Проверяет существование заказа
    """,
    responses={
        200: {
            "description": "Информация о заказе успешно обновлена",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "item_id": 1,
                        "buyer_id": 2,
                        "seller_id": 3,
                        "status": "completed",
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T13:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Заказ не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Order not found"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    }
)
async def update_order(order_id: int, order_data: OrderUpdateModel):
    """
    Обновляет информацию о заказе.
    
    Args:
        order_id (int): ID заказа
        order_data (OrderUpdateModel): Новые данные заказа
        
    Returns:
        OrderModel: Обновленная информация о заказе
        
    Raises:
        HTTPException: 404 если заказ не найден
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await orders.update_order(order_id, order_data)


@router.get(
    "/user/{user_id}",
    response_model=list[OrderModel],
    summary="Получить заказы пользователя",
    description="""
    Получает список заказов пользователя.
    
    - Можно получить заказы как покупателя или продавца
    - Возвращает полную информацию о каждом заказе
    - Включает статус и даты создания/обновления
    """,
    responses={
        200: {
            "description": "Список заказов пользователя успешно получен",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "item_id": 1,
                            "buyer_id": 2,
                            "seller_id": 3,
                            "status": "created",
                            "created_at": "2024-04-15T12:00:00",
                            "updated_at": "2024-04-15T12:00:00"
                        },
                        {
                            "id": 2,
                            "item_id": 2,
                            "buyer_id": 2,
                            "seller_id": 4,
                            "status": "completed",
                            "created_at": "2024-04-15T11:00:00",
                            "updated_at": "2024-04-15T13:00:00"
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    }
)
async def get_user_orders(
    user_id: int,
    is_buyer: bool = Query(True, description="Получить заказы как покупателя (True) или продавца (False)")
):
    """
    Получает список заказов пользователя.
    
    Args:
        user_id (int): ID пользователя
        is_buyer (bool, optional): Флаг, указывающий, является ли пользователь покупателем
        
    Returns:
        list[OrderModel]: Список заказов пользователя
        
    Raises:
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await orders.get_user_orders(user_id, is_buyer) 