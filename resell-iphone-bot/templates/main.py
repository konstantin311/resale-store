import aiohttp
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    CallbackQuery,
    InputMediaPhoto,
)
from aiogram.fsm.context import FSMContext
from loguru import logger


async def contact_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="Отправить контакты", request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return markup


async def main_menu(role: str = "buyer") -> InlineKeyboardMarkup:
    keyboard = []
    
    # Для продавцов и администраторов показываем все кнопки
    if role in ["seller", "admin"]:
        keyboard.extend([
            [InlineKeyboardButton(text="📢 Создать объявление", callback_data="create_ad")],
            [InlineKeyboardButton(text="📋 Мои объявления", callback_data="my_ads")],
            [InlineKeyboardButton(text="🛍️ Мои заказы (как продавец)", callback_data="my_orders_seller")],
        ])
    
    # Для всех пользователей добавляем кнопку просмотра заказов как покупателя
    keyboard.append([InlineKeyboardButton(text="📦 Мои заказы (как покупатель)", callback_data="my_orders_buyer")])
    
    # Для администратора добавляем специальные кнопки
    if role == "admin":
        keyboard.extend([
            [InlineKeyboardButton(text="📊 Все товары", callback_data="view_all_items")],
            [InlineKeyboardButton(text="📊 Непроданные товары", callback_data="view_unsold_items")],
            [
                InlineKeyboardButton(
                    text="📊 Статистика магазина",
                    callback_data="show_statistics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📁 Управление категориями",
                    callback_data="manage_categories"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Управление пользователями",
                    callback_data="manage_users"
                )
            ],
        ])
    
    # Для всех пользователей, кроме администратора, показываем кнопку просмотра объявлений
    if role != "admin":
        keyboard.append([
            InlineKeyboardButton(
                text="🔍 Посмотреть объявления",
                callback_data="view_ads",
            )
        ])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📢 Создать объявление", callback_data="create_ad")],
        [InlineKeyboardButton(text="📋 Мои объявления", callback_data="my_ads")],
        [
            InlineKeyboardButton(
                text="🔍 Посмотреть объявления",
                callback_data="view_ads",
            )
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def get_users_ads(telegram_id: int, host: str, page: int = 1) -> InlineKeyboardMarkup:
    try:
        # Сначала получаем ID пользователя по telegram_id
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{host}/api/api/users/telegram/{telegram_id}/id"
            ) as response:
                if response.status != 200:
                    return InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
                        ]
                    )
                user_id = await response.json()

        # Получаем непроданные объявления пользователя
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{host}/api/api/items/unsold/by_user/{user_id}?page={page}"
            ) as response:
                if response.status != 200:
                    return InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
                        ]
                    )
                result = await response.json()

        keyboard = [
            [
                InlineKeyboardButton(
                    text=f'📌 {item["name"]}', callback_data=f"item_card_{item['id']}"
                )
            ]
            for item in result.get("items", [])
        ]
        nav_keyboard = []
        if result.get("next_page", False):
            nav_keyboard.append(
                InlineKeyboardButton(
                    text="➡️ Следующая страница",
                    callback_data=f"next_page_{page + 1}",
                )
            )
        if page > 1:
            nav_keyboard.append(
                InlineKeyboardButton(
                    text="⬅️ Предыдущая страница",
                    callback_data=f"prev_page_{page - 1}",
                )
            )
        keyboard += [
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    except Exception as e:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
            ]
        )


async def get_ads(
    host: str, page: int = 1, category: str = None
) -> InlineKeyboardMarkup:
    url = f"{host}/api/api/items/?page={page}"
    if category:
        url += f"&category={category}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.json()
    keyboard = [
        [
            InlineKeyboardButton(
                text=f'📌 {item["name"]}', callback_data=f"view_item_{item['id']}"
            )
        ]
        for item in result.get("items", [])
    ]
    nav_keyboard = []
    if result.get("next_page", False):
        nav_keyboard.append(
            InlineKeyboardButton(
                text="➡️ Следующая страница",
                callback_data=f"next_page_{page + 1}",
            )
        )
    if page > 1:
        nav_keyboard.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущая страница",
                callback_data=f"prev_page_{page - 1}",
            )
        )
    keyboard += [
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def get_filter_menu() -> InlineKeyboardMarkup:
    logger.info("Creating filter menu")
    keyboard = [
        [InlineKeyboardButton(text="📅 По дате", callback_data="filter_date")],
        [
            InlineKeyboardButton(text="💰 По цене по возрастанию", callback_data="filter_asc"),
            InlineKeyboardButton(text="💰 По цене по убыванию", callback_data="filter_desc")
        ],
        [InlineKeyboardButton(text="❌ Сбросить фильтры", callback_data="filter_reset")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_ads")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_ads_with_filters(
    host: str,
    page: int = 1,
    category: str = None,
    filter_type: str = None,
    filter_value: str = None,
    show_all: bool = False
) -> InlineKeyboardMarkup:
    # Формируем URL с параметрами
    # Для обычных пользователей и по умолчанию используем эндпоинт unsold
    base_url = f"{host}/api/api/items/{'unsold' if not show_all else ''}"
    url = f"{base_url}?page={page}"
    
    if category:
        url += f"&category={category}"
    if filter_type:
        url += f"&filter_type={filter_type}"
    if filter_value:
        url += f"&filter_value={filter_value}"
    
    logger.info(f"Requesting ads with URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error getting ads: {response.status}")
                    return InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
                        ]
                    )
                result = await response.json()
                logger.info(f"Received response: {result}")
        
        # Создаем кнопки для объявлений
        keyboard = []
        if result.get("items"):
            for item in result.get("items", []):
                keyboard.append([
                    InlineKeyboardButton(
                        text=f'📌 {item["name"]} - {item["price"]} {item.get("currency", "")}',
                        callback_data=f"view_item_{item['id']}"
                    )
                ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    text="Нет объявлений",
                    callback_data="no_ads"
                )
            ])
        
        # Добавляем кнопки навигации
        nav_keyboard = []
        if result.get("next_page", False):
            nav_keyboard.append(
                InlineKeyboardButton(
                    text="➡️ Следующая страница",
                    callback_data=f"next_page_{page + 1}"
                )
            )
        if page > 1:
            nav_keyboard.append(
                InlineKeyboardButton(
                    text="⬅️ Предыдущая страница",
                    callback_data=f"prev_page_{page - 1}"
                )
            )
        
        # Добавляем кнопки фильтрации
        keyboard.append([
            InlineKeyboardButton(
                text="🔍 Фильтры",
                callback_data="show_filters"
            )
        ])
        
        # Добавляем навигацию и кнопку "Назад"
        if nav_keyboard:
            keyboard.append(nav_keyboard)
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 Назад в меню",
                callback_data="back_to_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    except Exception as e:
        logger.error(f"Error in get_ads_with_filters: {str(e)}")
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
            ]
        )


async def get_all_items(host: str, page: int = 1, show_unsold: bool = False) -> InlineKeyboardMarkup:
    try:
        # Формируем URL в зависимости от того, нужны ли все товары или только непроданные
        endpoint = "unsold" if show_unsold else ""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{host}/api/api/items/{endpoint}?page={page}"
            ) as response:
                if response.status != 200:
                    return InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
                        ]
                    )
                result = await response.json()

        keyboard = [
            [
                InlineKeyboardButton(
                    text=f'📌 {item["name"]}', callback_data=f"item_card_{item['id']}"
                )
            ]
            for item in result.get("items", [])
        ]
        nav_keyboard = []
        if result.get("next_page", False):
            nav_keyboard.append(
                InlineKeyboardButton(
                    text="➡️ Следующая страница",
                    callback_data=f"next_page_{page + 1}",
                )
            )
        if page > 1:
            nav_keyboard.append(
                InlineKeyboardButton(
                    text="⬅️ Предыдущая страница",
                    callback_data=f"prev_page_{page - 1}",
                )
            )
        keyboard += [
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    except Exception as e:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
            ]
        )



