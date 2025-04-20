import os
from core.db.tables import User, Item, Category, ItemVector

import dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from core.db.base import Base
from core.db.tables import User, Item, Category, ItemVector  # Импортируем все модели
from settings import Settings

dotenv.load_dotenv()

settings = Settings(
    db_name=os.getenv("DB_NAME", "postgres"),
    db_host=os.getenv("DB_HOST", "db"),
    db_port=int(os.getenv("DB_PORT", "5432")),
    db_user=os.getenv("DB_USER", "postgres"),
    db_password=os.getenv("DB_PASSWORD", "postgres"),
    cors_allowed_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    cors_allowed_methods=os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(","),
    cors_allowed_headers=os.getenv("ALLOWED_HEADERS", "*").split(","),
    pagination_limit=int(os.getenv("PAGINATION_LIMIT", "10")),
)


class DatabaseHandler:
    def __init__(self, url: str):
        self.url = url
        self.engine = create_async_engine(
            self.url,
            echo=True,
        )
        self.sessionmaker = async_sessionmaker(
            self.engine, autoflush=False, autocommit=False
        )


postgres_url = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
db = DatabaseHandler(postgres_url)


async def init_tables(db_handler: DatabaseHandler):
    """Initialize database tables"""
    async with db_handler.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)