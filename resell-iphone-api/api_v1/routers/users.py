from fastapi import APIRouter, HTTPException
from api_v1.services import users

from core.models.users import (
    UserResponseModel, 
    UserBase,
    RoleBase,
    RoleResponseModel
)

router = APIRouter(tags=["Пользователи"])


@router.post(
    "/",
    response_model=UserResponseModel,
    summary="Создать нового пользователя",
    description="""
    Создает нового пользователя в системе.
    
    - Telegram ID должен быть уникальным
    - Автоматически устанавливаются даты создания и обновления
    - Пользователю присваивается роль по умолчанию
    - Все поля обязательны для заполнения
    """,
    responses={
        200: {
            "description": "Пользователь успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "user123",
                        "name": "Иван Иванов",
                        "contact": "@ivanov",
                        "telegram_id": 123456789,
                        "role_id": 1,
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:00:00",
                        "role": {
                            "id": 1,
                            "name": "user",
                            "description": "Обычный пользователь",
                            "created_at": "2024-04-15T12:00:00",
                            "updated_at": "2024-04-15T12:00:00"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Пользователь с таким Telegram ID уже существует",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with this telegram_id already exists"
                    }
                }
            }
        },
        422: {
            "description": "Некорректные данные запроса",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid request data"
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
async def create_user(data: UserBase) -> UserResponseModel:
    """
    Создает нового пользователя.
    
    Args:
        data (UserBase): Данные нового пользователя
        
    Returns:
        UserResponseModel: Созданный пользователь с полной информацией
        
    Raises:
        HTTPException: 400 если пользователь с таким telegram_id уже существует
        HTTPException: 422 при некорректных данных запроса
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await users.create_user(data)


@router.get(
    "/{user_id}",
    response_model=UserResponseModel,
    summary="Получить информацию о пользователе",
    description="""
    Получает полную информацию о пользователе по его ID.
    
    - Возвращает все данные пользователя, включая его роль
    - Включает даты создания и обновления
    - Возвращает 404 если пользователь не найден
    """,
    responses={
        200: {
            "description": "Информация о пользователе успешно получена",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "user123",
                        "name": "Иван Иванов",
                        "contact": "@ivanov",
                        "telegram_id": 123456789,
                        "role_id": 1,
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:00:00",
                        "role": {
                            "id": 1,
                            "name": "user",
                            "description": "Обычный пользователь",
                            "created_at": "2024-04-15T12:00:00",
                            "updated_at": "2024-04-15T12:00:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Пользователь не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
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
async def get_user(user_id: int) -> UserResponseModel:
    """
    Получает информацию о пользователе по его ID.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        UserResponseModel: Полная информация о пользователе
        
    Raises:
        HTTPException: 404 если пользователь не найден
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await users.get_user(user_id)


@router.get(
    "/telegram/{telegram_id}/id",
    response_model=int,
    summary="Получить ID пользователя по Telegram ID",
    description="""
    Получает внутренний ID пользователя по его Telegram ID.
    
    - Полезно для интеграции с Telegram ботом
    - Возвращает только числовой ID пользователя
    - Возвращает 404 если пользователь не найден
    """,
    responses={
        200: {
            "description": "ID пользователя успешно получен",
            "content": {
                "application/json": {
                    "example": 1
                }
            }
        },
        404: {
            "description": "Пользователь с указанным Telegram ID не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
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
async def get_user_id_by_telegram_id(telegram_id: int) -> int:
    """
    Получает ID пользователя по его Telegram ID.
    
    Args:
        telegram_id (int): Telegram ID пользователя
        
    Returns:
        int: Внутренний ID пользователя в системе
        
    Raises:
        HTTPException: 404 если пользователь не найден
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await users.get_user_id_by_telegram_id(telegram_id)


@router.get(
    "/telegram/{telegram_id}/exists",
    response_model=bool,
    summary="Проверить существование пользователя",
    description="""
    Проверяет, существует ли пользователь с указанным Telegram ID.
    
    - Возвращает true/false в зависимости от существования пользователя
    - Полезно для проверки перед созданием нового пользователя
    - Быстрый и легковесный запрос
    """,
    responses={
        200: {
            "description": "Результат проверки существования пользователя",
            "content": {
                "application/json": {
                    "example": True
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
async def check_user_exists(telegram_id: int) -> bool:
    """
    Проверяет существование пользователя по Telegram ID.
    
    Args:
        telegram_id (int): Telegram ID пользователя
        
    Returns:
        bool: True если пользователь существует, False в противном случае
        
    Raises:
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await users.check_user_exists(telegram_id)


@router.post(
    "/roles/",
    response_model=RoleResponseModel,
    summary="Создать новую роль",
    description="""
    Создает новую роль в системе.
    
    - Имя роли должно быть уникальным
    - Автоматически устанавливаются даты создания и обновления
    - Все поля обязательны для заполнения
    - Роли используются для разграничения прав доступа
    """,
    responses={
        200: {
            "description": "Роль успешно создана",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "admin",
                        "description": "Администратор системы",
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:00:00"
                    }
                }
            }
        },
        400: {
            "description": "Роль с таким именем уже существует",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Role with this name already exists"
                    }
                }
            }
        },
        422: {
            "description": "Некорректные данные запроса",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid request data"
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
async def create_role(data: RoleBase) -> RoleResponseModel:
    """
    Создает новую роль в системе.
    
    Args:
        data (RoleBase): Данные для создания роли
        
    Returns:
        RoleResponseModel: Созданная роль с полной информацией
        
    Raises:
        HTTPException: 400 если роль с таким именем уже существует
        HTTPException: 422 при некорректных данных запроса
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await users.create_role(data)


@router.get(
    "/roles/",
    response_model=list[RoleResponseModel],
    summary="Получить список всех ролей",
    description="""
    Получает список всех ролей, доступных в системе.
    
    - Возвращает полную информацию о каждой роли
    - Включает даты создания и обновления
    - Роли отсортированы по ID
    """,
    responses={
        200: {
            "description": "Список ролей успешно получен",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "user",
                            "description": "Обычный пользователь",
                            "created_at": "2024-04-15T12:00:00",
                            "updated_at": "2024-04-15T12:00:00"
                        },
                        {
                            "id": 2,
                            "name": "admin",
                            "description": "Администратор системы",
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
async def get_roles() -> list[RoleResponseModel]:
    """
    Получает список всех ролей в системе.
    
    Returns:
        list[RoleResponseModel]: Список ролей с полной информацией
        
    Raises:
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await users.get_roles()


@router.put(
    "/{user_id}/role/{role_id}",
    response_model=UserResponseModel,
    summary="Обновить роль пользователя",
    description="""
    Изменяет роль пользователя на указанную.
    
    - Обновляет роль пользователя в системе
    - Возвращает обновленную информацию о пользователе
    - Проверяет существование пользователя и роли
    """,
    responses={
        200: {
            "description": "Роль пользователя успешно обновлена",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "user123",
                        "name": "Иван Иванов",
                        "contact": "@ivanov",
                        "telegram_id": 123456789,
                        "role_id": 2,
                        "created_at": "2024-04-15T12:00:00",
                        "updated_at": "2024-04-15T12:00:00",
                        "role": {
                            "id": 2,
                            "name": "admin",
                            "description": "Администратор системы",
                            "created_at": "2024-04-15T12:00:00",
                            "updated_at": "2024-04-15T12:00:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Пользователь или роль не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User or role not found"
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
async def update_user_role(user_id: int, role_id: int) -> UserResponseModel:
    """
    Обновляет роль пользователя.
    
    Args:
        user_id (int): ID пользователя
        role_id (int): ID новой роли
        
    Returns:
        UserResponseModel: Обновленная информация о пользователе
        
    Raises:
        HTTPException: 404 если пользователь или роль не найдены
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await users.update_user_role(user_id, role_id)
