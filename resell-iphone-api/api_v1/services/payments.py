from fastapi import Request, Response, HTTPException
from yookassa import Configuration
import json
from typing import Dict, Any
import logging
from api_v1.services.orders import update_order
from core.models.orders import OrderUpdateModel

logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    async def handle_webhook(request: Request) -> Response:
        """
        Обработчик уведомлений от ЮKassa.
        
        Args:
            request (Request): Запрос от ЮKassa с данными о платеже
            
        Returns:
            Response: Ответ со статусом 200 OK
        """
        try:
            # Получаем данные из запроса
            data = await request.json()
            
            # Логируем полученные данные
            logger.info(f"Получено уведомление от ЮKassa: {json.dumps(data, indent=2)}")
            
            # Проверяем тип события
            if data.get("event") == "payment.succeeded":
                # Обработка успешного платежа
                payment_id = data.get("object", {}).get("id")
                order_id = data.get("object", {}).get("metadata", {}).get("order_id")
                
                if not order_id:
                    logger.error("Order ID not found in payment metadata")
                    raise HTTPException(status_code=400, detail="Order ID not found in payment metadata")
                
                try:
                    # Обновляем статус заказа на PAID
                    update_data = OrderUpdateModel(status="PAID")
                    await update_order(int(order_id), update_data)
                    logger.info(f"Заказ {order_id} помечен как оплаченный")
                except Exception as e:
                    logger.error(f"Error updating order status: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")
                
            elif data.get("event") == "payment.canceled":
                # Обработка отмененного платежа
                payment_id = data.get("object", {}).get("id")
                logger.info(f"Платеж {payment_id} отменен")
            
            # Возвращаем 200 OK для подтверждения получения уведомления
            return Response(status_code=200)
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 