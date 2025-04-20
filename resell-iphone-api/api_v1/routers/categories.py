from typing import List

from fastapi import APIRouter

from api_v1.services import categories
from core.models.categories import CategoryModel, CategoryCreateModel, CategoryUpdateModel

router = APIRouter(tags=["Категории"])


@router.get("/", response_model=List[CategoryModel])
async def get_categories():
    """
    Получить список всех категорий.

    Этот эндпоинт возвращает список всех категорий, доступных в системе.

    Возвращает:
        List[CategoryModel]: Список категорий. Если категории отсутствуют, возвращается пустой список.

    Ошибки:
        500: Внутренняя ошибка сервера при получении списка категорий.
    """
    return await categories.get_categories()


@router.post("/", response_model=CategoryModel)
async def create_category(category_data: CategoryCreateModel):
    """
    Создать новую категорию.

    Этот эндпоинт создает новую категорию в системе.

    Параметры:
        category_data (CategoryCreateModel): Данные для создания категории.

    Возвращает:
        CategoryModel: Созданная категория.

    Ошибки:
        400: Категория с таким именем уже существует.
        500: Внутренняя ошибка сервера при создании категории.
    """
    return await categories.create_category(category_data)


@router.put("/{category_id}", response_model=CategoryModel)
async def update_category(category_id: int, category_data: CategoryUpdateModel):
    """
    Обновить существующую категорию.

    Этот эндпоинт обновляет данные существующей категории.

    Параметры:
        category_id (int): ID категории для обновления.
        category_data (CategoryUpdateModel): Новые данные категории.

    Возвращает:
        CategoryModel: Обновленная категория.

    Ошибки:
        404: Категория не найдена.
        400: Категория с таким именем уже существует.
        500: Внутренняя ошибка сервера при обновлении категории.
    """
    return await categories.update_category(category_id, category_data)


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """
    Удалить категорию.

    Этот эндпоинт удаляет категорию из системы.

    Параметры:
        category_id (int): ID категории для удаления.

    Ошибки:
        404: Категория не найдена.
        500: Внутренняя ошибка сервера при удалении категории.
    """
    await categories.delete_category(category_id)
    return {"message": "Категория успешно удалена"}