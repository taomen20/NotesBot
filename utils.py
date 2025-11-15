"""Вспомогательные функции."""
import re
from config import Config


def validate_name(name: str) -> tuple[bool, str]:
    """
    Валидация имени.
    Возвращает (is_valid, error_message).
    """
    if not name or not name.strip():
        return False, "Имя не может быть пустым"
    
    name = name.strip()
    
    if len(name) > 100:
        return False, "Имя слишком длинное (максимум 100 символов)"
    
    # Разрешаем только буквы, пробелы, дефисы и апострофы
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-\']+$', name):
        return False, "Имя содержит недопустимые символы"
    
    return True, ""


def validate_names_list(names: list[str]) -> tuple[bool, str]:
    """
    Валидация списка имен.
    Возвращает (is_valid, error_message).
    """
    if not names:
        return False, "Список имен не может быть пустым"
    
    if len(names) > Config.MAX_NAMES_PER_NOTE:
        return False, f"Максимальное количество имен: {Config.MAX_NAMES_PER_NOTE}"
    
    for name in names:
        is_valid, error = validate_name(name)
        if not is_valid:
            return False, f"Ошибка в имени '{name}': {error}"
    
    return True, ""


def validate_amount(amount: float) -> tuple[bool, str]:
    """
    Валидация суммы пожертвования.
    Возвращает (is_valid, error_message).
    """
    if amount < Config.MIN_DONATION_AMOUNT:
        return False, f"Минимальная сумма пожертвования: {Config.MIN_DONATION_AMOUNT:.2f} руб."
    
    if amount > 1000000:
        return False, "Сумма слишком большая"
    
    return True, ""


def format_note_text(note_type: str, names_for_health: list[str], names_for_repose: list[str]) -> str:
    """Форматирование текста записки для отображения."""
    text = f"📝 <b>Записка: {note_type}</b>\n\n"
    
    if names_for_health:
        text += "🙏 <b>За здравие:</b>\n"
        for i, name in enumerate(names_for_health, 1):
            text += f"{i}. {name}\n"
        text += "\n"
    
    if names_for_repose:
        text += "🕯️ <b>Об упокоении:</b>\n"
        for i, name in enumerate(names_for_repose, 1):
            text += f"{i}. {name}\n"
    
    return text


def format_prayer_text(note_type: str, names: list[str]) -> str:
    """Форматирование молитвы для прочтения."""
    if note_type == "for_health":
        prayer_type = "За здравие"
        emoji = "🙏"
    else:
        prayer_type = "Об упокоении"
        emoji = "🕯️"
    
    text = f"{emoji} <b>Молитва {prayer_type}</b>\n\n"
    text += "Господи, помилуй и спаси рабов Твоих:\n\n"
    
    for i, name in enumerate(names, 1):
        text += f"{i}. {name}\n"
    
    text += "\nАминь."
    
    return text

