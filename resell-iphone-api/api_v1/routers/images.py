from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from core.models.images import ImageModel
from api_v1.services.images import save_image, get_item_images, delete_image

router = APIRouter(
    prefix="/images",
    tags=["Изображения"],
    responses={
        404: {"description": "Изображение или товар не найдены"},
        400: {"description": "Некорректный формат файла"},
        500: {"description": "Внутренняя ошибка сервера"}
    }
)


@router.post(
    "/{item_id}",
    response_model=ImageModel,
    summary="Загрузить изображение для товара",
    description="""
    Загружает изображение для указанного товара.
    
    - Поддерживаемые форматы: JPG, PNG, GIF
    - Максимальный размер файла: 1MB
    - Изображение сохраняется в директории static/uploads
    - Генерируется уникальное имя файла
    """,
    responses={
        200: {
            "description": "Изображение успешно загружено",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "file_path": "static/uploads/550e8400-e29b-41d4-a716-446655440000.jpg",
                        "item_id": 1,
                        "created_at": "2024-04-15T12:00:00"
                    }
                }
            }
        }
    }
)
async def upload_image(item_id: int, file: UploadFile = File(...)):
    """
    Загружает изображение для товара.
    
    Args:
        item_id (int): ID товара, для которого загружается изображение
        file (UploadFile): Файл изображения
        
    Returns:
        ImageModel: Информация о загруженном изображении
        
    Raises:
        HTTPException: 404 если товар не найден
        HTTPException: 400 если файл не является изображением
        HTTPException: 500 при ошибке сохранения файла
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    return await save_image(file, item_id)


@router.get(
    "/{item_id}",
    response_model=List[ImageModel],
    summary="Получить все изображения товара",
    description="""
    Возвращает список всех изображений, прикрепленных к указанному товару.
    
    - Возвращает пустой список, если у товара нет изображений
    - Изображения сортируются по дате создания (от новых к старым)
    """,
    responses={
        200: {
            "description": "Список изображений товара",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "file_path": "static/uploads/550e8400-e29b-41d4-a716-446655440000.jpg",
                        "item_id": 1,
                        "created_at": "2024-04-15T12:00:00"
                    }]
                }
            }
        }
    }
)
async def get_images(item_id: int):
    """
    Получает список всех изображений товара.
    
    Args:
        item_id (int): ID товара
        
    Returns:
        List[ImageModel]: Список изображений товара
    """
    return await get_item_images(item_id)


@router.delete(
    "/{image_id}",
    summary="Удалить изображение",
    description="""
    Удаляет изображение по его ID.
    
    - Удаляет файл из файловой системы
    - Удаляет запись из базы данных
    - Операция необратима
    """,
    responses={
        200: {
            "description": "Изображение успешно удалено",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Image deleted successfully"
                    }
                }
            }
        }
    }
)
async def remove_image(image_id: int):
    """
    Удаляет изображение.
    
    Args:
        image_id (int): ID изображения для удаления
        
    Returns:
        dict: Сообщение об успешном удалении
        
    Raises:
        HTTPException: 404 если изображение не найдено
        HTTPException: 500 при ошибке удаления файла
    """
    await delete_image(image_id)
    return {"message": "Image deleted successfully"} 