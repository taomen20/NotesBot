"""Главный файл приложения."""
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import Config
from database import db
from handlers import user_handlers, priest_handlers, admin_handlers
from services.payment_service import PaymentService
from services.note_service import NoteService


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Действия при запуске бота."""
    logger.info("Бот запускается...")
    
    # Инициализация БД
    await db.init_db()
    logger.info("База данных инициализирована")
    
    # Настройка webhook
    if Config.TELEGRAM_WEBHOOK_URL:
        webhook_url = f"{Config.TELEGRAM_WEBHOOK_URL}{Config.TELEGRAM_WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")
    else:
        logger.warning("TELEGRAM_WEBHOOK_URL не установлен, webhook не настроен")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота."""
    logger.info("Бот останавливается...")
    await bot.session.close()
    await db.close()


async def yookassa_webhook_handler(request: web.Request):
    """Обработчик webhook от Яндекс.Кассы."""
    try:
        data = await request.json()
        logger.info(f"Получен webhook от Яндекс.Кассы: {data}")
        
        payment_service = PaymentService()
        result = payment_service.process_webhook(data)
        
        if not result:
            return web.Response(status=400, text="Invalid webhook data")
        
        payment_id = result["payment_id"]
        status = result["status"]
        note_id = result.get("note_id")
        
        # Если платеж успешен, обновляем статус записки
        if status == "succeeded" and note_id:
            async with db.get_session() as session:
                note = await NoteService.get_note_by_payment_id(session, payment_id)
                if note and note.status.value == "pending":
                    await NoteService.update_note_payment(session, note.id, payment_id)
                    logger.info(f"Записка {note_id} помечена как оплаченная")
        
        return web.Response(status=200, text="OK")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook от Яндекс.Кассы: {e}")
        return web.Response(status=500, text="Internal server error")


def create_app() -> web.Application:
    """Создание приложения aiohttp."""
    # Валидация конфигурации
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        raise
    
    # Инициализация бота и диспетчера
    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(user_handlers.router)
    dp.include_router(priest_handlers.router)
    dp.include_router(admin_handlers.router)
    
    # Создание приложения aiohttp
    app = web.Application()
    
    # Настройка webhook для Telegram
    if Config.TELEGRAM_WEBHOOK_URL:
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=Config.TELEGRAM_WEBHOOK_PATH)
    
    # Обработчик webhook от Яндекс.Кассы
    app.router.add_post("/yookassa-webhook", yookassa_webhook_handler)
    
    # Настройка приложения
    setup_application(app, dp, bot=bot)
    
    # Обработчики запуска и остановки
    app.on_startup.append(lambda app: on_startup(bot))
    app.on_shutdown.append(lambda app: on_shutdown(bot))
    
    return app


async def main():
    """Главная функция."""
    app = create_app()
    
    # Запуск сервера
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, Config.HOST, Config.PORT)
    await site.start()
    
    logger.info(f"Сервер запущен на {Config.HOST}:{Config.PORT}")
    
    # Ожидание бесконечно
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено")

