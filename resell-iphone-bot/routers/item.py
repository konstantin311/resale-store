from uuid import uuid4
import os

import aiohttp
import phonenumbers
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from models.item import Item
from states.item import Add
from templates.item import (
    save,
    get_item_menu,
    get_categories_buttons,
    contact,
    get_currency_buttons,
)
from templates.main import main_menu
from config import API_HOST

router = Router()


@router.callback_query(Add.MAIN)
async def process_callback(callback_query: CallbackQuery, state: FSMContext):
    names = {
        "item_name": "Название",
        "item_price": "Цена",
        "item_currency": "Валюта",
        "item_category": "Категория",
        "item_contact": "Контакт",
        "item_description": "Описание",
        "item_photo": "Фото"
    }
    logger.info(f"User:{callback_query.from_user.id} Query: {callback_query.data}")
    await logger.complete()
    if callback_query.data == "back_to_menu":
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
    elif callback_query.data.startswith("item_"):
        states = {
            "item_name": Add.NAME,
            "item_category": Add.CATEGORY,
            "item_price": Add.PRICE,
            "item_phone_number": Add.CONTACT,
            "item_photo": Add.PHOTO,
            "item_contact": Add.CONTACT,
            "item_description": Add.DESCRIPTION,
        }
        await state.set_state(states[callback_query.data])

        if callback_query.data == "item_category":
            await callback_query.message.edit_caption(
                caption=f"Выберите категорию",
                reply_markup=await get_categories_buttons(),
            )
        elif callback_query.data == "item_contact":
            await callback_query.message.edit_caption(
                caption="Введите номер телефона\n* он будет автоматически сохранен",
                reply_markup=await contact(),
            )
        elif callback_query.data == "item_photo":
            await callback_query.message.edit_caption(
                caption="Отправьте фото товара\n* оно будет автоматически сохранено",
                reply_markup=await save(),
            )
        else:
            await callback_query.message.edit_caption(
                caption=f"Введите {names[callback_query.data].lower()}\n* автоматически сохраняется",
                reply_markup=await save(),
            )
    elif callback_query.data == "upload":
        data = await state.get_data()
        # Проверяем наличие всех обязательных полей
        required_fields = ["name", "price", "currency", "category", "contact", "description", "image"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            await callback_query.answer(
                f"Пожалуйста, заполните все поля: {', '.join(missing_fields)}",
                show_alert=True
            )
            return

        try:
            # Проверяем доступность API
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{API_HOST}/api/api/v1/health-check") as response:
                        if response.status != 200:
                            raise Exception("API недоступен")
                        response_data = await response.json()
                        if response_data.get("status") != "ok" or response_data.get("database") != "connected":
                            raise Exception("API не готов к работе")
                except Exception as e:
                    logger.error(f"API недоступен: {str(e)}")
                    await callback_query.answer(
                        "Ошибка: сервис временно недоступен",
                        show_alert=True
                    )
                    return

            # Создаем FormData
            form_data = aiohttp.FormData()
            
            # Добавляем все поля в форму
            form_data.add_field('name', data["name"])
            form_data.add_field('price', str(data["price"]))
            form_data.add_field('currency', data["currency"])
            form_data.add_field('category', data["category_name"])
            form_data.add_field('contact', data["contact"])
            form_data.add_field('description', data["description"])
            
            # Обработка изображения
            if "image" in data:
                image_path = data["image"]
                logger.info(f"Processing image: {image_path}")
                
                # Проверка существования файла
                if not os.path.exists(image_path):
                    logger.error(f"Image file not found: {image_path}")
                    await callback_query.answer(
                        "Ошибка: файл изображения не найден",
                        show_alert=True
                    )
                    return
                
                # Проверка размера файла
                file_size = os.path.getsize(image_path)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    logger.error(f"Image file too large: {file_size} bytes")
                    await callback_query.answer(
                        "Ошибка: файл изображения слишком большой",
                        show_alert=True
                    )
                    return
                
                try:
                    # Добавляем изображение в форму
                    form_data.add_field(
                        'image',
                        open(image_path, 'rb'),
                        filename=os.path.basename(image_path),
                        content_type='image/jpeg'
                    )
                    logger.info(f"Image added to form data: {image_path}")
                except Exception as e:
                    logger.error(f"Error adding image to form data: {str(e)}")
                    await callback_query.answer(
                        "Ошибка при обработке изображения",
                        show_alert=True
                    )
                    return
            else:
                logger.info("No image provided, sending request without image")

            # Логируем данные перед отправкой
            logger.info(f"Current state data: {data}")
            logger.info(f"Form data fields: {form_data._fields}")
            logger.info(f"Sending request to: {API_HOST}/api/api/items/?telegram_id={callback_query.from_user.id}")
            await logger.complete()

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{API_HOST}/api/api/items/?telegram_id={callback_query.from_user.id}",
                        data=form_data
                    ) as response:
                        response_text = await response.text()
                        logger.info(f"API Response status: {response.status}")
                        logger.info(f"API Response headers: {response.headers}")
                        logger.info(f"API Response text: {response_text}")
                        
                        if response.status == 200:
                            await callback_query.answer(
                                "Объявление успешно создано",
                                show_alert=True
                            )
                            await state.set_state(None)
                            await state.clear()
                            await callback_query.message.delete()
                            await callback_query.bot.send_message(
                                chat_id=callback_query.message.chat.id,
                                text="Выберите нужный пункт меню 👇",
                                reply_markup=await main_menu(),
                            )
                        else:
                            error_msg = f"Ошибка при создании объявления: {response_text}"
                            logger.error(error_msg)
                            await callback_query.answer(
                                error_msg,
                                show_alert=True
                            )
            except Exception as e:
                error_msg = f"Ошибка при отправке на API: {str(e)}"
                logger.error(error_msg)
                await callback_query.answer(
                    error_msg,
                    show_alert=True
                )
        except Exception as e:
            error_msg = f"Ошибка при создании объявления: {str(e)}"
            logger.error(error_msg)
            await callback_query.answer(
                error_msg,
                show_alert=True
            )
    elif callback_query.data == "save":
        data = await state.get_data()
        try:
            # Проверяем наличие всех обязательных полей
            required_fields = ["name", "price", "currency", "category", "contact", "description"]
            missing_fields = [field for field in required_fields if field not in data or data[field] is None]
            
            if missing_fields:
                await callback_query.bot.answer_callback_query(
                    callback_query.id,
                    text=f"Пожалуйста, заполните все поля: {', '.join(missing_fields)}",
                    show_alert=True,
                )
                return

            # Создаем FormData
            form_data = aiohttp.FormData()
            
            # Добавляем все поля в форму
            form_data.add_field('name', str(data["name"]))
            form_data.add_field('price', str(data["price"]))
            form_data.add_field('currency', str(data["currency"]))
            form_data.add_field('category', str(data["category"]))
            form_data.add_field('contact', str(data["contact"]))
            form_data.add_field('description', str(data["description"]))
            
            # Обработка изображения
            if "image" in data and data["image"]:
                image_path = data["image"]
                if os.path.exists(image_path):
                    form_data.add_field(
                        'image',
                        open(image_path, 'rb'),
                        filename=os.path.basename(image_path),
                        content_type='image/jpeg'
                    )
            
            logger.info(f"Sending update data with FormData")
            
        except Exception as e:
            logger.error(f"Error preparing update data: {str(e)}")
            await callback_query.bot.answer_callback_query(
                callback_query.id,
                text="Ошибка при обновлении объявления",
                show_alert=False,
            )
            return
        else:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{API_HOST}/api/api/items/{data['id']}", data=form_data
                ) as response:
                    status = response.status
                    if status != 204:
                        error_text = await response.text()
                        logger.error(f"Error updating item: {error_text}")
            if status == 204:
                await callback_query.bot.answer_callback_query(
                    callback_query.id,
                    text="Объявление обновлено",
                    show_alert=True,
                )
                await callback_query.message.delete()
                await callback_query.bot.send_message(
                    chat_id=callback_query.message.chat.id,
                    text=f"Выберите нужный пункт меню 👇",
                    reply_markup=await main_menu(),
                )
                await state.set_state(None)
                await state.clear()
            else:
                await callback_query.bot.answer_callback_query(
                    callback_query.id,
                    text="Ошибка при обновлении объявления, пожалуйста попробуйте ещё раз",
                    show_alert=False,
                )

    elif callback_query.data == "delete":
        data = await state.get_data()
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{API_HOST}/api/api/items/{data['id']}") as response:
                status = response.status
        if status == 204:
            await callback_query.bot.answer_callback_query(
                callback_query.id,
                text="Объявление удалено",
                show_alert=True,
            )
        else:
            await callback_query.bot.answer_callback_query(
                callback_query.id,
                text="Ошибка при удалении объявления, пожалуйста попробуйте ещё раз",
                show_alert=False,
            )
            return

        await callback_query.message.delete()
        await callback_query.bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"Выберите нужный пункт меню 👇",
            reply_markup=await main_menu(),
        )
        await state.set_state(None)
        await state.clear()


@router.callback_query(
    StateFilter(Add.NAME, Add.PRICE, Add.CONTACT, Add.PHOTO, Add.DESCRIPTION)
)
async def process_attr_callback(
    callback_query: CallbackQuery, state: FSMContext
):
    logger.info(f"User:{callback_query.from_user.id} Query: {callback_query.data}")
    await logger.complete()
    if callback_query.data == "default_contact":
        async with aiohttp.ClientSession() as session:
            # Получаем ID пользователя по telegram_id
            async with session.get(
                f"{API_HOST}/api/api/users/telegram/{callback_query.from_user.id}/exists"
            ) as response:
                if response.status == 200:
                    user_id = await response.json()
                    # Получаем информацию о пользователе по его ID
                    async with session.get(
                        f"{API_HOST}/api/api/users/{user_id}"
                    ) as user_response:
                        if user_response.status == 200:
                            result = await user_response.json()
                            await state.update_data({"contact": result.get("contact")})
                            await callback_query.bot.answer_callback_query(
                                callback_query.id,
                                text=f"Контакт сохранён",
                                show_alert=False,
                            )
                        else:
                            await callback_query.bot.answer_callback_query(
                                callback_query.id,
                                text=f"Ошибка при получении контакта",
                                show_alert=True,
                            )
                else:
                    await callback_query.bot.answer_callback_query(
                        callback_query.id,
                        text=f"Ошибка при получении ID пользователя",
                        show_alert=True,
                    )
    else:
        await callback_query.bot.answer_callback_query(
            callback_query.id,
            text=f"{str(await state.get_state()).split(':')[1].capitalize()} сохранена",
            show_alert=False,
        )
    await get_item_menu(callback_query, state)
    await state.set_state(Add.MAIN)
    return


@router.callback_query(Add.CATEGORY)
async def process_category(callback_query: CallbackQuery, state: FSMContext):
    logger.info(f"User:{callback_query.from_user.id} Query: {callback_query.data}")
    await logger.complete()
    if callback_query.data != "create_ad":
        # Получаем ID и название категории
        category_id = callback_query.data.split("_")[1]
        # Получаем название категории из нажатой кнопки
        for row in callback_query.message.reply_markup.inline_keyboard:
            for button in row:
                if button.callback_data == callback_query.data:
                    category_name = button.text.replace("📌 ", "")
                    break
        await state.update_data({
            "category": category_id,
            "category_name": category_name
        })
        await callback_query.bot.answer_callback_query(
            callback_query.id,
            text=f"Категория {category_name} сохранена",
            show_alert=False,
        )
    await get_item_menu(callback_query, state)
    await state.set_state(Add.MAIN)
    return


@router.message(StateFilter(Add.NAME, Add.CATEGORY, Add.CONTACT, Add.DESCRIPTION))
async def process_attr_text(message: Message, state: FSMContext):
    logger.info(f"User:{message.from_user.id} Text: {message.text}")
    await logger.complete()
    if await state.get_state() == Add.PRICE:
        try:
            result = float(message.text)
        except ValueError:
            await message.answer("Пожалуйста, введите число")
            return
        else:
            await state.update_data(
                {str(await state.get_state()).split(":")[1].lower(): result}
            )
    elif await state.get_state() == Add.NAME:
        if len(message.text) > 30:
            await message.answer("Название должно быть не более 30 символов")
            return
        elif len(message.text) < 3:
            await message.answer("Название должно быть не менее 3 символов")
            return
    elif await state.get_state() == Add.CONTACT:
        try:
            valid = phonenumbers.is_valid_number(phonenumbers.parse(message.text))
            if not valid:
                raise phonenumbers.phonenumberutil.NumberParseException
        except phonenumbers.phonenumberutil.NumberParseException:
            await message.answer("Пожалуйста, введите корректный номер телефона")
            return await message.delete()
    await state.update_data(
        {str(await state.get_state()).split(":")[1].lower(): message.text}
    )
    await message.delete()
    data = await state.get_data()
    await data["message"].delete()
    await get_item_menu(data["message"], state)
    await state.set_state(Add.MAIN)


@router.message(StateFilter(Add.PRICE))
async def process_price(message: Message, state: FSMContext):
    logger.info(f"User:{message.from_user.id} Text: {message.text}")
    try:
        result = float(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите число")
        return
    else:
        await state.update_data({"price": result})
    await logger.complete()
    data = await state.get_data()
    await message.delete()
    try:
        await message.bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=data["message"].message_id,
            caption=f"Выберите валюту:",
            reply_markup=await get_currency_buttons(),
        )
    except Exception as e:
        await data["message"].delete()
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=data["image"],
            caption=f"Выберите валюту:",
            reply_markup=await get_currency_buttons(),
        )
    await state.set_state(Add.CURRENCY)
    return


@router.callback_query(Add.CURRENCY)
async def process_currency(callback_query: CallbackQuery, state: FSMContext):
    logger.info(f"User:{callback_query.from_user.id} Query: {callback_query.data}")
    await logger.complete()
    await state.update_data({"currency": callback_query.data.split("_")[1]})
    await get_item_menu(callback_query, state)
    await state.set_state(Add.MAIN)
    return


@router.message(
    StateFilter(Add.PHOTO),
)
async def process_photo(message: Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        logger.info(f"Received photo with size: {photo.file_size} bytes")
        
        # Проверка размера файла
        if photo.file_size > 10 * 1024 * 1024:  # 10MB
            logger.warning(f"Photo too large: {photo.file_size} bytes")
            await message.answer(
                "Фото слишком большое. Максимальный размер - 10MB",
                reply_markup=await save(),
            )
            return

        # Создание уникального имени файла
        unique_filename = f"{uuid4()}.jpg"
        file_path = os.path.join("static", unique_filename)
        
        # Проверка и создание директории
        try:
            os.makedirs("static", exist_ok=True)
            if not os.access("static", os.W_OK):
                raise Exception("Directory 'static' is not writable")
        except Exception as e:
            logger.error(f"Error creating/accessing static directory: {str(e)}")
            await message.answer(
                "Ошибка при сохранении фото. Пожалуйста, попробуйте позже.",
                reply_markup=await save(),
            )
            return

        # Загрузка файла
        try:
            file_id = photo.file_id
            file = await message.bot.get_file(file_id)
            file_path = file.file_path
            
            logger.info(f"Downloading photo to: {file_path}")
            await message.bot.download_file(file_path, f"static/{unique_filename}")
            
            # Проверка успешности загрузки
            if not os.path.exists(f"static/{unique_filename}"):
                raise Exception("File was not saved successfully")
                
            await state.update_data(image=f"static/{unique_filename}")
            logger.info(f"Photo successfully saved as: static/{unique_filename}")
            
            await message.answer(
                "Фото успешно загружено",
                reply_markup=await save(),
            )
        except Exception as e:
            logger.error(f"Error saving photo: {str(e)}")
            await message.answer(
                "Ошибка при сохранении фото. Пожалуйста, попробуйте позже.",
                reply_markup=await save(),
            )
            return
    else:
        await message.answer(
            "Пожалуйста, отправьте фото",
            reply_markup=await save(),
        )
    
    await logger.complete()
    await message.delete()
    data = await state.get_data()
    if "message" in data:
        await data["message"].delete()
        # Создаем временный callback_query для возврата в меню
        temp_callback = type('obj', (object,), {
            'message': data["message"],
            'bot': message.bot,
            'delete': lambda: None
        })
        await get_item_menu(temp_callback, state)
    await state.set_state(Add.MAIN)
