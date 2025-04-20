import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import uvicorn.logging

import api_v1
from core.db.base import Base
from database_handler import DatabaseHandler, settings, init_tables
from deps import DatabaseMarker, SettingsMarker
from settings import Settings
from api_v1.routers import images, items, categories, users, health, payments

# Настройка логирования
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.dependency_overrides[SettingsMarker]()

    postgres_url = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    logger.info(f"Подключение к базе данных по URL: {postgres_url}")
    db = DatabaseHandler(postgres_url)

    # 🔍 Проверка подключения
    try:
        async with db.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("✅ Успешное подключение к базе данных")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        raise

    await init_tables(db)  # ← Не забудь передать db
    app.dependency_overrides.update({
        DatabaseMarker: lambda: db.sessionmaker,
    })

    yield

    await db.engine.dispose()


def register_app(settings: Settings) -> FastAPI:
    root_app = FastAPI()
    app = FastAPI(lifespan=lifespan)
    
    # Register health check first to avoid route conflicts
    app.include_router(health.router, prefix="/api/v1")
    
    # Then register other routers
    app.include_router(api_v1.router, prefix="/api")
    app.include_router(images.router, prefix="/api/v1")
    app.include_router(payments.router, prefix="/api/v1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=settings.cors_allowed_methods,
        allow_headers=settings.cors_allowed_headers,
    )

    root_app.mount("/api", app)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return root_app


app = register_app(settings=settings)
