from unittest.mock import AsyncMock, MagicMock

# Мок для категории
mock_category = {
    "id": 1,
    "name": "Смартфоны",
    "description": "Категория для смартфонов"
}

# Мок для товара
mock_item = {
    "id": 1,
    "title": "iPhone 13 Pro",
    "description": "Новый iPhone 13 Pro, 256GB",
    "price": 999.99,
    "category_id": 1
}

# Мок для сессии базы данных
class MockDBSession:
    def __init__(self):
        self.items = []
        self.categories = []
        
    async def execute(self, query):
        return MagicMock()
        
    async def commit(self):
        pass
        
    async def refresh(self, obj):
        pass
        
    async def close(self):
        pass

    def add(self, obj):
        if hasattr(obj, '__tablename__'):
            if obj.__tablename__ == 'items':
                self.items.append(obj)
            elif obj.__tablename__ == 'categories':
                self.categories.append(obj)

# Мок для зависимости базы данных
async def override_get_db():
    session = MockDBSession()
    try:
        yield session
    finally:
        await session.close() 