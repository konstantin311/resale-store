from fastapi import APIRouter, Query, Form, File, UploadFile
from fastapi.params import Query
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from typing import List, Optional

from api_v1.services import items, users
from core.models.items import ItemsModel, ItemExtendedModel, ItemCreateModel, ItemUpdateIsSold
from core.models.users import UserBase
from database import db
from core.db.tables import Item
from config import DatabaseMarker

router = APIRouter(tags=["Товары"])


@router.get(
    "/",
    response_model=ItemsModel,
    summary="Получить список товаров",
    description="""
    Получает список товаров с возможностью фильтрации и разбиения на страницы.
    
    - Поддерживает фильтрацию по категории
    - Поддерживает сортировку по различным параметрам (цена, дата)
    - Реализовано разбиение на страницы
    - Возвращает только актуальные объявления (не старше 7 дней)
    """,
    responses={
        200: {
            "description": "Список товаров успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "next_page": True,
                        "items": [
                            {
                                "id": 1,
                                "name": "iPhone 13 Pro",
                                "image": "static/uploads/image.jpg",
                                "date": "2024-04-15T12:00:00",
                                "price": 999.99,
                                "currency": "USD",
                                "category": "Смартфоны",
                                "contact": "@username",
                                "description": "Отличное состояние, гарантия",
                                "user_id": 1,
                                "username": "user123",
                                "is_sold": False
                            }
                        ]
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
async def get_items(
    category: str = Query(None, description="Фильтр по категории"),
    page: int = Query(1, description="Номер страницы для разбиения на страницы"),
    filter_type: str = Query(
        None, description="Тип фильтра (например, price, date)"
    ),
    filter_value: str = Query(None, description="Значение фильтра (asc или desc)"),
):
    """
    Получить список товаров с возможностью фильтрации и разбиения на страницы.
    
    Args:
        category (str, optional): Фильтр по категории товаров
        page (int, optional): Номер страницы для пагинации
        filter_type (str, optional): Поле для сортировки (price, date)
        filter_value (str, optional): Направление сортировки (asc, desc)
        
    Returns:
        ItemsModel: Модель со списком товаров и информацией о пагинации
        
    Raises:
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await items.get_items(
        category=category,
        page=page,
        filter_type=filter_type,
        filter_value=filter_value,
    )


@router.get("/unsold", response_model=ItemsModel)
async def get_unsold_items(
    category: str = Query(None, description="Фильтр по категории"),
    page: int = Query(1, description="Номер страницы для разбиения на страницы"),
    filter_type: str = Query(
        None, description="Тип фильтра (например, цена, дата)"
    ),
    filter_value: str = Query(None, description="Значение для выбранного фильтра"),
):
    """
    Получить список непроданных товаров с возможностью фильтрации и разбиения на страницы.

    Этот эндпоинт позволяет получить список товаров, которые еще не проданы. 
    Можно отфильтровать товары по категории, применить дополнительные фильтры 
    и разбить результаты на страницы.

    Аргументы:
        category (str, необязательный): Фильтр по категории. По умолчанию None.
        page (int, необязательный): Номер страницы для разбиения на страницы. По умолчанию 1.
        filter_type (str, необязательный): Тип фильтра (например, цена, дата). По умолчанию None.
        filter_value (str, необязательный): Значение для выбранного фильтра. По умолчанию None.

    Возвращает:
        ItemsModel: Модель со списком непроданных товаров, информацией о разбиении на страницы 
        и индикатором следующей страницы. Если товары не найдены — возвращает пустой список.

    Ошибки:
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await items.get_unsold_items(
        category=category,
        page=page,
        filter_type=filter_type,
        filter_value=filter_value,
    )


@router.get(
    "/search",
    response_model=ItemsModel,
    summary="Поиск товаров",
    description="""
    Поиск товаров по строке запроса с возможностью разбиения на страницы.
    
    - Поддерживает полнотекстовый поиск по названию и описанию
    - Реализовано разбиение на страницы
    - Возвращает только актуальные объявления (не старше 7 дней)
    - Результаты сортируются по релевантности
    """,
    responses={
        200: {
            "description": "Результаты поиска успешно получены",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "next_page": True,
                        "items": [
                            {
                                "id": 1,
                                "name": "iPhone 13 Pro",
                                "image": "static/uploads/image.jpg",
                                "date": "2024-04-15T12:00:00",
                                "price": 999.99,
                                "currency": "USD",
                                "category": "Смартфоны",
                                "contact": "@username",
                                "description": "Отличное состояние, гарантия",
                                "user_id": 1,
                                "username": "user123",
                                "is_sold": False
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Не указана строка поиска",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Search query is required"
                    }
                }
            }
        },
        404: {
            "description": "Товары не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No items found"
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
async def search_items(
    query: str = Query(..., description="Строка поиска"),
    page: int = Query(1, description="Номер страницы для разбиения на страницы"),
):
    """
    Поиск товаров по строке запроса.
    
    Args:
        query (str): Строка поиска
        page (int, optional): Номер страницы для пагинации
        
    Returns:
        ItemsModel: Модель со списком найденных товаров и информацией о пагинации
        
    Raises:
        HTTPException: 400 если строка поиска не указана
        HTTPException: 404 если товары не найдены
        HTTPException: 500 при внутренней ошибке сервера
    """
    result = await items.get_search_results(search_query=query, page=page)
    return result


@router.get(
    "/{item_id}",
    response_model=ItemExtendedModel,
    summary="Получить товар по ID",
    description="""
    Получает подробную информацию о товаре по его идентификатору.
    
    - Возвращает полную информацию о товаре
    - Включает данные о пользователе-продавце
    - Возвращает только актуальные объявления (не старше 7 дней)
    """,
    responses={
        200: {
            "description": "Товар успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "iPhone 13 Pro",
                        "image": "static/uploads/image.jpg",
                        "date": "2024-04-15T12:00:00",
                        "price": 999.99,
                        "currency": "USD",
                        "category": "Смартфоны",
                        "contact": "@username",
                        "description": "Отличное состояние, гарантия",
                        "user_id": 1,
                        "username": "user123",
                        "is_sold": False
                    }
                }
            }
        },
        404: {
            "description": "Товар не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Item not found"
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
async def get_item(item_id: int):
    """
    Получить информацию о товаре по его ID.
    
    Args:
        item_id (int): ID товара
        
    Returns:
        ItemExtendedModel: Модель с полной информацией о товаре
        
    Raises:
        HTTPException: 404 если товар не найден
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await items.get_item(item_id)


@router.get(
    "/by_user/{user_id}",
    response_model=ItemsModel,
    summary="Получить товары пользователя",
    description="""
    Получает список товаров, принадлежащих конкретному пользователю.
    
    - Поддерживает разбиение на страницы
    - Возвращает только актуальные объявления (не старше 7 дней)
    - Включает полную информацию о каждом товаре
    """,
    responses={
        200: {
            "description": "Список товаров пользователя успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "next_page": True,
                        "items": [
                            {
                                "id": 1,
                                "name": "iPhone 13 Pro",
                                "image": "static/uploads/image.jpg",
                                "date": "2024-04-15T12:00:00",
                                "price": 999.99,
                                "currency": "USD",
                                "category": "Смартфоны",
                                "contact": "@username",
                                "description": "Отличное состояние, гарантия",
                                "user_id": 1,
                                "username": "user123",
                                "is_sold": False
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Товары пользователя не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User items not found"
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
async def get_user_items(
    user_id: int,
    page: int = Query(1, description="Номер страницы для разбиения на страницы")
):
    """
    Получить список товаров пользователя.
    
    Args:
        user_id (int): ID пользователя
        page (int, optional): Номер страницы для пагинации
        
    Returns:
        ItemsModel: Модель со списком товаров и информацией о пагинации
        
    Raises:
        HTTPException: 404 если товары пользователя не найдены
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await items.get_users_items(user_id, page)


@router.get(
    "/unsold/by_user/{user_id}",
    response_model=ItemsModel,
    summary="Получить непроданные товары пользователя",
    description="""
    Получает список непроданных товаров, принадлежащих конкретному пользователю.
    
    - Поддерживает разбиение на страницы
    - Возвращает только актуальные объявления (не старше 7 дней)
    - Включает полную информацию о каждом товаре
    - Возвращает только товары со статусом is_sold=False
    """,
    responses={
        200: {
            "description": "Список непроданных товаров пользователя успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "page": 1,
                        "next_page": True,
                        "items": [
                            {
                                "id": 1,
                                "name": "iPhone 13 Pro",
                                "image": "static/uploads/image.jpg",
                                "date": "2024-04-15T12:00:00",
                                "price": 999.99,
                                "currency": "USD",
                                "category": "Смартфоны",
                                "contact": "@username",
                                "description": "Отличное состояние, гарантия",
                                "user_id": 1,
                                "username": "user123",
                                "is_sold": False
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Непроданные товары пользователя не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User unsold items not found"
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
async def get_user_unsold_items(
    user_id: int,
    page: int = Query(1, description="Номер страницы для разбиения на страницы")
):
    """
    Получить список непроданных товаров пользователя.
    
    Args:
        user_id (int): ID пользователя
        page (int, optional): Номер страницы для пагинации
        
    Returns:
        ItemsModel: Модель со списком непроданных товаров и информацией о пагинации
        
    Raises:
        HTTPException: 404 если непроданные товары пользователя не найдены
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await items.get_users_unsold_items(user_id, page)


@router.post(
    "/",
    response_model=None,
    summary="Создать новое объявление",
    description="""
    Создает новое объявление с возможностью загрузки изображения.
    
    - Все поля, кроме изображения, обязательны
    - Категория должна существовать в базе данных
    - Telegram ID пользователя должен быть указан
    - Изображение сохраняется в директории static/uploads
    - Генерируется уникальное имя файла для изображения
    """,
    responses={
        200: {
            "description": "Объявление успешно создано",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Item created successfully"
                    }
                }
            }
        },
        404: {
            "description": "Категория или пользователь не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Category not found"
                    }
                }
            }
        },
        422: {
            "description": "Некорректные данные",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "price"],
                                "msg": "value is not a valid float",
                                "type": "type_error.float"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def create_item(
    name: str = Form(..., description="Название товара"),
    price: float = Form(..., description="Цена товара"),
    currency: str = Form(..., description="Валюта (например, USD, EUR, RUB)"),
    category: str = Form(..., description="Название категории"),
    contact: str = Form(..., description="Контактная информация"),
    description: str = Form(..., description="Подробное описание товара"),
    image: UploadFile = File(None, description="Изображение товара (необязательно)"),
    telegram_id: int = Query(..., description="Telegram ID пользователя, создающего объявление")
):
    """
    Создает новое объявление с возможностью загрузки изображения.
    
    Args:
        name (str): Название товара
        price (float): Цена товара
        currency (str): Валюта
        category (str): Категория товара
        contact (str): Контактная информация
        description (str): Описание товара
        image (UploadFile, optional): Изображение товара
        telegram_id (int): Telegram ID пользователя
        
    Returns:
        None: Если объявление успешно создано
        
    Raises:
        HTTPException: 404 если категория или пользователь не найдены
        HTTPException: 422 если данные некорректны
        HTTPException: 500 при внутренней ошибке сервера
    """
    # Получаем ID пользователя по telegram_id
    user_id = await users.get_user_id_by_telegram_id(telegram_id)
    
    data = ItemCreateModel(
        name=name,
        price=price,
        currency=currency,
        category=category,
        contact=contact,
        description=description,
        image=image
    )
    await items.create_item(data, user_id)


@router.patch(
    "/{item_id}",
    response_model=None,
    status_code=204,
    summary="Обновить существующее объявление",
    description="""
    Обновляет существующее объявление с возможностью загрузки нового изображения.
    
    - Все поля, кроме изображения, необязательны
    - Категория должна существовать в базе данных
    - Изображение сохраняется в директории static/uploads
    - Генерируется уникальное имя файла для изображения
    """,
    responses={
        204: {
            "description": "Объявление успешно обновлено"
        },
        404: {
            "description": "Товар или категория не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Item not found"
                    }
                }
            }
        },
        422: {
            "description": "Некорректные данные",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "price"],
                                "msg": "value is not a valid float",
                                "type": "type_error.float"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def update_item(
    item_id: int,
    name: str = Form(None, description="Название товара"),
    price: float = Form(None, description="Цена товара"),
    currency: str = Form(None, description="Валюта (например, USD, EUR, RUB)"),
    category: str = Form(None, description="Название категории"),
    contact: str = Form(None, description="Контактная информация"),
    description: str = Form(None, description="Подробное описание товара"),
    image: UploadFile = File(None, description="Изображение товара (необязательно)")
):
    """
    Обновляет существующее объявление с возможностью загрузки нового изображения.
    
    Args:
        item_id (int): ID товара для обновления
        name (str, optional): Новое название товара
        price (float, optional): Новая цена товара
        currency (str, optional): Новая валюта
        category (str, optional): Новая категория товара
        contact (str, optional): Новая контактная информация
        description (str, optional): Новое описание товара
        image (UploadFile, optional): Новое изображение товара
        
    Returns:
        None: Если объявление успешно обновлено
        
    Raises:
        HTTPException: 404 если товар или категория не найдены
        HTTPException: 422 если данные некорректны
        HTTPException: 500 при внутренней ошибке сервера
    """
    data = ItemCreateModel(
        name=name,
        price=price,
        currency=currency,
        category=category,
        contact=contact,
        description=description,
        image=image
    )
    await items.update_item(item_id, data)


@router.delete(
    "/{item_id}",
    response_model=None,
    status_code=204,
    summary="Удалить товар",
    description="""
    Удаляет товар по его идентификатору.
    
    - Полностью удаляет товар из базы данных
    - Удаляет связанные изображения
    - Доступно только для владельца товара
    - Возвращает статус 204 при успешном удалении
    """,
    responses={
        204: {
            "description": "Товар успешно удален"
        },
        404: {
            "description": "Товар не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Item not found"
                    }
                }
            }
        },
        403: {
            "description": "Нет прав для удаления",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
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
async def delete_item(item_id: int):
    """
    Удаляет товар по его ID.
    
    Args:
        item_id (int): ID товара для удаления
        
    Returns:
        None: При успешном удалении возвращает статус 204
        
    Raises:
        HTTPException: 404 если товар не найден
        HTTPException: 403 если нет прав для удаления
        HTTPException: 500 при внутренней ошибке сервера
    """
    await items.delete_item(item_id)


@router.patch(
    "/{item_id}/is_sold",
    response_model=ItemExtendedModel,
    summary="Обновить статус продажи товара",
    description="""
    Обновляет статус is_sold для товара.
    
    - Позволяет отметить товар как проданный или непроданный
    - Возвращает обновленную информацию о товаре
    - Доступно только для владельца товара
    """,
    responses={
        200: {
            "description": "Статус товара успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "iPhone 13 Pro",
                        "image": "static/uploads/image.jpg",
                        "date": "2024-04-15T12:00:00",
                        "price": 999.99,
                        "currency": "USD",
                        "category": "Смартфоны",
                        "contact": "@username",
                        "description": "Отличное состояние, гарантия",
                        "user_id": 1,
                        "username": "user123",
                        "is_sold": True
                    }
                }
            }
        },
        404: {
            "description": "Товар не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Item not found"
                    }
                }
            }
        },
        403: {
            "description": "Нет прав для обновления статуса",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
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
async def update_item_is_sold(
    item_id: int,
    is_sold_data: ItemUpdateIsSold
):
    """
    Обновляет статус is_sold для товара.
    
    Args:
        item_id (int): ID товара
        is_sold_data (ItemUpdateIsSold): Новый статус is_sold
        
    Returns:
        ItemExtendedModel: Обновленная информация о товаре
        
    Raises:
        HTTPException: 404 если товар не найден
        HTTPException: 403 если нет прав для обновления
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await items.update_item_is_sold(item_id, is_sold_data)
