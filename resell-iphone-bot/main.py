import asyncio
import os
from dotenv import load_dotenv

import aiohttp
from aiogram import Bot, Dispatcher, types, Router
from aiogram import filters
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardRemove,
    BotCommand,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from loguru import logger

from routers.item import router as item_router
from routers.main import router as main_router
from states import register
from templates.main import contact_keyboard, main_menu
from config import API_HOST, BOT_TOKEN

# Загрузка переменных окружения
load_dotenv()

router = Router()

@router.message(filters.Command("start"))
async def send_welcome(message: types.Message, state: FSMContext) -> None:
    await state.set_state(None)
    await state.clear()
    
    # Проверяем существование пользователя
    async with aiohttp.ClientSession() as session:
        try:
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


@router.message(register.Register.CONTACT)
async def get_contact(
    message: types.Message, bot: Bot, state: FSMContext
) -> None:
    if message.contact:
        logger.info(f"Processing contact for user {message.from_user.id}")
        # Сначала проверяем, существует ли пользователь
        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"Checking if user exists: {message.from_user.id}")
                async with session.get(f"{API_HOST}/api/api/users/telegram/{message.from_user.id}/exists") as exists_response:
                    if exists_response.status == 200:
                        exists = await exists_response.json()
                        logger.info(f"User exists check result: {exists}")
                        if exists:
                            # Если пользователь существует, получаем его данные
                            logger.info(f"Getting user data for existing user: {message.from_user.id}")
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
                                            await state.set_state(None)
                                            await state.clear()
                                            return
                        else:
                            # Если пользователь не существует, создаем нового
                            logger.info(f"Creating new user: {message.from_user.id}")
                            user_data = {
                                "telegram_id": message.from_user.id,
                                "username": message.from_user.username or str(message.from_user.id),
                                "name": f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip() or str(message.from_user.id),
                                "contact": message.contact.phone_number,
                                "role_id": 1  # ID роли "buyer" (покупатель) - роль по умолчанию для новых пользователей
                            }
                            
                            logger.info(f"Sending user data: {user_data}")
                            async with session.post(f"{API_HOST}/api/api/users/", json=user_data) as response:
                                response_text = await response.text()
                                logger.info(f"Create user response status: {response.status}, text: {response_text}")
                                
                                # После создания пользователя показываем меню покупателя
                                # Все новые пользователи по умолчанию становятся покупателями
                                await message.answer(
                                    text=f"Вы успешно зарегистрированы как покупатель! Выберите нужный пункт меню 👇",
                                    reply_markup=await main_menu(role="buyer"),
                                )
                                await state.set_state(None)
                                await state.clear()
                    else:
                        error_text = await exists_response.text()
                        logger.error(f"Error checking user existence: {error_text}")
                        await message.answer(
                            text="Ошибка при проверке существования пользователя. Пожалуйста, попробуйте позже.",
                            reply_markup=await contact_keyboard(),
                        )
            except Exception as e:
                logger.error(f"Exception in get_contact: {str(e)}")
                await message.answer(
                    text="Ошибка при регистрации. Пожалуйста, попробуйте позже.",
                    reply_markup=await contact_keyboard(),
                )
    else:
        await message.answer(
            "Пожалуйста, отправьте контакт",
            reply_markup=await contact_keyboard(),
        )


async def main() -> None:
    logger.info("Starting bot")
    await logger.complete()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(router)  # Основной роутер с командами
    dp.include_router(item_router)  # Роутер для работы с объявлениями
    dp.include_router(main_router)  # Роутер для основного меню

    try:
        # Запускаем бота в режиме polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    logger.add("logs.log", level="INFO", rotation="1 week")
    asyncio.run(main())
