"""Сервис для управления пользователями и ролями."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from models import User, UserRole
from services.logging_service import operation_logger


class UserService:
    """Сервис для работы с пользователями."""
    
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        telegram_id: int,
        username: str = None
    ) -> User:
        """Получить пользователя или создать нового."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                role=UserRole.USER
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_by_telegram_id(
        session: AsyncSession,
        telegram_id: int
    ) -> User | None:
        """Получить пользователя по Telegram ID."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user_role(
        session: AsyncSession,
        user_id: int,
        new_role: UserRole
    ) -> bool:
        """Обновить роль пользователя."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        old_role = user.role
        user.role = new_role
        await session.commit()
        
        operation_logger.log_role_changed(
            user_id=user_id,
            old_role=old_role.value,
            new_role=new_role.value
        )
        
        return True
    
    @staticmethod
    async def get_users_by_role(
        session: AsyncSession,
        role: UserRole
    ) -> list[User]:
        """Получить всех пользователей с определенной ролью."""
        result = await session.execute(
            select(User).where(User.role == role)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
        """Проверить, является ли пользователь администратором."""
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        return user is not None and user.role == UserRole.ADMIN
    
    @staticmethod
    async def is_priest_or_altar_server(
        session: AsyncSession,
        telegram_id: int
    ) -> bool:
        """Проверить, является ли пользователь священником или алтарником."""
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        if not user:
            return False
        return user.role in (UserRole.PRIEST, UserRole.ALTAR_SERVER)

