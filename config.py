"""Конфигурация приложения."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс для хранения конфигурации приложения."""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: Optional[str] = os.getenv("TELEGRAM_WEBHOOK_URL")
    TELEGRAM_WEBHOOK_PATH: str = os.getenv("TELEGRAM_WEBHOOK_PATH", "/webhook")
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/notesbot_db"
    )
    
    # YooKassa
    YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID", "")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY", "")
    YOOKASSA_WEBHOOK_URL: Optional[str] = os.getenv("YOOKASSA_WEBHOOK_URL")
    
    # Payment Settings
    MIN_DONATION_AMOUNT: float = float(os.getenv("MIN_DONATION_AMOUNT", "100.0"))
    PAYMENT_DESCRIPTION: str = os.getenv("PAYMENT_DESCRIPTION", "Пожертвование")
    
    # Application Settings
    MAX_NAMES_PER_NOTE: int = int(os.getenv("MAX_NAMES_PER_NOTE", "10"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка обязательных параметров конфигурации."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        if not cls.YOOKASSA_SHOP_ID:
            raise ValueError("YOOKASSA_SHOP_ID не установлен")
        if not cls.YOOKASSA_SECRET_KEY:
            raise ValueError("YOOKASSA_SECRET_KEY не установлен")
        return True

