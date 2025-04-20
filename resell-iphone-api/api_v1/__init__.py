from fastapi import APIRouter

from api_v1.routers import items, categories, users, orders, statistics

router = APIRouter()

router.include_router(items.router, prefix="/items")
router.include_router(categories.router, prefix="/categories")
router.include_router(users.router, prefix="/users")
router.include_router(orders.router, prefix="/orders")
router.include_router(statistics.router, prefix="/statistics")
