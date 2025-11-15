"""Подключение к базе данных и инициализация таблиц."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from config import Config
from models import Base


class Database:
    """Класс для работы с базой данных."""
    
    def __init__(self):
        """Инициализация подключения к БД."""
        self.engine = create_async_engine(
            Config.DATABASE_URL,
            echo=False,
            poolclass=NullPool,
            future=True
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_db(self):
        """Создание всех таблиц в базе данных."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Закрытие соединения с БД."""
        await self.engine.dispose()
    
    def get_session(self):
        """Получение сессии БД (async context manager)."""
        return self.async_session_maker()


# Глобальный экземпляр базы данных
db = Database()

