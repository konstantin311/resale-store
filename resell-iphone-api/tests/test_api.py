import pytest
from httpx import AsyncClient
from .mocks import mock_item, mock_category

# Тест эндпоинта health check
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Тесты для работы с товарами
@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    # Сначала создаем категорию
    await test_create_category(client)
    
    response = await client.post("/api/v1/items/", json={
        "title": mock_item["title"],
        "description": mock_item["description"],
        "price": mock_item["price"],
        "category_id": mock_item["category_id"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == mock_item["title"]
    assert data["price"] == mock_item["price"]
    return data["id"]

@pytest.mark.asyncio
async def test_get_items(client: AsyncClient):
    # Создаем тестовый товар
    await test_create_item(client)
    
    response = await client.get("/api/v1/items/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_get_item_by_id(client: AsyncClient):
    # Создаем тестовый товар
    item_id = await test_create_item(client)
    
    response = await client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == mock_item["title"]

@pytest.mark.asyncio
async def test_update_item(client: AsyncClient):
    # Создаем тестовый товар
    item_id = await test_create_item(client)
    
    update_data = {
        "title": "iPhone 13 Pro Max",
        "price": 1099.99
    }
    response = await client.patch(f"/api/v1/items/{item_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["price"] == update_data["price"]

@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient):
    # Создаем тестовый товар
    item_id = await test_create_item(client)
    
    # Удаляем товар
    response = await client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 204
    
    # Проверяем, что товар действительно удален
    response = await client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 404

# Тесты для работы с категориями
@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    response = await client.post("/api/v1/categories/", json={
        "name": mock_category["name"],
        "description": mock_category["description"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == mock_category["name"]
    return data["id"]

@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient):
    # Создаем тестовую категорию
    await test_create_category(client)
    
    response = await client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

# Тест для проверки метрик Prometheus
@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    response = await client.get("/api/metrics")
    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text 