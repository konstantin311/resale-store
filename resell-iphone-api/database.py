from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

Base = declarative_base()

class Database:
    def __init__(self, host: str, port: int, name: str, user: str, password: str):
        self.database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        self.engine = create_async_engine(self.database_url)
        self.sessionmaker = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        """Get database session"""
        async with self.sessionmaker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self):
        """Close database connection"""
        await self.engine.dispose()


# Create database instance with environment variables
db = Database(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    name=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
) 