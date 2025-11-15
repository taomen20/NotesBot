"""Сервис для работы с записками."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from models import Note, NoteName, NoteType, NoteStatus, User
from services.logging_service import operation_logger


class NoteService:
    """Сервис для работы с записками."""
    
    @staticmethod
    async def create_note(
        session: AsyncSession,
        user_id: int,
        note_type: NoteType,
        names_for_health: list[str],
        names_for_repose: list[str],
        amount: float
    ) -> Note:
        """Создать новую записку."""
        note = Note(
            user_id=user_id,
            type=note_type,
            status=NoteStatus.PENDING,
            amount=amount
        )
        session.add(note)
        await session.flush()
        
        # Добавить имена
        all_names = []
        for name in names_for_health:
            all_names.append(NoteName(
                note_id=note.id,
                name=name,
                list_type=NoteType.FOR_HEALTH
            ))
        
        for name in names_for_repose:
            all_names.append(NoteName(
                note_id=note.id,
                name=name,
                list_type=NoteType.FOR_REPOSE
            ))
        
        session.add_all(all_names)
        await session.commit()
        await session.refresh(note)
        
        total_names = len(names_for_health) + len(names_for_repose)
        operation_logger.log_note_created(
            note_id=note.id,
            note_type=note_type.value,
            names_count=total_names,
            amount=amount
        )
        
        return note
    
    @staticmethod
    async def update_note_payment(
        session: AsyncSession,
        note_id: int,
        payment_id: str
    ) -> bool:
        """Обновить записку после оплаты."""
        result = await session.execute(
            select(Note).where(Note.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            return False
        
        note.payment_id = payment_id
        note.status = NoteStatus.PAID
        await session.commit()
        
        return True
    
    @staticmethod
    async def get_note_by_payment_id(
        session: AsyncSession,
        payment_id: str
    ) -> Note | None:
        """Получить записку по ID платежа."""
        result = await session.execute(
            select(Note)
            .options(selectinload(Note.names), selectinload(Note.user))
            .where(Note.payment_id == payment_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_queue_count(
        session: AsyncSession,
        note_type: NoteType | None = None
    ) -> int:
        """Получить количество записок в очереди."""
        query = select(func.count(Note.id)).where(Note.status == NoteStatus.PAID)
        
        if note_type:
            query = query.where(Note.type == note_type)
        
        result = await session.execute(query)
        return result.scalar() or 0
    
    @staticmethod
    async def get_next_note(
        session: AsyncSession,
        note_type: NoteType
    ) -> Note | None:
        """Получить следующую записку из очереди."""
        result = await session.execute(
            select(Note)
            .options(selectinload(Note.names), selectinload(Note.user))
            .where(
                and_(
                    Note.status == NoteStatus.PAID,
                    Note.type == note_type
                )
            )
            .order_by(Note.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def mark_note_as_read(
        session: AsyncSession,
        note_id: int,
        reader_role: str
    ) -> bool:
        """Отметить записку как прочитанную."""
        result = await session.execute(
            select(Note).where(Note.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            return False
        
        note.status = NoteStatus.READ
        note.read_at = datetime.now()
        await session.commit()
        
        operation_logger.log_note_read(
            note_id=note_id,
            note_type=note.type.value,
            reader_role=reader_role
        )
        
        return True
    
    @staticmethod
    async def delete_note(
        session: AsyncSession,
        note_id: int
    ) -> bool:
        """Удалить записку."""
        result = await session.execute(
            select(Note).where(Note.id == note_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            return False
        
        note.status = NoteStatus.DELETED
        await session.commit()
        
        return True
    
    @staticmethod
    async def get_note_with_names(
        session: AsyncSession,
        note_id: int
    ) -> Note | None:
        """Получить записку с именами."""
        result = await session.execute(
            select(Note)
            .options(selectinload(Note.names), selectinload(Note.user))
            .where(Note.id == note_id)
        )
        return result.scalar_one_or_none()

