"""Сервис для интеграции с Яндекс.Кассой."""
from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotificationFactory
from yookassa.domain.response import PaymentResponse
from config import Config
from services.logging_service import operation_logger


class PaymentService:
    """Сервис для работы с платежами через Яндекс.Кассу."""
    
    def __init__(self):
        """Инициализация сервиса платежей."""
        Configuration.account_id = Config.YOOKASSA_SHOP_ID
        Configuration.secret_key = Config.YOOKASSA_SECRET_KEY
    
    def create_payment(
        self,
        amount: float,
        note_id: int,
        user_id: int,
        return_url: str
    ) -> PaymentResponse:
        """Создать платеж в Яндекс.Кассе."""
        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": Config.PAYMENT_DESCRIPTION,
            "metadata": {
                "note_id": str(note_id),
                "user_id": str(user_id)
            }
        }, str(note_id))
        
        operation_logger.log_payment_created(
            note_id=note_id,
            payment_id=payment.id,
            amount=amount
        )
        
        return payment
    
    def process_webhook(self, request_body: dict) -> dict | None:
        """Обработать webhook от Яндекс.Кассы."""
        try:
            notification = WebhookNotificationFactory().create(request_body)
            payment_object = notification.object
            
            payment_id = payment_object.id
            status = payment_object.status
            amount = float(payment_object.amount.value)
            
            operation_logger.log_payment_status(
                payment_id=payment_id,
                status=status,
                amount=amount
            )
            
            metadata = payment_object.metadata or {}
            note_id = metadata.get("note_id")
            
            return {
                "payment_id": payment_id,
                "status": status,
                "amount": amount,
                "note_id": note_id
            }
        except Exception as e:
            operation_logger.log_error("webhook_processing", str(e))
            return None
    
    def get_payment_status(self, payment_id: str) -> dict | None:
        """Получить статус платежа."""
        try:
            payment = Payment.find_one(payment_id)
            return {
                "id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "paid": payment.paid
            }
        except Exception as e:
            operation_logger.log_error("get_payment_status", str(e))
            return None

