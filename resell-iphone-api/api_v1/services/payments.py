from fastapi import Request, Response
from yookassa import Configuration
import json
from typing import Dict, Any

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
        # Получаем данные из запроса
        data = await request.json()
        
        # Логируем полученные данные (для демонстрации)
        print(f"Получено уведомление от ЮKassa: {json.dumps(data, indent=2)}")
        
        # Проверяем тип события
        if data.get("event") == "payment.succeeded":
            # Обработка успешного платежа
            payment_id = data.get("object", {}).get("id")
            print(f"Платеж {payment_id} успешно выполнен")
            
        elif data.get("event") == "payment.canceled":
            # Обработка отмененного платежа
            payment_id = data.get("object", {}).get("id")
            print(f"Платеж {payment_id} отменен")
        
        # Возвращаем 200 OK для подтверждения получения уведомления
        return Response(status_code=200) 