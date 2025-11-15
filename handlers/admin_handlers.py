"""Обработчики для администратора."""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database import db
from models import UserRole
from services.user_service import UserService
from services.note_service import NoteService
from keyboards import get_admin_main_keyboard, get_cancel_keyboard


router = Router()


class AdminStates(StatesGroup):
    """Состояния для административных действий."""
    waiting_for_user_id = State()
    waiting_for_role = State()


def check_admin_access(func):
    """Декоратор для проверки доступа администратора."""
    async def wrapper(message: Message, *args, **kwargs):
        async with db.get_session() as session:
            is_admin = await UserService.is_admin(session, message.from_user.id)
            if not is_admin:
                await message.answer("❌ У вас нет доступа к этой функции.")
                return
            return await func(message, *args, **kwargs)
    return wrapper


@router.message(Command("start"))
async def cmd_start_admin(message: Message):
    """Обработчик команды /start для администратора."""
    async with db.get_session() as session:
        is_admin = await UserService.is_admin(session, message.from_user.id)
        if is_admin:
            await message.answer(
                "Добро пожаловать! Вы вошли как администратор.\n\n"
                "Используйте кнопки меню для управления системой.",
                reply_markup=get_admin_main_keyboard()
            )


@router.message(F.text == "📊 Статистика")
@check_admin_access
async def show_statistics(message: Message):
    """Показать статистику системы."""
    async with db.get_session() as session:
        queue_count = await NoteService.get_queue_count(session)
        
        # Получаем количество пользователей по ролям
        users = await UserService.get_users_by_role(session, UserRole.USER)
        priests = await UserService.get_users_by_role(session, UserRole.PRIEST)
        altar_servers = await UserService.get_users_by_role(session, UserRole.ALTAR_SERVER)
        admins = await UserService.get_users_by_role(session, UserRole.ADMIN)
        
        stats_text = (
            "📊 <b>Статистика системы</b>\n\n"
            f"📝 Записок в очереди: {queue_count}\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"Обычные пользователи: {len(users)}\n"
            f"Священники: {len(priests)}\n"
            f"Алтарники: {len(altar_servers)}\n"
            f"Администраторы: {len(admins)}"
        )
        
        await message.answer(stats_text, parse_mode="HTML")


@router.message(F.text == "👥 Управление ролями")
@check_admin_access
async def start_manage_roles(message: Message, state: FSMContext):
    """Начать управление ролями."""
    await message.answer(
        "Введите Telegram ID пользователя, роль которого хотите изменить:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(StateFilter(AdminStates.waiting_for_user_id))
@check_admin_access
async def process_user_id(message: Message, state: FSMContext):
    """Обработка Telegram ID пользователя."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_admin_main_keyboard())
        return
    
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный Telegram ID (число).")
        return
    
    async with db.get_session() as session:
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        if not user:
            await message.answer("❌ Пользователь с таким ID не найден.")
            return
        
        await state.update_data(telegram_id=telegram_id, current_role=user.role.value)
        
        roles_text = (
            f"Текущая роль пользователя: <b>{user.role.value}</b>\n\n"
            "Выберите новую роль:\n"
            "1. user - Обычный пользователь\n"
            "2. priest - Священник\n"
            "3. altar_server - Алтарник\n"
            "4. admin - Администратор\n\n"
            "Отправьте номер или название роли:"
        )
        
        await message.answer(roles_text, parse_mode="HTML")
        await state.set_state(AdminStates.waiting_for_role)


@router.message(StateFilter(AdminStates.waiting_for_role))
@check_admin_access
async def process_role(message: Message, state: FSMContext):
    """Обработка выбора роли."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=get_admin_main_keyboard())
        return
    
    data = await state.get_data()
    telegram_id = data.get("telegram_id")
    
    # Парсинг роли
    role_mapping = {
        "1": UserRole.USER,
        "2": UserRole.PRIEST,
        "3": UserRole.ALTAR_SERVER,
        "4": UserRole.ADMIN,
        "user": UserRole.USER,
        "priest": UserRole.PRIEST,
        "altar_server": UserRole.ALTAR_SERVER,
        "admin": UserRole.ADMIN,
    }
    
    role = role_mapping.get(message.text.lower())
    if not role:
        await message.answer("❌ Неверная роль. Попробуйте снова.")
        return
    
    async with db.get_session() as session:
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        if not user:
            await message.answer("❌ Пользователь не найден.")
            await state.clear()
            return
        
        success = await UserService.update_user_role(session, user.id, role)
        
        if success:
            await message.answer(
                f"✅ Роль пользователя изменена на: <b>{role.value}</b>",
                parse_mode="HTML",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при изменении роли.",
                reply_markup=get_admin_main_keyboard()
            )
    
    await state.clear()


@router.message(F.text == "📈 Активность")
@check_admin_access
async def show_activity(message: Message):
    """Показать активность священников/алтарников."""
    async with db.get_session() as session:
        priests = await UserService.get_users_by_role(session, UserRole.PRIEST)
        altar_servers = await UserService.get_users_by_role(session, UserRole.ALTAR_SERVER)
        
        activity_text = "📈 <b>Активность священников и алтарников</b>\n\n"
        
        if not priests and not altar_servers:
            activity_text += "Нет назначенных священников или алтарников."
        else:
            # Здесь можно добавить логику получения последней активности
            # Пока просто показываем список
            if priests:
                activity_text += "🙏 <b>Священники:</b>\n"
                for priest in priests:
                    username = priest.username or f"ID: {priest.telegram_id}"
                    activity_text += f"• {username}\n"
                activity_text += "\n"
            
            if altar_servers:
                activity_text += "🕯️ <b>Алтарники:</b>\n"
                for altar in altar_servers:
                    username = altar.username or f"ID: {altar.telegram_id}"
                    activity_text += f"• {username}\n"
        
        await message.answer(activity_text, parse_mode="HTML")


@router.message(F.text == "⚙️ Настройки")
@check_admin_access
async def show_settings(message: Message):
    """Показать настройки системы."""
    from config import Config
    
    settings_text = (
        "⚙️ <b>Настройки системы</b>\n\n"
        f"Минимальная сумма пожертвования: {Config.MIN_DONATION_AMOUNT:.2f} руб.\n"
        f"Максимальное количество имен: {Config.MAX_NAMES_PER_NOTE}\n"
        f"Описание платежа: {Config.PAYMENT_DESCRIPTION}"
    )
    
    await message.answer(settings_text, parse_mode="HTML")

