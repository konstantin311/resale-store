from fastapi import APIRouter, Request
from api_v1.services.payments import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/yookassa/webhook",
    summary="Эндпоинт для получения уведомлений от ЮKassa",
    description="""
    Этот эндпоинт принимает уведомления от ЮKassa о статусе платежей.
    
    Поддерживаемые события:
    - payment.succeeded - успешный платеж
    - payment.canceled - отмененный платеж
    
    Эндпоинт всегда возвращает статус 200 OK для подтверждения получения уведомления.
    """,
    response_description="Подтверждение получения уведомления",
    status_code=200
)
async def yookassa_webhook(request: Request):
    return await PaymentService.handle_webhook(request) 