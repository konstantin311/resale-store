from fastapi import APIRouter

from api_v1.services import statistics
from core.models.statistics import StatisticsResponse

router = APIRouter(tags=["Статистика"])


@router.get(
    "/",
    response_model=StatisticsResponse,
    summary="Получить статистику магазина",
    description="""
    Получает полную статистику магазина.
    
    - Общее количество пользователей и их распределение по ролям
    - Количество активных продавцов и покупателей
    - Статистика заказов за разные периоды
    - Финансовая статистика за разные периоды
    """,
    responses={
        200: {
            "description": "Статистика успешно получена",
            "content": {
                "application/json": {
                    "example": {
                        "total_users": 100,
                        "total_sellers": 30,
                        "total_buyers": 70,
                        "active_sellers": 25,
                        "active_buyers": 60,
                        "total_orders": 500,
                        "year_orders": 200,
                        "month_orders": 50,
                        "total_profit": 100000.00,
                        "year_profit": 40000.00,
                        "month_profit": 10000.00
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error"
                    }
                }
            }
        }
    }
)
async def get_statistics():
    """
    Получает полную статистику магазина.
    
    Returns:
        StatisticsResponse: Объект со статистикой магазина
        
    Raises:
        HTTPException: 500 при внутренней ошибке сервера
    """
    return await statistics.get_statistics() 