# NotesBot - Чат-бот для отправки записок на молитву

Telegram-бот для отправки записок на молитву во время богослужений с интеграцией платежного шлюза Яндекс.Касса.

## Возможности

- **Для пользователей:**
  - Создание записок "За здравие" и "Об упокоении"
  - Ввод списка имен с валидацией
  - Оплата через Яндекс.Кассу (карты МИР, СБП)
  - Получение уведомлений о прочтении записки

- **Для священников/алтарников:**
  - Просмотр очереди записок
  - Чтение записок с именами
  - Подтверждение прочтения записок
  - Автоматическая отправка уведомлений пользователям

- **Для администраторов:**
  - Просмотр статистики системы
  - Управление ролями пользователей
  - Просмотр активности священников/алтарников
  - Настройки системы

## Технологический стек

- Python 3.10+
- aiogram 3.x (async фреймворк для Telegram)
- PostgreSQL (база данных)
- SQLAlchemy (ORM)
- YooKassa SDK (платежный шлюз)
- aiohttp (веб-сервер для webhook)

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd NotesBot
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных PostgreSQL

Создайте базу данных:

```sql
CREATE DATABASE notesbot_db;
```

### 5. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните необходимые параметры:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com
TELEGRAM_WEBHOOK_PATH=/webhook

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/notesbot_db

# YooKassa Configuration
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here
YOOKASSA_WEBHOOK_URL=https://your-domain.com/yookassa-webhook

# Payment Settings
MIN_DONATION_AMOUNT=100.0
PAYMENT_DESCRIPTION=Пожертвование

# Application Settings
MAX_NAMES_PER_NOTE=10
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 6. Получение токена Telegram бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env`

### 7. Настройка Яндекс.Кассы

1. Зарегистрируйтесь в [Яндекс.Касса](https://yookassa.ru/)
2. Получите Shop ID и Secret Key в личном кабинете
3. Настройте webhook URL: `https://your-domain.com/yookassa-webhook`
4. Укажите реквизиты получателя в настройках

## Запуск

### Разработка

Для локальной разработки можно использовать polling вместо webhook:

```python
# Временно измените main.py для использования polling
# или используйте отдельный скрипт для разработки
```

### Production

1. Убедитесь, что у вас есть домен с SSL-сертификатом
2. Настройте reverse proxy (nginx) для проксирования запросов:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /yookassa-webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. Запустите приложение:

```bash
python main.py
```

Или используйте systemd service:

```ini
[Unit]
Description=NotesBot Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/NotesBot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Настройка первого администратора

После первого запуска бота, назначьте администратора через базу данных:

```sql
UPDATE users 
SET role = 'admin' 
WHERE telegram_id = YOUR_TELEGRAM_ID;
```

Или используйте команду в боте (если уже есть администратор).

## Структура проекта

```
NotesBot/
├── main.py                 # Точка входа, настройка webhook
├── config.py               # Конфигурация приложения
├── database.py             # Подключение к БД
├── models.py               # SQLAlchemy модели
├── handlers/               # Обработчики команд
│   ├── user_handlers.py   # Обработчики пользователей
│   ├── priest_handlers.py # Обработчики священников
│   └── admin_handlers.py  # Обработчики администраторов
├── services/               # Бизнес-логика
│   ├── note_service.py    # Работа с записками
│   ├── payment_service.py # Интеграция с Яндекс.Кассой
│   ├── user_service.py    # Управление пользователями
│   └── logging_service.py # Логирование
├── keyboards.py           # Клавиатуры Telegram
├── utils.py               # Вспомогательные функции
├── requirements.txt       # Зависимости
└── logs/                  # Логи операций
```

## Логирование

Система ведет журнал операций в `logs/operations.log` без сохранения персональных данных:
- Создание записок (без имен)
- Платежи (суммы, статусы)
- Прочтение записок (тип, время)
- Изменение ролей

## Безопасность

- Все персональные данные (имена) хранятся в базе данных
- Логи не содержат персональных данных
- После прочтения записки все данные удаляются из системы
- Используется HTTPS для webhook
- Валидация всех входных данных

## Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## Поддержка

[Укажите контакты для поддержки]
