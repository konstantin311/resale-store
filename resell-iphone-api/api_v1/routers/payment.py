from fastapi import APIRouter, Depends, HTTPException, status, Request
from core.models.payment import PaymentCreate, PaymentResponse, PaymentStatus
from api_v1.services.payment import create_payment, get_payment, update_payment_status
from core.logger import logger

router = APIRouter(
    prefix="/payments",
    tags=["Платежи"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Платеж не найден"},
        status.HTTP_400_BAD_REQUEST: {"description": "Неверные данные запроса"},
    },
)

@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый платеж",
    description="""
    Создает новый платеж в ЮКассе и сохраняет его в базе данных.
    
    Параметры:
    - amount: Сумма платежа
    - description: Описание платежа
    - metadata: Дополнительные метаданные (опционально)
    
    Возвращает:
    - Информацию о созданном платеже, включая URL для оплаты
    """
)
async def create_new_payment(payment_data: PaymentCreate):
    """
    Создает новый платеж.
    """
    return await create_payment(payment_data)

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Получить информацию о платеже",
    description="Получает информацию о платеже по его ID"
)
async def get_payment_by_id(payment_id: str):
    """
    Получает информацию о платеже.
    """
    return await get_payment(payment_id)

@router.post(
    "/webhook",
    summary="Webhook для уведомлений от ЮКассы",
    description="""
    Эндпоинт для получения уведомлений от ЮКассы о статусе платежа.
    Должен быть указан в настройках ЮКассы как URL для уведомлений.
    """
)
async def payment_webhook(request: Request):
    """
    Обрабатывает уведомления от ЮКассы.
    """
    try:
        # Получаем тело запроса
        notification = await request.json()
        
        # Проверяем тип уведомления
        if notification.get("event") != "payment.succeeded":
            return {"status": "ignored"}
        
        # Получаем ID платежа
        payment_id = notification["object"]["id"]
        
        # Обновляем статус платежа
        await update_payment_status(payment_id, PaymentStatus.SUCCEEDED)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing payment notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 