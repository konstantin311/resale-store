from typing import List

from fastapi import APIRouter

from api_v1.services import categories
from core.models.categories import CategoryModel, CategoryCreateModel, CategoryUpdateModel

router = APIRouter(tags=["Категории"])


@router.get(
    "/",
    response_model=List[CategoryModel],
    summary="Получить список категорий",
    description="""
    Получает список всех доступных категорий.
    
    - Возвращает все категории в алфавитном порядке
    - Включает информацию о дате создания и обновления
    - Возвращает пустой список, если категории отсутствуют
    """,
    responses={
        200: {
            "description": "Список категорий успешно получен",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Смартфоны",
                            "created_at": "2024-04-15T12:00:00",
                            "updated_at": "2024-04-15T12:00:00"
                        },
                        {
                            "id": 2,
                            "name": "Ноутбуки",
                            "created_at": "2024-04-15T12:00:00",
                            "updated_at": "2024-04-15T12:00:00"
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
async def get_categories():
    """
    Получить список всех категорий.
    
    Returns:
        List[CategoryModel]: Список категорий
        
    Raises:
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await categories.get_categories()


@router.post(
    "/",
    response_model=CategoryModel,
    summary="Создать новую категорию",
    description="""
    Создает новую категорию в системе.
    
    - Имя категории должно быть уникальным
    - Автоматически устанавливаются даты создания и обновления
    - Доступно только для администраторов
    """,
    responses={
        200: {
            "description": "Категория успешно создана",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Смартфоны",
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:00:00"
                    }
                }
            }
        },
        400: {
            "description": "Категория с таким именем уже существует",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Category with this name already exists"
                    }
                }
            }
        },
        403: {
            "description": "Нет прав для создания категории",
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
async def create_category(category_data: CategoryCreateModel):
    """
    Создает новую категорию.
    
    Args:
        category_data (CategoryCreateModel): Данные для создания категории
        
    Returns:
        CategoryModel: Созданная категория
        
    Raises:
        HTTPException: 400 если категория с таким именем уже существует
        HTTPException: 403 если нет прав для создания
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await categories.create_category(category_data)


@router.put(
    "/{category_id}",
    response_model=CategoryModel,
    summary="Обновить категорию",
    description="""
    Обновляет существующую категорию.
    
    - Можно изменить только имя категории
    - Новое имя должно быть уникальным
    - Автоматически обновляется дата обновления
    - Доступно только для администраторов
    """,
    responses={
        200: {
            "description": "Категория успешно обновлена",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Смартфоны и планшеты",
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:30:00"
                    }
                }
            }
        },
        400: {
            "description": "Категория с таким именем уже существует",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Category with this name already exists"
                    }
                }
            }
        },
        403: {
            "description": "Нет прав для обновления категории",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        },
        404: {
            "description": "Категория не найдена",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Category not found"
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
async def update_category(category_id: int, category_data: CategoryUpdateModel):
    """
    Обновляет существующую категорию.
    
    Args:
        category_id (int): ID категории для обновления
        category_data (CategoryUpdateModel): Новые данные категории
        
    Returns:
        CategoryModel: Обновленная категория
        
    Raises:
        HTTPException: 400 если категория с таким именем уже существует
        HTTPException: 403 если нет прав для обновления
        HTTPException: 404 если категория не найдена
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await categories.update_category(category_id, category_data)


@router.delete(
    "/{category_id}",
    response_model=None,
    status_code=204,
    summary="Удалить категорию",
    description="""
    Удаляет категорию из системы.
    
    - Категория не должна содержать связанных товаров
    - Удаление необратимо
    - Доступно только для администраторов
    - Возвращает статус 204 при успешном удалении
    """,
    responses={
        204: {
            "description": "Категория успешно удалена"
        },
        400: {
            "description": "Невозможно удалить категорию с товарами",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete category: there are items associated with it"
                    }
                }
            }
        },
        403: {
            "description": "Нет прав для удаления категории",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        },
        404: {
            "description": "Категория не найдена",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Category not found"
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
async def delete_category(category_id: int):
    """
    Удаляет категорию.
    
    Args:
        category_id (int): ID категории для удаления
        
    Returns:
        None: При успешном удалении возвращает статус 204
        
    Raises:
        HTTPException: 400 если категория содержит товары
        HTTPException: 403 если нет прав для удаления
        HTTPException: 404 если категория не найдена
        HTTPException: 500 при внутренней ошибке сервера
    """
    await categories.delete_category(category_id)
    return {"message": "Категория успешно удалена"}