"""Обработчики для обычных пользователей."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database import db
from models import NoteType, UserRole
from services.user_service import UserService
from services.note_service import NoteService
from services.payment_service import PaymentService
from keyboards import (
    get_main_menu_keyboard,
    get_note_type_keyboard,
    get_cancel_keyboard
)
from utils import validate_names_list, validate_amount, format_note_text
from config import Config


router = Router()


class CreateNoteStates(StatesGroup):
    """Состояния для создания записки."""
    waiting_for_type = State()
    waiting_for_health_names = State()
    waiting_for_repose_names = State()
    waiting_for_amount = State()
    confirming = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    await state.clear()
    
    async with db.get_session() as session:
        user = await UserService.get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.username
        )
        
        # Определяем клавиатуру в зависимости от роли
        if user.role == UserRole.ADMIN:
            from keyboards import get_admin_main_keyboard
            keyboard = get_admin_main_keyboard()
        elif user.role in (UserRole.PRIEST, UserRole.ALTAR_SERVER):
            from keyboards import get_priest_main_keyboard
            keyboard = get_priest_main_keyboard()
        else:
            keyboard = get_main_menu_keyboard()
        
        await message.answer(
            "Добро пожаловать! Я помогу вам отправить записку на молитву.\n\n"
            "Используйте кнопки меню для навигации.",
            reply_markup=keyboard
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    help_text = (
        "📖 <b>Помощь</b>\n\n"
        "Для создания записки:\n"
        "1. Нажмите 'Создать записку'\n"
        "2. Выберите тип записки\n"
        "3. Введите имена (по одному на строку)\n"
        "4. Укажите сумму пожертвования\n"
        "5. Подтвердите и перейдите к оплате\n\n"
        f"Максимальное количество имен: {Config.MAX_NAMES_PER_NOTE}\n"
        f"Минимальная сумма: {Config.MIN_DONATION_AMOUNT:.2f} руб."
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "📝 Создать записку")
async def start_create_note(message: Message, state: FSMContext):
    """Начать создание записки."""
    await state.set_state(CreateNoteStates.waiting_for_type)
    await message.answer(
        "Выберите тип записки:",
        reply_markup=get_note_type_keyboard()
    )


@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    """Отменить текущее действие."""
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data.startswith("note_type:"), StateFilter(CreateNoteStates.waiting_for_type))
async def process_note_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа записки."""
    note_type = callback.data.split(":")[1]
    await state.update_data(note_type=note_type, health_names=[], repose_names=[])
    
    await callback.message.edit_text(
        "Введите имена для молитвы <b>За здравие</b>.\n"
        "По одному имени на строку.\n"
        "Когда закончите, отправьте 'Готово' или 'Далее'.",
        parse_mode="HTML"
    )
    await state.set_state(CreateNoteStates.waiting_for_health_names)


@router.message(StateFilter(CreateNoteStates.waiting_for_health_names))
async def process_health_names(message: Message, state: FSMContext):
    """Обработка имен для молитвы за здравие."""
    if message.text.lower() in ("готово", "далее", "пропустить"):
        data = await state.get_data()
        health_names = data.get("health_names", [])
        
        await message.answer(
            "Введите имена для молитвы <b>Об упокоении</b>.\n"
            "По одному имени на строку.\n"
            "Когда закончите, отправьте 'Готово' или 'Далее'.\n"
            "Если не нужно, отправьте 'Пропустить'.",
            parse_mode="HTML"
        )
        await state.set_state(CreateNoteStates.waiting_for_repose_names)
        return
    
    data = await state.get_data()
    health_names = data.get("health_names", [])
    
    # Парсинг имен из сообщения
    new_names = [name.strip() for name in message.text.split("\n") if name.strip()]
    
    all_names = health_names + new_names
    
    is_valid, error = validate_names_list(all_names)
    if not is_valid:
        await message.answer(f"❌ {error}")
        return
    
    await state.update_data(health_names=all_names)
    await message.answer(
        f"✅ Добавлено имен: {len(all_names)}\n"
        f"Отправьте 'Готово' или 'Далее' для продолжения."
    )


@router.message(StateFilter(CreateNoteStates.waiting_for_repose_names))
async def process_repose_names(message: Message, state: FSMContext):
    """Обработка имен для молитвы об упокоении."""
    if message.text.lower() in ("готово", "далее", "пропустить"):
        data = await state.get_data()
        health_names = data.get("health_names", [])
        repose_names = data.get("repose_names", [])
        
        if not health_names and not repose_names:
            await message.answer("❌ Необходимо указать хотя бы одно имя.")
            return
        
        await message.answer(
            f"Введите сумму пожертвования (минимум {Config.MIN_DONATION_AMOUNT:.2f} руб.):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(CreateNoteStates.waiting_for_amount)
        return
    
    data = await state.get_data()
    repose_names = data.get("repose_names", [])
    health_names = data.get("health_names", [])
    
    # Парсинг имен из сообщения
    new_names = [name.strip() for name in message.text.split("\n") if name.strip()]
    
    all_names = repose_names + new_names
    total_names = len(health_names) + len(all_names)
    
    if total_names > Config.MAX_NAMES_PER_NOTE:
        await message.answer(
            f"❌ Превышено максимальное количество имен: {Config.MAX_NAMES_PER_NOTE}"
        )
        return
    
    is_valid, error = validate_names_list(all_names)
    if not is_valid:
        await message.answer(f"❌ {error}")
        return
    
    await state.update_data(repose_names=all_names)
    await message.answer(
        f"✅ Добавлено имен: {len(all_names)}\n"
        f"Отправьте 'Готово' или 'Далее' для продолжения."
    )


@router.message(StateFilter(CreateNoteStates.waiting_for_amount))
async def process_amount(message: Message, state: FSMContext):
    """Обработка суммы пожертвования."""
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число.")
        return
    
    is_valid, error = validate_amount(amount)
    if not is_valid:
        await message.answer(f"❌ {error}")
        return
    
    data = await state.get_data()
    health_names = data.get("health_names", [])
    repose_names = data.get("repose_names", [])
    note_type = data.get("note_type")
    
    # Определяем тип записки на основе наличия имен
    if health_names and repose_names:
        # Если есть оба типа, используем выбранный тип как основной
        pass
    elif health_names:
        note_type = "for_health"
    elif repose_names:
        note_type = "for_repose"
    
    note_text = format_note_text(note_type, health_names, repose_names)
    note_text += f"\n💰 Сумма пожертвования: {amount:.2f} руб."
    
    await state.update_data(amount=amount, note_type=note_type)
    await message.answer(
        f"{note_text}\n\nПодтвердите создание записки:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await state.set_state(CreateNoteStates.confirming)


@router.message(StateFilter(CreateNoteStates.confirming))
async def confirm_note(message: Message, state: FSMContext):
    """Подтверждение и создание записки."""
    if message.text.lower() not in ("подтвердить", "да", "создать", "готово"):
        await message.answer("Для подтверждения отправьте 'Подтвердить' или 'Да'.")
        return
    
    data = await state.get_data()
    health_names = data.get("health_names", [])
    repose_names = data.get("repose_names", [])
    amount = data.get("amount")
    note_type_str = data.get("note_type")
    
    async with db.get_session() as session:
        user = await UserService.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("❌ Ошибка: пользователь не найден.")
            await state.clear()
            return
        
        note_type = NoteType(note_type_str)
        
        # Создаем записку
        note = await NoteService.create_note(
            session,
            user.id,
            note_type,
            health_names,
            repose_names,
            amount
        )
        
        # Создаем платеж
        payment_service = PaymentService()
        return_url = f"{Config.TELEGRAM_WEBHOOK_URL}/payment-success"
        
        try:
            payment = payment_service.create_payment(
                amount,
                note.id,
                user.id,
                return_url
            )
            
            # Сохраняем ID платежа
            await NoteService.update_note_payment(session, note.id, payment.id)
            
            # Отправляем ссылку на оплату
            if payment.confirmation and payment.confirmation.confirmation_url:
                await message.answer(
                    f"✅ Записка создана!\n\n"
                    f"Перейдите по ссылке для оплаты:\n"
                    f"{payment.confirmation.confirmation_url}",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await message.answer(
                    "✅ Записка создана, но произошла ошибка при создании платежа. "
                    "Пожалуйста, обратитесь к администратору.",
                    reply_markup=get_main_menu_keyboard()
                )
        
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при создании платежа: {str(e)}\n"
                "Пожалуйста, попробуйте позже или обратитесь к администратору.",
                reply_markup=get_main_menu_keyboard()
            )
    
    await state.clear()

