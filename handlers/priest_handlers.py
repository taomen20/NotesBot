"""Обработчики для священника/алтарника."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import db
from models import NoteType, UserRole
from services.user_service import UserService
from services.note_service import NoteService
from keyboards import (
    get_priest_main_keyboard,
    get_priest_note_type_keyboard,
    get_note_actions_keyboard
)
from utils import format_prayer_text


router = Router()


def check_priest_access(func):
    """Декоратор для проверки доступа священника/алтарника."""
    async def wrapper(message: Message, *args, **kwargs):
        async with db.get_session() as session:
            is_priest = await UserService.is_priest_or_altar_server(
                session,
                message.from_user.id
            )
            if not is_priest:
                await message.answer("❌ У вас нет доступа к этой функции.")
                return
            return await func(message, *args, **kwargs)
    return wrapper


@router.message(Command("start"))
async def cmd_start_priest(message: Message):
    """Обработчик команды /start для священника."""
    async with db.get_session() as session:
        is_priest = await UserService.is_priest_or_altar_server(
            session,
            message.from_user.id
        )
        if is_priest:
            await message.answer(
                "Добро пожаловать! Вы вошли как священник/алтарник.\n\n"
                "Используйте кнопки меню для работы с записками.",
                reply_markup=get_priest_main_keyboard()
            )


@router.message(F.text == "📊 Статистика очереди")
@check_priest_access
async def show_queue_stats(message: Message):
    """Показать статистику очереди."""
    async with db.get_session() as session:
        total_count = await NoteService.get_queue_count(session)
        health_count = await NoteService.get_queue_count(session, NoteType.FOR_HEALTH)
        repose_count = await NoteService.get_queue_count(session, NoteType.FOR_REPOSE)
        
        stats_text = (
            "📊 <b>Статистика очереди</b>\n\n"
            f"Всего записок: {total_count}\n"
            f"За здравие: {health_count}\n"
            f"Об упокоении: {repose_count}"
        )
        
        await message.answer(stats_text, parse_mode="HTML")


@router.message(F.text == "📖 Прочитать записку")
@check_priest_access
async def start_read_note(message: Message):
    """Начать чтение записки."""
    async with db.get_session() as session:
        total_count = await NoteService.get_queue_count(session)
        
        if total_count == 0:
            await message.answer("📭 В очереди нет записок.")
            return
        
        await message.answer(
            "Выберите тип записки для прочтения:",
            reply_markup=get_priest_note_type_keyboard()
        )


@router.callback_query(F.data.startswith("read_note:"))
async def read_note(callback: CallbackQuery):
    """Прочитать записку."""
    async with db.get_session() as session:
        is_priest = await UserService.is_priest_or_altar_server(
            session,
            callback.from_user.id
        )
        if not is_priest:
            await callback.answer("❌ У вас нет доступа.", show_alert=True)
            return
        
        note_type_str = callback.data.split(":")[1]
        note_type = NoteType(note_type_str)
        
        # Получаем следующую записку из очереди
        note = await NoteService.get_next_note(session, note_type)
        
        if not note:
            note_type_name = "За здравие" if note_type == NoteType.FOR_HEALTH else "Об упокоении"
            await callback.message.edit_text(
                f"📭 Нет записок типа '{note_type_name}' в очереди."
            )
            return
        
        # Разделяем имена по типам
        names_for_health = [n.name for n in note.names if n.list_type == NoteType.FOR_HEALTH]
        names_for_repose = [n.name for n in note.names if n.list_type == NoteType.FOR_REPOSE]
        
        # Формируем текст молитвы
        prayer_text = ""
        
        if names_for_health:
            prayer_text += format_prayer_text("for_health", names_for_health)
            prayer_text += "\n\n"
        
        if names_for_repose:
            prayer_text += format_prayer_text("for_repose", names_for_repose)
        
        # Сохраняем ID записки для подтверждения
        await callback.message.edit_text(
            prayer_text,
            parse_mode="HTML",
            reply_markup=get_note_actions_keyboard(note.id)
        )
        
        await callback.answer()


@router.callback_query(F.data.startswith("confirm_read:"))
async def confirm_read_note(callback: CallbackQuery):
    """Подтвердить прочтение записки."""
    async with db.get_session() as session:
        is_priest = await UserService.is_priest_or_altar_server(
            session,
            callback.from_user.id
        )
        if not is_priest:
            await callback.answer("❌ У вас нет доступа.", show_alert=True)
            return
        
        note_id = int(callback.data.split(":")[1])
        
        # Получаем записку
        note = await NoteService.get_note_with_names(session, note_id)
        if not note:
            await callback.answer("❌ Записка не найдена.", show_alert=True)
            return
        
        user = note.user
        
        # Получаем роль читающего
        reader = await UserService.get_user_by_telegram_id(session, callback.from_user.id)
        reader_role = reader.role.value if reader else "unknown"
        
        # Отмечаем как прочитанную
        await NoteService.mark_note_as_read(session, note_id, reader_role)
        
        # Отправляем уведомление пользователю
        from aiogram import Bot
        from config import Config
        bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"✅ Ваша записка прочитана на богослужении.\n\n"
                f"Тип: {'За здравие' if note.type == NoteType.FOR_HEALTH else 'Об упокоении'}\n"
                f"Дата прочтения: {note.read_at.strftime('%d.%m.%Y %H:%M') if note.read_at else 'Не указано'}"
            )
        except Exception as e:
            # Если не удалось отправить уведомление, логируем, но продолжаем
            pass
        
        # Удаляем записку
        await NoteService.delete_note(session, note_id)
        
        await callback.message.edit_text(
            "✅ Записка прочитана и удалена из системы.\n"
            "Пользователю отправлено уведомление."
        )
        await callback.answer("Записка прочитана")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню."""
    await callback.message.edit_text(
        "Главное меню",
        reply_markup=None
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_priest_main_keyboard()
    )
    await callback.answer()

