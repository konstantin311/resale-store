from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


class DatabaseHandler:
    def __init__(self, url: str):
        self.url = url
        self.engine = create_async_engine(
            self.url,
            echo=False,
        )
        self.sessionmaker = async_sessionmaker(
            self.engine, autoflush=False, autocommit=False
        )

    async def close_connection(self):
        await self.engine.dispose()
