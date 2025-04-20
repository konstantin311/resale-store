import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# API settings
API_TOKEN = os.getenv("API_TOKEN")
API_HOST = os.getenv("API_HOST", "http://localhost:8015")

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN") or API_TOKEN  # Используем API_TOKEN как fallback
BOT_USERNAME = os.getenv("BOT_USERNAME")  # Имя бота в Telegram (без @)

# YooKassa settings
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_TEST_MODE = os.getenv("YOOKASSA_TEST_MODE", "True").lower() == "true" 