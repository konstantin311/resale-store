import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
    FSInputFile,
)

from states import item
from config import API_HOST


async def item_menu(upload: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="💬 Название", callback_data="item_name"),
            InlineKeyboardButton(text="📝 Описание", callback_data="item_description"),
        ],
        [
            InlineKeyboardButton(text="📂 Категория", callback_data="item_category"),
            InlineKeyboardButton(text="💲 Стоимость", callback_data="item_price"),
        ],
        [
            InlineKeyboardButton(text="📷 Фото", callback_data="item_photo"),
            InlineKeyboardButton(text="📞 Контакт", callback_data="item_contact"),
        ],
        [
            (
                InlineKeyboardButton(
                    text="📢 Опубликовать объявление", callback_data="upload"
                )
                if not upload
                else InlineKeyboardButton(text="📢 Сохранить", callback_data="save")
            )
        ],
    ]
    if upload:
        keyboard.append(
            [InlineKeyboardButton(text="❌ Удалить", callback_data="delete")]
        )
    keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    )
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def save() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="create_ad")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def contact() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="Стандартный контакт", callback_data="default_contact"
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="create_ad")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def get_item_menu(
    callback_query: CallbackQuery | Message,
    state: FSMContext,
    host: str = "",
    photo: str = "https://elm48.ru/bitrix/templates/kitlisa-market/img/shop.png",
    update: bool = False,
) -> Message:
    (
        await callback_query.message.delete()
        if isinstance(callback_query, CallbackQuery)
        else callback_query.delete()
    )
    state_data = await state.get_data()
    if state_data.get("update"):
        update = True
    caption = f"""Название: {state_data.get('name')}
Описание: {state_data.get('description')}
Категория: {state_data.get('category_name', state_data.get('category'))}
Стоимость: {state_data.get('price')}
Валюта: {state_data.get('currency')}
Контактный номер: {state_data.get('contact')}
    """
    chat_id = (
        callback_query.chat.id
        if isinstance(callback_query, Message)
        else callback_query.message.chat.id
    )

    if state_data.get("image"):
        photo = state_data.get("image")
        photo = photo.replace("http://127.0.0.1:8015/api", ".")
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(photo),
            caption=caption,
            reply_markup=await item_menu(update),
        )
        await state.update_data(message=message)
        return message
    if await state.get_state() is None:
        await state.set_state(item.Add.MAIN)
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            reply_markup=await item_menu(update),
        )
        await state.update_data(message=message)
        return message
    if isinstance(callback_query, Message):
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            reply_markup=await item_menu(update),
        )
        await state.update_data(message=message)
        return message
    elif state_data.get("photo"):
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(state_data.get("photo")),
            caption=caption,
            reply_markup=await item_menu(update),
        )
        await state.update_data(message=message)
        return message
    else:
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            reply_markup=await item_menu(update),
        )
        await state.update_data(message=message)
        return message


async def get_categories_buttons() -> InlineKeyboardMarkup:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/categories/") as response:
                if response.status != 200:
                    return InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Назад", callback_data="create_ad")]
                        ]
                    )
                result = await response.json()

        keyboard = [
            [
                InlineKeyboardButton(
                    text=f'📌 {item["name"]}', callback_data=f"category_{item['id']}"
                )
            ]
            for item in result
        ]
        keyboard += [
            [InlineKeyboardButton(text="🔙 Назад", callback_data="create_ad")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    except Exception as e:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="create_ad")]
            ]
        )


async def get_currency_buttons() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="💵 USD", callback_data="currency_USD"),
        InlineKeyboardButton(text="💶 EUR", callback_data="currency_EUR"),
        InlineKeyboardButton(text="💷 RUB", callback_data="currency_RUB"),
    ]
    keyboard = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def view_item_menu(
    callback_query: CallbackQuery | Message,
    state: FSMContext,
    host: str = "",
    photo: str = "https://elm48.ru/bitrix/templates/kitlisa-market/img/shop.png",
) -> Message:
    (
        await callback_query.message.delete()
        if isinstance(callback_query, CallbackQuery)
        else callback_query.delete()
    )
    state_data = await state.get_data()
    caption = f"""Название: {state_data.get('name')}
Описание: {state_data.get('description')}
Категория: {state_data.get('category_name', state_data.get('category'))}
Стоимость: {state_data.get('price')}
Валюта: {state_data.get('currency')}
Контактный номер: {state_data.get('contact')}
    """
    chat_id = (
        callback_query.chat.id
        if isinstance(callback_query, Message)
        else callback_query.message.chat.id
    )

    # Создаем клавиатуру с кнопками
    keyboard = []
    
    # Добавляем кнопку "Купить" только если пользователь не является продавцом или администратором
    if not state_data.get("is_seller", False) and not state_data.get("is_admin", False):
        keyboard.append([InlineKeyboardButton(text="🛒 Купить", callback_data="buy_item")])
    
    # Добавляем кнопки управления статусом заказа для продавцов и администраторов
    if state_data.get("is_seller", False) or state_data.get("is_admin", False):
        order_id = state_data.get("order_id")
        if order_id:
            keyboard.extend([
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить заказ",
                        callback_data=f"update_order_status_{order_id}_confirmed"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🚚 Отправить заказ",
                        callback_data=f"update_order_status_{order_id}_shipped"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Завершить заказ",
                        callback_data=f"update_order_status_{order_id}_completed"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отменить заказ",
                        callback_data=f"update_order_status_{order_id}_cancelled"
                    )
                ]
            ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    if state_data.get("image"):
        photo = state_data.get("image")
        photo = photo.replace("http://127.0.0.1:8015/api", ".")
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(photo),
            caption=caption,
            reply_markup=markup,
        )
        return message
    elif state_data.get("photo"):
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(state_data.get("photo")),
            caption=caption,
            reply_markup=markup,
        )
        return message
    else:
        message = await callback_query.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            reply_markup=markup,
        )
        return message
