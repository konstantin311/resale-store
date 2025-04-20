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


@router.get("/", response_model=ItemsModel)
async def get_items(
    category: str = Query(None, description="Фильтр по категории"),
    page: int = Query(1, description="Номер страницы для разбиения на страницы"),
    filter_type: str = Query(
        None, description="Тип фильтра (например, цена, дата)"
    ),
    filter_value: str = Query(None, description="Значение для выбранного фильтра"),
):
    """
    Получить список товаров с возможностью фильтрации и разбиения на страницы.

    Этот эндпоинт позволяет получить список товаров. Можно отфильтровать товары по категории,
    применить дополнительные фильтры и разбить результаты на страницы.

    Аргументы:
        category (str, необязательный): Фильтр по категории. По умолчанию None.
        page (int, необязательный): Номер страницы для разбиения на страницы. По умолчанию 1.
        filter_type (str, необязательный): Тип фильтра (например, цена, дата). По умолчанию None.
        filter_value (str, необязательный): Значение для выбранного фильтра. По умолчанию None.

    Возвращает:
        ItemsModel: Модель со списком товаров, информацией о разбиении на страницы и индикатором следующей страницы. Если товары не найдены — возвращает пустой список.

    Ошибки:
        500: Внутренняя ошибка сервера при получении данных.
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


@router.get("/search", response_model=ItemsModel)
async def search_items(
    query: str = Query(..., description="Строка поиска"),
    page: int = Query(1, description="Номер страницы для разбиения на страницы"),
):
    """
    Поиск товаров по строке запроса.

    Этот эндпоинт позволяет выполнить поиск товаров по строке запроса. Результаты разбиваются на страницы.

    Аргументы:
        query (str): Строка поиска.
        page (int, необязательный): Номер страницы для разбиения на страницы. По умолчанию 1.

    Возвращает:
        ItemsModel: Модель со списком найденных товаров, информацией о разбиении на страницы и индикатором следующей страницы.

    Ошибки:
        400: Если строка поиска не указана.
        404: Если по запросу ничего не найдено.
        500: Внутренняя ошибка сервера при выполнении поиска.
    """
    result = await items.get_search_results(search_query=query, page=page)
    return result


@router.get("/{item_id}", response_model=ItemExtendedModel)
async def get_item(item_id: int):
    """
    Получить информацию о товаре по его ID.

    Этот эндпоинт возвращает подробную информацию о товаре по его идентификатору.

    Аргументы:
        item_id (int): Идентификатор товара.

    Возвращает:
        ItemExtendedModel: Модель с полной информацией о товаре. Если товар не найден — ошибка 404.

    Ошибки:
        404: Товар не найден.
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await items.get_item(item_id)


@router.get("/by_user/{user_id}", response_model=ItemsModel)
async def get_user_items(user_id: int, page: int = Query(1, description="Номер страницы для разбиения на страницы")):
    """
    Получить список товаров пользователя с разбиением на страницы.

    Этот эндпоинт возвращает список товаров, принадлежащих конкретному пользователю. Результаты разбиваются на страницы.

    Аргументы:
        user_id (int): Идентификатор пользователя.
        page (int, необязательный): Номер страницы для разбиения на страницы. По умолчанию 1.

    Возвращает:
        ItemsModel: Модель со списком товаров, информацией о разбиении на страницы и индикатором следующей страницы.

    Ошибки:
        404: Если у пользователя нет товаров.
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await items.get_users_items(user_id, page)


@router.get("/unsold/by_user/{user_id}", response_model=ItemsModel)
async def get_user_unsold_items(
    user_id: int,
    page: int = Query(1, description="Номер страницы для разбиения на страницы")
):
    """
    Получить список непроданных товаров конкретного пользователя.

    Этот эндпоинт возвращает список товаров, которые принадлежат указанному пользователю
    и еще не проданы. Результаты разбиваются на страницы.

    Аргументы:
        user_id (int): Идентификатор пользователя.
        page (int, необязательный): Номер страницы для разбиения на страницы. По умолчанию 1.

    Возвращает:
        ItemsModel: Модель со списком непроданных товаров пользователя, информацией о разбиении 
        на страницы и индикатором следующей страницы.

    Ошибки:
        404: Если у пользователя нет непроданных товаров.
        500: Внутренняя ошибка сервера при получении данных.
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


@router.delete("/{item_id}", response_model=None, status_code=204)
async def delete_item(item_id: int):
    """
    Удалить существующий товар.

    Этот эндпоинт позволяет удалить товар по его идентификатору.

    Аргументы:
        item_id (int): Идентификатор товара.

    Возвращает:
        None: Если товар успешно удалён.

    Ошибки:
        404: Товар не найден.
        500: Внутренняя ошибка сервера при удалении товара.
    """
    await items.delete_item(item_id)


@router.patch("/{item_id}/is_sold", response_model=ItemExtendedModel)
async def update_item_is_sold(item_id: int, is_sold_data: ItemUpdateIsSold):
    """
    Обновляет статус is_sold для товара.
    
    Аргументы:
        item_id (int): ID товара
        is_sold_data (ItemUpdateIsSold): Новый статус is_sold
        
    Возвращает:
        ItemExtendedModel: Обновленный товар
        
    Ошибки:
        404: Товар не найден
    """
    return await items.update_item_is_sold(item_id, is_sold_data)
