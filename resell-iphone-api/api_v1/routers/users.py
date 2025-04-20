from fastapi import APIRouter, HTTPException
from api_v1.services import users

from core.models.users import (
    UserResponseModel, 
    UserBase,
    RoleBase,
    RoleResponseModel
)

router = APIRouter(tags=["Пользователи"])


@router.post("/", response_model=UserResponseModel)
async def create_user(data: UserBase) -> UserResponseModel:
    """
    Создать нового пользователя.

    Этот эндпоинт позволяет создать нового пользователя.
    Telegram ID должен быть уникальным.

    Аргументы:
        data (UserBase): Данные нового пользователя.

    Возвращает:
        UserResponseModel: Созданный пользователь.

    Ошибки:
        400: Пользователь с таким telegram_id уже существует или роль не найдена.
        422: Некорректные данные запроса.
        500: Внутренняя ошибка сервера при создании пользователя.
    """
    return await users.create_user(data)


@router.get("/{user_id}", response_model=UserResponseModel)
async def get_user(user_id: int) -> UserResponseModel:
    """
    Получить информацию о пользователе по его ID.

    Этот эндпоинт позволяет получить подробную информацию о пользователе по его ID.

    Аргументы:
        user_id (int):  ID пользователя.

    Возвращает:
        UserResponseModel: Модель с подробной информацией о пользователе.

    Ошибки:
        404: Пользователь не найден.
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await users.get_user(user_id)


@router.get("/telegram/{telegram_id}/id", response_model=int)
async def get_user_id_by_telegram_id(telegram_id: int) -> int:
    """
    Получить ID пользователя по его Telegram ID.

    Этот эндпоинт позволяет получить ID пользователя по его Telegram ID.

    Аргументы:
        telegram_id (int): Telegram ID пользователя.

    Возвращает:
        int: ID пользователя.

    Ошибки:
        404: Пользователь не найден.
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await users.get_user_id_by_telegram_id(telegram_id)


@router.get("/telegram/{telegram_id}/exists", response_model=bool)
async def check_user_exists(telegram_id: int) -> bool:
    """
    Проверить существование пользователя по Telegram ID.

    Этот эндпоинт позволяет проверить, существует ли пользователь с указанным Telegram ID.

    Аргументы:
        telegram_id (int): Telegram ID пользователя.

    Возвращает:
        bool: True, если пользователь существует, False в противном случае.

    Ошибки:
        500: Внутренняя ошибка сервера при проверке существования пользователя.
    """
    return await users.check_user_exists(telegram_id)


@router.post("/roles/", response_model=RoleResponseModel)
async def create_role(data: RoleBase) -> RoleResponseModel:
    """
    Создать новую роль.

    Этот эндпоинт позволяет создать новую роль в системе.

    Аргументы:
        data (RoleBase): Данные новой роли.

    Возвращает:
        RoleResponseModel: Созданная роль.

    Ошибки:
        400: Роль с таким именем уже существует.
        422: Некорректные данные запроса.
        500: Внутренняя ошибка сервера при создании роли.
    """
    return await users.create_role(data)


@router.get("/roles/", response_model=list[RoleResponseModel])
async def get_roles() -> list[RoleResponseModel]:
    """
    Получить список всех ролей.

    Этот эндпоинт возвращает список всех ролей, доступных в системе.

    Возвращает:
        list[RoleResponseModel]: Список ролей.

    Ошибки:
        500: Внутренняя ошибка сервера при получении данных.
    """
    return await users.get_roles()


@router.put("/{user_id}/role/{role_id}", response_model=UserResponseModel)
async def update_user_role(user_id: int, role_id: int) -> UserResponseModel:
    """
    Обновить роль пользователя.

    Этот эндпоинт позволяет изменить роль пользователя.

    Аргументы:
        user_id (int): ID пользователя.
        role_id (int): ID новой роли.

    Возвращает:
        UserResponseModel: Обновленный пользователь.

    Ошибки:
        404: Пользователь или роль не найдены.
        500: Внутренняя ошибка сервера при обновлении роли.
    """
    return await users.update_user_role(user_id, role_id)
