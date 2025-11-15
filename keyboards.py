"""Клавиатуры для Telegram бота."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from models import NoteType


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для обычных пользователей."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Создать записку")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_note_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа записки."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="За здравие",
                    callback_data="note_type:for_health"
                ),
                InlineKeyboardButton(
                    text="Об упокоении",
                    callback_data="note_type:for_repose"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
    )
    return keyboard


def get_priest_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для священника/алтарника."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика очереди")],
            [KeyboardButton(text="📖 Прочитать записку")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_priest_note_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа записки для прочтения."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="За здравие",
                    callback_data="read_note:for_health"
                ),
                InlineKeyboardButton(
                    text="Об упокоении",
                    callback_data="read_note:for_repose"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )
    return keyboard


def get_note_actions_keyboard(note_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с запиской."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить прочтение",
                    callback_data=f"confirm_read:{note_id}"
                )
            ],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
        ]
    )
    return keyboard


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для администратора."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="👥 Управление ролями")],
            [KeyboardButton(text="📈 Активность")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    return keyboard

