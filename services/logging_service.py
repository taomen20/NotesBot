"""Сервис логирования операций без персональных данных."""
import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import Config


class OperationLogger:
    """Логгер для операций системы без персональных данных."""
    
    def __init__(self):
        """Инициализация логгера."""
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("operations")
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Очистка существующих обработчиков
        self.logger.handlers.clear()
        
        # Файловый обработчик с ротацией
        log_file = self.log_dir / "operations.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        
        # Формат логов
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def log_note_created(self, note_id: int, note_type: str, names_count: int, amount: float):
        """Логирование создания записки."""
        self.logger.info(
            f"Note created: id={note_id}, type={note_type}, "
            f"names_count={names_count}, amount={amount:.2f}"
        )
    
    def log_payment_created(self, note_id: int, payment_id: str, amount: float):
        """Логирование создания платежа."""
        self.logger.info(
            f"Payment created: note_id={note_id}, payment_id={payment_id}, "
            f"amount={amount:.2f}"
        )
    
    def log_payment_status(self, payment_id: str, status: str, amount: float):
        """Логирование изменения статуса платежа."""
        self.logger.info(
            f"Payment status: payment_id={payment_id}, status={status}, "
            f"amount={amount:.2f}"
        )
    
    def log_note_read(self, note_id: int, note_type: str, reader_role: str):
        """Логирование прочтения записки."""
        self.logger.info(
            f"Note read: note_id={note_id}, type={note_type}, "
            f"reader_role={reader_role}, timestamp={datetime.now().isoformat()}"
        )
    
    def log_role_changed(self, user_id: int, old_role: str, new_role: str):
        """Логирование изменения роли пользователя."""
        self.logger.info(
            f"Role changed: user_id={user_id}, old_role={old_role}, "
            f"new_role={new_role}"
        )
    
    def log_error(self, operation: str, error: str):
        """Логирование ошибки."""
        self.logger.error(f"Error in {operation}: {error}")


# Глобальный экземпляр логгера
operation_logger = OperationLogger()

