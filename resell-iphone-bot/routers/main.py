import aiohttp
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from loguru import logger
import os
import json
import time
import asyncio
from datetime import datetime

from states.item import Edit, Add
from templates.item import get_item_menu, view_item_menu
from templates.main import (
    main_menu,
    get_users_ads,
    get_ads,
    get_main_menu,
    get_ads_with_filters,
    get_filter_menu,
    get_all_items,
    contact_keyboard
)
from aiogram.fsm.state import State, StatesGroup
from states import register
from config import API_HOST, BOT_USERNAME

router = Router()

class ItemStates(StatesGroup):
    name = State()
    price = State()
    description = State()
    city = State()
    contacts = State()
    photo = State()

class CategoryStates(StatesGroup):
    adding_name = State()
    editing_name = State()
    editing_category_id = State()
    editing_user_id = State()

@router.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext) -> None:
    # Очищаем состояние
    await state.set_state(None)
    await state.clear()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Проверяем существование пользователя
            async with session.get(f"{API_HOST}/api/api/users/telegram/{message.from_user.id}/exists") as exists_response:
                if exists_response.status == 200:
                    exists = await exists_response.json()
                    if exists:
                        # Если пользователь существует, получаем его данные
                        async with session.get(f"{API_HOST}/api/api/users/telegram/{message.from_user.id}/id") as id_response:
                            if id_response.status == 200:
                                user_id = await id_response.json()
                                async with session.get(f"{API_HOST}/api/api/users/{user_id}") as user_response:
                                    if user_response.status == 200:
                                        user_data = await user_response.json()
                                        role = user_data.get("role", {}).get("name", "buyer")
                                        await message.answer(
                                            text=f"Выберите нужный пункт меню 👇",
                                            reply_markup=await main_menu(role=role),
                                        )
                                        return
                    else:
                        # Если пользователь не существует, запрашиваем контакт
                        logger.info(f"User:{message.from_user.id} Command: /start - New user")
                        await message.answer(
                            "Чтобы отправить контакт, нажмите на кнопку ниже",
                            reply_markup=await contact_keyboard(),
                        )
                        await state.set_state(register.Register.CONTACT)
    except Exception as e:
        logger.error(f"Error in send_welcome: {str(e)}")
        await message.answer(
            text="Ошибка при проверке данных пользователя. Пожалуйста, попробуйте позже.",
            reply_markup=await contact_keyboard(),
        )
        await state.set_state(register.Register.CONTACT)

@router.callback_query(lambda c: c.data.startswith("pay_order_"))
async def pay_order(callback_query: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback_query.data.split("_")[2])
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем данные о заказе
            async with session.get(f"{API_HOST}/api/api/orders/{order_id}") as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error getting order data: {error_text}")
                    await callback_query.message.answer(
                        text="Ошибка при получении данных заказа. Пожалуйста, попробуйте позже."
                    )
                    return
                order_data = await response.json()
                
            # Создаем платеж через Юкассу
            yookassa_data = {
                "amount": {
                    "value": str(order_data["total"]),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"https://t.me/{BOT_USERNAME}?start=payment_{order_id}"
                },
                "capture": True,
                "description": f"Оплата заказа #{order_id}",
                "metadata": {
                    "order_id": order_id,
                    "telegram_id": callback_query.from_user.id
                }
            }
            
            # Генерируем уникальный ключ идемпотентности
            idempotence_key = f"order_{order_id}_{int(time.time())}"
            
            # Отправляем запрос в Юкассу
            async with session.post(
                "https://api.yookassa.ru/v3/payments",
                json=yookassa_data,
                headers={"Idempotence-Key": idempotence_key},
                auth=aiohttp.BasicAuth(
                    login=os.getenv("YOOKASSA_SHOP_ID"),
                    password=os.getenv("YOOKASSA_SECRET_KEY")
                )
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error creating Yookassa payment: {error_text}")
                    await callback_query.message.answer(
                        text="Ошибка при создании платежа",
                        show_alert=True
                    )
                    return
                
                payment = await response.json()
                
                # Создаем кнопки для перехода к оплате и проверки статуса
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💳 Перейти к оплате",
                                url=payment["confirmation"]["confirmation_url"]
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔄 Проверить статус оплаты",
                                callback_data=f"check_payment_{order_id}"
                            )
                        ]
                    ]
                )
                
                await callback_query.message.edit_text(
                    text=f"Сумма к оплате: {order_data['total']}\n"
                         f"Для оплаты перейдите по ссылке ниже.\n"
                         f"После оплаты нажмите кнопку 'Проверить статус оплаты'.",
                    reply_markup=keyboard
                )
    except Exception as e:
        logger.error(f"Error in pay_order: {str(e)}")
        await callback_query.message.answer(
            text="Произошла ошибка при создании платежа. Пожалуйста, попробуйте позже."
        )
    return

@router.callback_query(lambda c: c.data.startswith("check_payment_"))
async def check_payment(callback_query: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback_query.data.split("_")[2])
    logger.info(f"Checking payment status for order {order_id}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем данные о заказе
            async with session.get(f"{API_HOST}/api/api/orders/{order_id}") as order_response:
                if order_response.status != 200:
                    error_text = await order_response.text()
                    logger.error(f"Error getting order data: {error_text}")
                    await callback_query.message.answer(
                        text="❌ Произошла ошибка при получении данных заказа. Пожалуйста, свяжитесь с поддержкой."
                    )
                    return
                order_data = await order_response.json()
                logger.info(f"Retrieved order data: {order_data}")
            
            # Проверяем статус заказа
            if order_data["status"] == "PAID":
                await callback_query.message.edit_text(
                    text="✅ Заказ успешно оплачен! Спасибо за покупку.\n"
                         "Скоро с вами свяжется продавец для уточнения деталей доставки.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🔙 Вернуться в главное меню",
                                    callback_data="back_to_menu"
                                )
                            ]
                        ]
                    )
                )
            else:
                # Создаем клавиатуру с кнопкой проверки и возврата в меню
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔄 Проверить оплату заказа",
                                callback_data=f"check_payment_{order_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔙 Вернуться в главное меню",
                                callback_data="back_to_menu"
                            )
                        ]
                    ]
                )
                
                await callback_query.message.edit_text(
                    text="⏳ Ожидаем подтверждения оплаты от платежной системы.\n"
                         "Нажмите кнопку ниже, чтобы проверить статус оплаты.",
                    reply_markup=keyboard
                )
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        await callback_query.message.answer(
            text="❌ Произошла ошибка при проверке статуса оплаты. Пожалуйста, свяжитесь с поддержкой."
        )

@router.callback_query(F.data == "show_filters")
async def show_filters(callback_query: CallbackQuery, state: FSMContext):
    logger.info("Show filters button pressed")
    await callback_query.message.edit_text(
        text="🔍 Фильтры",
        reply_markup=await get_filter_menu()
    )

@router.callback_query(lambda c: c.data.startswith("view_item_"))
async def view_item(callback_query: CallbackQuery, state: FSMContext):
    item_id = int(callback_query.data.split("_")[2])
    logger.info(f"Trying to view item with ID: {item_id} from {API_HOST}/api/api/items/{item_id}")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_HOST}/api/api/items/{item_id}") as response:
            logger.info(f"Response status: {response.status}")
            if response.status == 200:
                item = await response.json()
                logger.info(f"Received item data: {item}")
                if "image" in item and item["image"]:
                    item["image"] = item["image"].split("/api/")[-1]
                await state.set_data(item)
                await view_item_menu(
                    callback_query, state, photo=item.get("photo")
                )
            else:
                error_text = await response.text()
                logger.error(f"Error getting item: {error_text}")
                await callback_query.bot.answer_callback_query(
                    callback_query.id,
                    text="Ошибка при получении информации о товаре",
                    show_alert=True,
                )

def get_status_text(status: str) -> str:
    status_map = {
        "CREATED": "Создан",
        "PAID": "Оплачен"
    }
    return status_map.get(status, status)

@router.callback_query(lambda c: c.data == "my_orders_buyer")
async def show_buyer_orders(callback_query: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Starting show_buyer_orders for user {callback_query.from_user.id}")
        
        # Отправляем сообщение о загрузке
        loading_message = await callback_query.message.edit_text(
            "🔄 Загрузка ваших заказов...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
        )
        
        async with aiohttp.ClientSession() as session:
            # Получаем ID пользователя по telegram_id
            logger.info(f"Requesting user ID for telegram_id: {callback_query.from_user.id}")
            async with session.get(f"{API_HOST}/api/api/users/telegram/{callback_query.from_user.id}/id") as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to get user ID. Status: {response.status}, Error: {error_text}")
                    await loading_message.edit_text(
                        "❌ Ошибка при получении данных пользователя.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                    )
                    return
                user_id = await response.json()
                logger.info(f"Got user ID: {user_id}")
            
            # Получаем список заказов пользователя как покупателя
            orders_url = f"{API_HOST}/api/api/orders/user/{user_id}?is_buyer=true"
            logger.info(f"Requesting orders from: {orders_url}")
            
            async with session.get(orders_url) as response:
                response_text = await response.text()
                logger.info(f"Orders API response: {response_text}")
                
                if response.status == 200:
                    try:
                        orders = await response.json()
                        logger.info(f"Parsed orders: {orders}")
                        
                        if not orders:
                            logger.info("No orders found for user")
                            await loading_message.edit_text(
                                "📦 У вас пока нет заказов как покупателя.",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                            )
                            return
                        
                        # Форматируем список заказов
                        orders_text = "📦 Ваши заказы:\n\n"
                        for order in orders:
                            logger.info(f"Processing order: {order}")
                            # Получаем информацию о товаре
                            item_url = f"{API_HOST}/api/api/items/{order['item_id']}"
                            logger.info(f"Requesting item info from: {item_url}")
                            
                            async with session.get(item_url) as item_response:
                                item_data = None
                                if item_response.status == 200:
                                    item_data = await item_response.json()
                                    logger.info(f"Got item data: {item_data}")
                                
                            orders_text += (
                                f"🆔 Заказ #{order['id']}\n"
                                f"📱 Товар: {item_data['name'] if item_data else 'Неизвестный товар'}\n"
                                f"💰 Сумма: {order['total']} RUB\n"
                                f"📊 Статус: {get_status_text(order['status'])}\n"
                                f"📅 Дата: {order['created_at']}\n"
                                f"🏠 Адрес доставки: {order['delivery_address']}\n"
                                f"📞 Телефон продавца: {order['seller_phone']}\n\n"
                            )
                        
                        logger.info(f"Final orders text: {orders_text}")
                        await loading_message.edit_text(
                            orders_text,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                        )
                    except Exception as e:
                        logger.error(f"Error processing orders: {str(e)}")
                        await loading_message.edit_text(
                            "❌ Ошибка при обработке данных заказов.",
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                        )
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get orders. Status: {response.status}, Error: {error_text}")
                    await loading_message.edit_text(
                        "❌ Произошла ошибка при получении списка заказов.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                    )
    except Exception as e:
        logger.error(f"Error in show_buyer_orders: {str(e)}")
        await loading_message.edit_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
        )

@router.callback_query(lambda c: c.data == "my_orders_seller")
async def show_seller_orders(callback_query: CallbackQuery, state: FSMContext):
    try:
        # Отправляем сообщение о загрузке
        loading_message = await callback_query.message.edit_text(
            "🔄 Загрузка ваших заказов...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
        )
        
        async with aiohttp.ClientSession() as session:
            # Получаем ID пользователя по telegram_id
            async with session.get(f"{API_HOST}/api/api/users/telegram/{callback_query.from_user.id}/id") as response:
                if response.status != 200:
                    await loading_message.edit_text(
                        "❌ Ошибка при получении данных пользователя.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                    )
                    return
                user_id = await response.json()
            
            # Получаем список заказов пользователя как продавца
            orders_url = f"{API_HOST}/api/api/orders/user/{user_id}?is_buyer=false"
            logger.info(f"Requesting orders from: {orders_url}")
            
            async with session.get(orders_url) as response:
                if response.status == 200:
                    orders = await response.json()
                    
                    if not orders:
                        await loading_message.edit_text(
                            "🛍️ У вас пока нет заказов как продавца.",
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                        )
                        return
                    
                    # Форматируем список заказов
                    orders_text = "🛍️ Заказы на ваши товары:\n\n"
                    for order in orders:
                        # Получаем информацию о товаре
                        async with session.get(f"{API_HOST}/api/api/items/{order['item_id']}") as item_response:
                            item_data = await item_response.json() if item_response.status == 200 else None
                            
                        # Получаем информацию о покупателе
                        async with session.get(f"{API_HOST}/api/api/users/{order['buyer_id']}") as buyer_response:
                            buyer_data = await buyer_response.json() if buyer_response.status == 200 else None
                            
                        orders_text += (
                            f"🆔 Заказ #{order['id']}\n"
                            f"📱 Товар: {item_data['name'] if item_data else 'Неизвестный товар'}\n"
                            f"💰 Сумма: {order['total']} RUB\n"
                            f"👤 Покупатель: @{buyer_data['username'] if buyer_data and buyer_data.get('username') else 'ID ' + str(order['buyer_id'])}\n"
                            f"📊 Статус: {get_status_text(order['status'])}\n"
                            f"📅 Дата: {order['created_at']}\n"
                            f"🏠 Адрес доставки: {order['delivery_address']}\n"
                            f"📞 Телефон покупателя: {order['buyer_phone']}\n\n"
                        )
                    
                    await loading_message.edit_text(
                        orders_text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get orders. Status: {response.status}, Error: {error_text}")
                    await loading_message.edit_text(
                        "❌ Произошла ошибка при получении списка заказов.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
                    )
    except Exception as e:
        logger.error(f"Error in show_seller_orders: {e}")
        await loading_message.edit_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]])
        )

@router.callback_query(lambda c: c.data not in [
    "my_orders_buyer",
    "my_orders_seller",
    "show_statistics",
    "manage_categories",
    "add_category",
    "edit_category",
    "delete_category",
    "manage_users",
    "change_user_role"
] and not c.data.startswith(("edit_category_", "delete_category_", "set_role_")))
async def process_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    logger.info(f"User:{callback_query.from_user.id} Query: {callback_query.data}")
    
    # Если это запрос на просмотр заказов, пропускаем его
    if callback_query.data in ["my_orders_buyer", "my_orders_seller"]:
        return

    if callback_query.data == "buy_item":
        # Получаем данные о товаре из состояния
        state_data = await state.get_data()
        item_id = state_data.get("id")
        
        # Сохраняем данные о товаре и пользователе в состоянии
        await state.update_data(
            item_id=item_id
        )
        
        # Запрашиваем адрес доставки
        await callback_query.message.answer(
            "Пожалуйста, введите адрес доставки:"
        )
        await state.set_state(register.Register.ADDRESS)
        return

    elif callback_query.data == "view_all_items":
        keyboard = await get_all_items(host=API_HOST, show_unsold=False)
        await callback_query.message.edit_text(
            "📊 Все товары:", reply_markup=keyboard
        )
        return

    elif callback_query.data == "view_unsold_items":
        keyboard = await get_all_items(host=API_HOST, show_unsold=True)
        await callback_query.message.edit_text(
            "📊 Непроданные товары:", reply_markup=keyboard
        )
        return

    elif callback_query.data.startswith("next_page_"):
        page = int(callback_query.data.split("_")[2])
        if "view_all_items" in callback_query.message.text:
            keyboard = await get_all_items(host=API_HOST, page=page, show_unsold=False)
        elif "view_unsold_items" in callback_query.message.text:
            keyboard = await get_all_items(host=API_HOST, page=page, show_unsold=True)
        else:
            keyboard = await get_users_ads(callback_query.from_user.id, API_HOST, page)
        await callback_query.message.edit_reply_markup(reply_markup=keyboard)
        return

    elif callback_query.data.startswith("prev_page_"):
        page = int(callback_query.data.split("_")[2])
        if "view_all_items" in callback_query.message.text:
            keyboard = await get_all_items(host=API_HOST, page=page, show_unsold=False)
        elif "view_unsold_items" in callback_query.message.text:
            keyboard = await get_all_items(host=API_HOST, page=page, show_unsold=True)
        else:
            keyboard = await get_users_ads(callback_query.from_user.id, API_HOST, page)
        await callback_query.message.edit_reply_markup(reply_markup=keyboard)
        return

    elif callback_query.data == "create_ad":
        message = await get_item_menu(callback_query, state)
        await state.update_data(message=message)
    elif callback_query.data == "back_to_menu":
        await state.set_state(None)
        await state.clear()
        # Получаем ID пользователя
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/users/telegram/{callback_query.from_user.id}/id") as id_response:
                if id_response.status == 200:
                    user_id = await id_response.json()
                    # Получаем информацию о пользователе по ID
                    async with session.get(f"{API_HOST}/api/api/users/{user_id}") as user_response:
                        if user_response.status == 200:
                            user_data = await user_response.json()
                            role = user_data.get("role", {}).get("name", "buyer")
                            await callback_query.bot.delete_message(
                                callback_query.message.chat.id, callback_query.message.message_id
                            )
                            await callback_query.bot.send_message(
                                chat_id=callback_query.message.chat.id,
                                text=f"Выберите нужный пункт меню 👇",
                                reply_markup=await main_menu(role=role),
                            )
                        else:
                            await callback_query.answer(
                                text="Ошибка при получении данных пользователя. Пожалуйста, попробуйте позже.",
                                show_alert=True,
                            )
                else:
                    await callback_query.answer(
                        text="Ошибка при получении ID пользователя. Пожалуйста, попробуйте позже.",
                        show_alert=True,
                    )
    elif callback_query.data == "my_ads":
        await state.set_data({"page": 1})
        await callback_query.message.edit_text(
            text="Мои объявления",
            reply_markup=await get_users_ads(callback_query.from_user.id, API_HOST),
        )
        await state.set_state(Edit.CHOICE)
    elif callback_query.data == "view_ads":
        await state.update_data(
            current_page=1,
            current_category=None,
            current_filter_type=None,
            current_filter_value=None
        )
        await callback_query.message.edit_text(
            text="📋 Список объявлений",
            reply_markup=await get_ads_with_filters(API_HOST)
        )
    elif callback_query.data == "show_filters":
        await callback_query.message.edit_text(
            text="🔍 Фильтры",
            reply_markup=await get_filter_menu()
        )
    elif callback_query.data.startswith("filter_"):
        filter_data = callback_query.data.split("_")[1]
        state_data = await state.get_data()
        current_page = state_data.get("current_page", 1)
        current_category = state_data.get("current_category")
        current_filter_type = state_data.get("current_filter_type")
        current_filter_value = state_data.get("current_filter_value")
        
        logger.info(f"Processing filter: {filter_data}")
        logger.info(f"Current state before update: page={current_page}, category={current_category}, filter_type={current_filter_type}, filter_value={current_filter_value}")
        
        if filter_data == "date":
            await state.update_data(current_filter_type="date", current_filter_value=None)
            current_filter_type = "date"
            current_filter_value = None
        elif filter_data == "asc":
            await state.update_data(current_filter_type="price", current_filter_value="asc")
            current_filter_type = "price"
            current_filter_value = "asc"
        elif filter_data == "desc":
            await state.update_data(current_filter_type="price", current_filter_value="desc")
            current_filter_type = "price"
            current_filter_value = "desc"
        elif filter_data == "reset":
            await state.update_data(
                current_filter_type=None,
                current_filter_value=None
            )
            current_filter_type = None
            current_filter_value = None
        
        logger.info(f"Updated state: page={current_page}, category={current_category}, filter_type={current_filter_type}, filter_value={current_filter_value}")
        
        await callback_query.message.edit_text(
            text="📋 Список объявлений",
            reply_markup=await get_ads_with_filters(
                API_HOST,
                current_page,
                current_category,
                current_filter_type,
                current_filter_value
            )
        )
    elif callback_query.data == "back_to_ads":
        state_data = await state.get_data()
        current_page = state_data.get("current_page", 1)
        current_category = state_data.get("current_category")
        current_filter_type = state_data.get("current_filter_type")
        current_filter_value = state_data.get("current_filter_value")
        
        await callback_query.message.edit_text(
            text="📋 Список объявлений",
            reply_markup=await get_ads_with_filters(
                API_HOST,
                current_page,
                current_category,
                current_filter_type,
                current_filter_value
            )
        )
    elif callback_query.data.startswith("item_card_"):
        item_id = int(callback_query.data.split("_")[2])
        logger.info(f"Trying to get item with ID: {item_id} from {API_HOST}/api/api/items/{item_id}")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/items/{item_id}") as response:
                logger.info(f"Response status: {response.status}")
                if response.status == 200:
                    item = await response.json()
                    logger.info(f"Received item data: {item}")
                    item["update"] = True
                    if "image" in item and item["image"]:
                        item["image"] = item["image"].split("/api/")[-1]
                    await state.set_data(item)
                    message = await get_item_menu(
                        callback_query, state, photo=item.get("photo"), update=True, host=API_HOST
                    )
                    await state.update_data(message=message)
                    await state.set_state(Add.MAIN)
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting item: {error_text}")
                    await callback_query.bot.answer_callback_query(
                        callback_query.id,
                        text="Ошибка при получении информации о товаре",
                        show_alert=True,
                    )

@router.callback_query(Edit.CHOICE)
async def process_callback(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data.startswith("item_card_"):
        item_id = int(callback_query.data.split("_")[2])
        logger.info(f"Trying to get item with ID: {item_id} from {API_HOST}/api/api/items/{item_id}")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/items/{item_id}") as response:
                logger.info(f"Response status: {response.status}")
                if response.status == 200:
                    item = await response.json()
                    logger.info(f"Received item data: {item}")
                    item["update"] = True
                    if "image" in item and item["image"]:
                        item["image"] = item["image"].split("/api/")[-1]
                    await state.set_data(item)
                    message = await get_item_menu(
                        callback_query, state, photo=item.get("photo"), update=True, host=API_HOST
                    )
                    await state.update_data(message=message)
                    await state.set_state(Add.MAIN)
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting item: {error_text}")
                    await callback_query.bot.answer_callback_query(
                        callback_query.id,
                        text="Ошибка при получении информации о товаре",
                        show_alert=True,
                    )
    elif callback_query.data == "back_to_menu":
        await state.set_state(None)
        await state.clear()
        await callback_query.bot.delete_message(
            callback_query.message.chat.id, callback_query.message.message_id
        )
        await callback_query.bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"Выберите нужный пункт меню 👇",
            reply_markup=await main_menu(),
        )

@router.callback_query(lambda c: c.data.startswith("filter_"))
async def process_filters(callback_query: CallbackQuery, state: FSMContext):
    logger.info(f"Filter button pressed: {callback_query.data}")
    filter_data = callback_query.data.split("_")[1]
    
    state_data = await state.get_data()
    current_page = state_data.get("current_page", 1)
    current_category = state_data.get("current_category")
    current_filter_type = state_data.get("current_filter_type")
    current_filter_value = state_data.get("current_filter_value")
    
    logger.info(f"Current state: page={current_page}, category={current_category}, filter_type={current_filter_type}, filter_value={current_filter_value}")
    
    if filter_data == "date":
        await state.update_data(current_filter_type="date")
        await callback_query.message.edit_text(
            text="📋 Список объявлений",
            reply_markup=await get_ads_with_filters(
                API_HOST,
                current_page,
                current_category,
                "date",
                current_filter_value
            )
        )
    elif filter_data == "asc":
        await state.update_data(current_filter_value="asc")
        await callback_query.message.edit_text(
            text="📋 Список объявлений",
            reply_markup=await get_ads_with_filters(
                API_HOST,
                current_page,
                current_category,
                current_filter_type,
                "asc"
            )
        )
    elif filter_data == "desc":
        await state.update_data(current_filter_value="desc")
        await callback_query.message.edit_text(
            text="📋 Список объявлений",
            reply_markup=await get_ads_with_filters(
                API_HOST,
                current_page,
                current_category,
                current_filter_type,
                "desc"
            )
        )
    elif filter_data == "reset":
        await state.update_data(
            current_filter_type=None,
            current_filter_value=None
        )
        await callback_query.message.edit_text(
            text="📋 Список объявлений",
            reply_markup=await get_ads_with_filters(
                API_HOST,
                current_page,
                current_category
            )
        )
    
    logger.info("Filter processing completed")

@router.callback_query(lambda c: c.data.startswith(("next_page_", "prev_page_")))
async def process_pagination(callback_query: CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split("_")[2])
    state_data = await state.get_data()
    current_category = state_data.get("current_category")
    current_filter_type = state_data.get("current_filter_type")
    current_filter_value = state_data.get("current_filter_value")
    
    await state.update_data(current_page=page)
    
    await callback_query.message.edit_text(
        text="📋 Список объявлений",
        reply_markup=await get_ads_with_filters(
            API_HOST,
            page,
            current_category,
            current_filter_type,
            current_filter_value
        )
    )

@router.callback_query(lambda c: c.data == "back_to_ads")
async def back_to_ads(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_page = state_data.get("current_page", 1)
    current_category = state_data.get("current_category")
    current_filter_type = state_data.get("current_filter_type")
    current_filter_value = state_data.get("current_filter_value")
    
    await callback_query.message.edit_reply_markup(
        reply_markup=await get_ads_with_filters(
            API_HOST,
            current_page,
            current_category,
            current_filter_type,
            current_filter_value
        )
    )

@router.message(register.Register.ADDRESS)
async def process_address(message: Message, state: FSMContext) -> None:
    # Получаем сохраненные данные
    state_data = await state.get_data()
    item_id = state_data.get("id")  # Используем id из state_data
    
    # Создаем заказ
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем ID пользователя
            async with session.get(f"{API_HOST}/api/api/users/telegram/{message.from_user.id}/id") as id_response:
                if id_response.status != 200:
                    await message.answer(
                        text="Ошибка при получении ID пользователя. Пожалуйста, попробуйте позже."
                    )
                    return
                user_id = await id_response.json()
            
            # Получаем данные о товаре
            async with session.get(f"{API_HOST}/api/api/items/{item_id}") as item_response:
                if item_response.status != 200:
                    await message.answer(
                        text="Ошибка при получении данных о товаре. Пожалуйста, попробуйте позже."
                    )
                    return
                item_data = await item_response.json()
            
            # Получаем данные о продавце
            async with session.get(f"{API_HOST}/api/api/users/{item_data.get('user_id')}") as seller_response:
                if seller_response.status != 200:
                    await message.answer(
                        text="Ошибка при получении данных о продавце. Пожалуйста, попробуйте позже."
                    )
                    return
                seller_data = await seller_response.json()
            
            # Создаем заказ
            order_data = {
                "item_id": item_id,
                "buyer_id": user_id,
                "seller_id": item_data.get("user_id"),
                "buyer_telegram_id": message.from_user.id,
                "seller_telegram_id": seller_data.get("telegram_id"),
                "buyer_phone": state_data.get("contact"),
                "seller_phone": seller_data.get("contact"),
                "delivery_address": message.text,
                "total": float(item_data.get("price", 0)),  # Преобразуем в float и устанавливаем значение по умолчанию
                "status": "CREATED"  # Начальный статус заказа
            }
            
            async with session.post(f"{API_HOST}/api/api/orders/", json=order_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error creating order: {error_text}")
                    await message.answer(
                        text="Ошибка при создании заказа. Пожалуйста, попробуйте позже."
                    )
                    return
                
                order = await response.json()
                
                # Создаем кнопку для оплаты
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💳 Оплатить заказ",
                                callback_data=f"pay_order_{order['id']}"
                            )
                        ]
                    ]
                )
                
                await message.answer(
                    text=f"Заказ успешно создан!\n"
                         f"ID заказа: {order['id']}\n"
                         f"Статус: {order['status']}\n"
                         f"Сумма: {order['total']}\n"
                         f"Адрес доставки: {message.text}",
                    reply_markup=keyboard
                )
                
                # Очищаем состояние
                await state.set_state(None)
                await state.clear()
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        await message.answer(
            text="Произошла ошибка при создании заказа. Пожалуйста, попробуйте позже."
        )

@router.callback_query(lambda c: c.data.startswith("update_order_status_"))
async def update_order_status(callback_query: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback_query.data.split("_")[3])
    new_status = callback_query.data.split("_")[4]
    
    # Проверяем, что статус является допустимым
    if new_status not in ["CREATED", "PAID"]:
        await callback_query.answer(
            text="Недопустимый статус заказа",
            show_alert=True
        )
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем данные о заказе
            async with session.get(f"{API_HOST}/api/api/orders/{order_id}") as order_response:
                if order_response.status != 200:
                    await callback_query.answer(
                        text="Ошибка при получении данных заказа",
                        show_alert=True
                    )
                    return
                order_data = await order_response.json()
            
            # Обновляем статус заказа, сохраняя текущее местоположение
            update_data = {
                "status": new_status,
                "location": order_data.get("location", "CREATED")
            }
            
            async with session.patch(
                f"{API_HOST}/api/api/orders/{order_id}",
                json=update_data
            ) as response:
                if response.status != 200:
                    await callback_query.answer(
                        text="Ошибка при обновлении статуса заказа",
                        show_alert=True
                    )
                    return
                
                await callback_query.answer(
                    text="Статус заказа успешно обновлен",
                    show_alert=True
                )
                
                # Обновляем сообщение с информацией о заказе
                await callback_query.message.edit_text(
                    text=f"Статус заказа #{order_id} обновлен на: {new_status}"
                )
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        await callback_query.answer(
            text="Произошла ошибка при обновлении статуса заказа",
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback_query: CallbackQuery, state: FSMContext):
    try:
        # Получаем роль пользователя
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/users/telegram/{callback_query.from_user.id}/role") as response:
                if response.status == 200:
                    role = await response.json()
                    # Получаем главное меню с учетом роли пользователя
                    markup = await main_menu(role)
                    await callback_query.message.edit_text(
                        "Главное меню",
                        reply_markup=markup
                    )
                else:
                    # Если не удалось получить роль, показываем меню по умолчанию
                    markup = await main_menu()
                    await callback_query.message.edit_text(
                        "Главное меню",
                        reply_markup=markup
                    )
    except Exception as e:
        logger.error(f"Error in back_to_menu: {e}")
        # В случае ошибки показываем меню по умолчанию
        markup = await main_menu()
        await callback_query.message.edit_text(
            "Главное меню",
            reply_markup=markup
        )

@router.callback_query(lambda c: c.data == "show_statistics")
async def show_statistics(callback_query: CallbackQuery, state: FSMContext):
    logger.info("Starting show_statistics handler")
    try:
        # Отправляем сообщение о загрузке
        await callback_query.answer("Загрузка статистики...")
        
        logger.info(f"Making request to {API_HOST}/api/api/statistics/")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/statistics/") as response:
                logger.info(f"Got response with status {response.status}")
                if response.status == 200:
                    stats = await response.json()
                    logger.info(f"Received statistics: {stats}")
                    
                    # Форматируем дату в более читаемый вид
                    last_updated = datetime.fromisoformat(stats["last_updated"].replace("Z", "+00:00"))
                    formatted_date = last_updated.strftime("%d.%m.%Y %H:%M:%S")
                    
                    stats_message = (
                        "📊 Статистика магазина\n\n"
                        f"👥 Всего пользователей: {stats['total_users']}\n"
                        f"🛍️ Продавцов: {stats['total_sellers']} (активных: {stats['active_sellers']})\n"
                        f"🛒 Покупателей: {stats['total_buyers']} (активных: {stats['active_buyers']})\n\n"
                        f"📦 Заказы:\n"
                        f"• Всего: {stats['total_orders']}\n"
                        f"• За год: {stats['yearly_orders']}\n"
                        f"• За месяц: {stats['monthly_orders']}\n\n"
                        f"💰 Прибыль:\n"
                        f"• Общая: {stats['total_profit']} RUB\n"
                        f"• За год: {stats['yearly_profit']} RUB\n"
                        f"• За месяц: {stats['monthly_profit']} RUB\n\n"
                        f"🕒 Обновлено: {formatted_date}"
                    )
                    
                    logger.info("Preparing keyboard")
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🔙 Вернуться в главное меню",
                                    callback_data="back_to_menu"
                                )
                            ]
                        ]
                    )
                    
                    logger.info("Sending statistics message")
                    await callback_query.message.edit_text(
                        text=stats_message,
                        reply_markup=keyboard
                    )
                    logger.info("Statistics message sent successfully")
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting statistics. Status: {response.status}, Response: {error_text}")
                    await callback_query.answer(
                        text="❌ Ошибка при получении статистики",
                        show_alert=True
                    )
    except Exception as e:
        logger.error(f"Error in show_statistics: {str(e)}")
        logger.exception("Full exception details:")
        await callback_query.answer(
            text="❌ Произошла ошибка при получении статистики",
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "manage_categories")
async def show_categories(callback_query: CallbackQuery, state: FSMContext):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/categories/") as response:
                if response.status == 200:
                    categories = await response.json()
                    
                    # Формируем сообщение со списком категорий
                    message_text = "📁 Управление категориями\n\n"
                    if categories:
                        for category in categories:
                            message_text += f"• {category['name']} (ID: {category['id']})\n"
                    else:
                        message_text += "Категории отсутствуют\n"
                    
                    # Создаем клавиатуру с кнопками управления
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                text="➕ Добавить категорию",
                                callback_data="add_category"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="✏️ Изменить категорию",
                                callback_data="edit_category"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Удалить категорию",
                                callback_data="delete_category"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔙 Вернуться в главное меню",
                                callback_data="back_to_menu"
                            )
                        ]
                    ]
                    
                    await callback_query.message.edit_text(
                        text=message_text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                    )
                else:
                    await callback_query.answer(
                        "❌ Ошибка при получении списка категорий",
                        show_alert=True
                    )
    except Exception as e:
        logger.error(f"Error in show_categories: {str(e)}")
        await callback_query.answer(
            "❌ Произошла ошибка",
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "add_category")
async def add_category_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        "Введите название новой категории:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Отмена",
                        callback_data="manage_categories"
                    )
                ]
            ]
        )
    )
    await state.set_state(CategoryStates.adding_name)

@router.message(CategoryStates.adding_name)
async def add_category_process(message: Message, state: FSMContext):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_HOST}/api/api/categories/",
                json={"name": message.text}
            ) as response:
                if response.status == 200:
                    await message.answer("✅ Категория успешно добавлена!")
                else:
                    await message.answer("❌ Ошибка при добавлении категории")
        
        # Возвращаемся к управлению категориями
        await state.clear()
        await show_categories_message(message)
    except Exception as e:
        logger.error(f"Error in add_category_process: {str(e)}")
        await message.answer("❌ Произошла ошибка при добавлении категории")

@router.callback_query(lambda c: c.data == "edit_category")
async def edit_category_start(callback_query: CallbackQuery, state: FSMContext):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/categories/") as response:
                if response.status == 200:
                    categories = await response.json()
                    keyboard = []
                    
                    for category in categories:
                        keyboard.append([
                            InlineKeyboardButton(
                                text=f"✏️ {category['name']}",
                                callback_data=f"edit_category_{category['id']}"
                            )
                        ])
                    
                    keyboard.append([
                        InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="manage_categories"
                        )
                    ])
                    
                    await callback_query.message.edit_text(
                        "Выберите категорию для редактирования:",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                    )
                else:
                    await callback_query.answer(
                        "❌ Ошибка при получении списка категорий",
                        show_alert=True
                    )
    except Exception as e:
        logger.error(f"Error in edit_category_start: {str(e)}")
        await callback_query.answer(
            "❌ Произошла ошибка",
            show_alert=True
        )

@router.callback_query(lambda c: c.data.startswith("edit_category_"))
async def edit_category_name(callback_query: CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split("_")[2])
    await state.update_data(editing_category_id=category_id)
    await callback_query.message.edit_text(
        "Введите новое название категории:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Отмена",
                        callback_data="manage_categories"
                    )
                ]
            ]
        )
    )
    await state.set_state(CategoryStates.editing_name)

@router.message(CategoryStates.editing_name)
async def edit_category_process(message: Message, state: FSMContext):
    try:
        state_data = await state.get_data()
        category_id = state_data.get("editing_category_id")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{API_HOST}/api/api/categories/{category_id}",
                json={"name": message.text}
            ) as response:
                if response.status == 200:
                    await message.answer("✅ Категория успешно обновлена!")
                else:
                    await message.answer("❌ Ошибка при обновлении категории")
        
        # Возвращаемся к управлению категориями
        await state.clear()
        await show_categories_message(message)
    except Exception as e:
        logger.error(f"Error in edit_category_process: {str(e)}")
        await message.answer("❌ Произошла ошибка при обновлении категории")

@router.callback_query(lambda c: c.data == "delete_category")
async def delete_category_start(callback_query: CallbackQuery, state: FSMContext):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/categories/") as response:
                if response.status == 200:
                    categories = await response.json()
                    keyboard = []
                    
                    for category in categories:
                        keyboard.append([
                            InlineKeyboardButton(
                                text=f"❌ {category['name']}",
                                callback_data=f"delete_category_{category['id']}"
                            )
                        ])
                    
                    keyboard.append([
                        InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="manage_categories"
                        )
                    ])
                    
                    await callback_query.message.edit_text(
                        "Выберите категорию для удаления:",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                    )
                else:
                    await callback_query.answer(
                        "❌ Ошибка при получении списка категорий",
                        show_alert=True
                    )
    except Exception as e:
        logger.error(f"Error in delete_category_start: {str(e)}")
        await callback_query.answer(
            "❌ Произошла ошибка",
            show_alert=True
        )

@router.callback_query(lambda c: c.data.startswith("delete_category_"))
async def delete_category_confirm(callback_query: CallbackQuery, state: FSMContext):
    try:
        category_id = int(callback_query.data.split("_")[2])
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{API_HOST}/api/api/categories/{category_id}") as response:
                if response.status == 200:
                    await callback_query.answer("✅ Категория успешно удалена!")
                else:
                    await callback_query.answer(
                        "❌ Ошибка при удалении категории",
                        show_alert=True
                    )
        
        # Обновляем список категорий
        await show_categories(callback_query, state)
    except Exception as e:
        logger.error(f"Error in delete_category_confirm: {str(e)}")
        await callback_query.answer(
            "❌ Произошла ошибка при удалении категории",
            show_alert=True
        )

async def show_categories_message(message: Message):
    """Вспомогательная функция для отображения списка категорий"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_HOST}/api/api/categories/") as response:
                if response.status == 200:
                    categories = await response.json()
                    
                    message_text = "📁 Управление категориями\n\n"
                    if categories:
                        for category in categories:
                            message_text += f"• {category['name']} (ID: {category['id']})\n"
                    else:
                        message_text += "Категории отсутствуют\n"
                    
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                text="➕ Добавить категорию",
                                callback_data="add_category"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="✏️ Изменить категорию",
                                callback_data="edit_category"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Удалить категорию",
                                callback_data="delete_category"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔙 Вернуться в главное меню",
                                callback_data="back_to_menu"
                            )
                        ]
                    ]
                    
                    await message.answer(
                        text=message_text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                    )
                else:
                    await message.answer("❌ Ошибка при получении списка категорий")
    except Exception as e:
        logger.error(f"Error in show_categories_message: {str(e)}")
        await message.answer("❌ Произошла ошибка")

@router.callback_query(lambda c: c.data == "manage_users")
async def show_users(callback_query: CallbackQuery, state: FSMContext):
    try:
        # Получаем список всех пользователей
        async with aiohttp.ClientSession() as session:
            # Сначала получаем список ролей
            async with session.get(f"{API_HOST}/api/api/users/roles/") as roles_response:
                if roles_response.status != 200:
                    await callback_query.answer("❌ Ошибка при получении списка ролей", show_alert=True)
                    return
                roles = await roles_response.json()
                roles_dict = {role['id']: role['name'] for role in roles}

            # Получаем статистику для получения общего списка пользователей
            async with session.get(f"{API_HOST}/api/api/statistics/") as stats_response:
                if stats_response.status != 200:
                    await callback_query.answer("❌ Ошибка при получении статистики", show_alert=True)
                    return
                stats = await stats_response.json()
                total_users = stats['total_users']

            # Формируем сообщение со списком пользователей
            message_text = "👥 Управление пользователями\n\n"
            message_text += f"Всего пользователей: {total_users}\n"
            message_text += "Выберите действие:\n"

            # Создаем клавиатуру с кнопками управления
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="🔄 Изменить роль пользователя",
                        callback_data="change_user_role"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Вернуться в главное меню",
                        callback_data="back_to_menu"
                    )
                ]
            ]

            await callback_query.message.edit_text(
                text=message_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )

    except Exception as e:
        logger.error(f"Error in show_users: {str(e)}")
        await callback_query.answer(
            "❌ Произошла ошибка при получении списка пользователей",
            show_alert=True
        )

@router.callback_query(lambda c: c.data == "change_user_role")
async def change_user_role_start(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        "Введите Telegram ID пользователя, чью роль хотите изменить:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="manage_users"
                    )
                ]
            ]
        )
    )
    await state.set_state(CategoryStates.editing_user_id)

@router.message(CategoryStates.editing_user_id)
async def process_user_id(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text)
        async with aiohttp.ClientSession() as session:
            # Проверяем существование пользователя
            async with session.get(f"{API_HOST}/api/api/users/telegram/{telegram_id}/exists") as exists_response:
                if exists_response.status != 200:
                    await message.answer("❌ Ошибка при проверке пользователя")
                    await state.clear()
                    return
                exists = await exists_response.json()
                if not exists:
                    await message.answer("❌ Пользователь не найден")
                    await state.clear()
                    return

            # Получаем ID пользователя
            async with session.get(f"{API_HOST}/api/api/users/telegram/{telegram_id}/id") as id_response:
                if id_response.status != 200:
                    await message.answer("❌ Ошибка при получении ID пользователя")
                    await state.clear()
                    return
                user_id = await id_response.json()

            # Получаем информацию о пользователе
            async with session.get(f"{API_HOST}/api/api/users/{user_id}") as user_response:
                if user_response.status != 200:
                    await message.answer("❌ Ошибка при получении данных пользователя")
                    await state.clear()
                    return
                user_data = await user_response.json()

            # Получаем список доступных ролей
            async with session.get(f"{API_HOST}/api/api/users/roles/") as roles_response:
                if roles_response.status != 200:
                    await message.answer("❌ Ошибка при получении списка ролей")
                    await state.clear()
                    return
                roles = await roles_response.json()

            # Сохраняем ID пользователя в состоянии
            await state.update_data(user_id=user_id)

            # Создаем клавиатуру с доступными ролями
            keyboard = []
            current_role = user_data.get('role', {}).get('name', 'Неизвестно')
            for role in roles:
                if role['name'] != current_role:  # Не показываем текущую роль
                    keyboard.append([
                        InlineKeyboardButton(
                            text=f"👤 {role['name']}",
                            callback_data=f"set_role_{role['id']}"
                        )
                    ])

            keyboard.append([
                InlineKeyboardButton(
                    text="🔙 Отмена",
                    callback_data="manage_users"
                )
            ])

            await message.answer(
                f"Текущая роль пользователя: {current_role}\n"
                "Выберите новую роль:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )

    except ValueError:
        await message.answer("❌ Некорректный формат Telegram ID. Пожалуйста, введите число.")
        await state.clear()
    except Exception as e:
        logger.error(f"Error in process_user_id: {str(e)}")
        await message.answer("❌ Произошла ошибка при обработке запроса")
        await state.clear()

@router.callback_query(lambda c: c.data.startswith("set_role_"))
async def set_user_role(callback_query: CallbackQuery, state: FSMContext):
    try:
        role_id = int(callback_query.data.split("_")[2])
        state_data = await state.get_data()
        user_id = state_data.get('user_id')

        if not user_id:
            await callback_query.answer("❌ Ошибка: ID пользователя не найден", show_alert=True)
            return

        async with aiohttp.ClientSession() as session:
            # Обновляем роль пользователя
            async with session.put(
                f"{API_HOST}/api/api/users/{user_id}/role/{role_id}"
            ) as response:
                if response.status == 200:
                    # Получаем название роли
                    async with session.get(f"{API_HOST}/api/api/users/roles/") as roles_response:
                        roles = await roles_response.json()
                        role_name = next((role['name'] for role in roles if role['id'] == role_id), "Неизвестно")
                    
                    await callback_query.answer(f"✅ Роль пользователя успешно изменена на {role_name}", show_alert=True)
                    await state.clear()
                    # Возвращаемся к управлению пользователями
                    await show_users(callback_query, state)
                else:
                    error_text = await response.text()
                    logger.error(f"Error updating user role: {error_text}")
                    await callback_query.answer(
                        "❌ Ошибка при обновлении роли пользователя",
                        show_alert=True
                    )

    except Exception as e:
        logger.error(f"Error in set_user_role: {str(e)}")
        await callback_query.answer(
            "❌ Произошла ошибка при изменении роли",
            show_alert=True
        )
        await state.clear()