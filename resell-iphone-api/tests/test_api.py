import pytest
from httpx import AsyncClient

# Тест эндпоинта health check
@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Тесты для работы с товарами
@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    item_data = {
        "title": "iPhone 13 Pro",
        "description": "Новый iPhone 13 Pro, 256GB",
        "price": 999.99,
        "category_id": 1
    }
    response = await client.post("/api/v1/items/", json=item_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == item_data["title"]
    assert data["price"] == item_data["price"]
    return data["id"]

@pytest.mark.asyncio
async def test_get_items(client: AsyncClient):
    response = await client.get("/api/v1/items/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_get_item_by_id(client: AsyncClient):
    # Сначала создаем товар
    item_id = await test_create_item(client)
    # Затем получаем его по ID
    response = await client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id

@pytest.mark.asyncio
async def test_update_item(client: AsyncClient):
    # Сначала создаем товар
    item_id = await test_create_item(client)
    # Затем обновляем его
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
    # Сначала создаем товар
    item_id = await test_create_item(client)
    # Затем удаляем его
    response = await client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 204
    # Проверяем, что товар действительно удален
    response = await client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 404

# Тесты для работы с категориями
@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    category_data = {
        "name": "Смартфоны",
        "description": "Категория для смартфонов"
    }
    response = await client.post("/api/v1/categories/", json=category_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == category_data["name"]
    return data["id"]

@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient):
    response = await client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# Тест для проверки метрик Prometheus
@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    response = await client.get("/api/metrics")
    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text 