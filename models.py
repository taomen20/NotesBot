"""SQLAlchemy модели для базы данных."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


class UserRole(str, Enum):
    """Роли пользователей."""
    USER = "user"
    PRIEST = "priest"
    ALTAR_SERVER = "altar_server"
    ADMIN = "admin"


class NoteType(str, Enum):
    """Типы записок."""
    FOR_HEALTH = "for_health"  # За здравие
    FOR_REPOSE = "for_repose"  # Об упокоении


class NoteStatus(str, Enum):
    """Статусы записок."""
    PENDING = "pending"  # Ожидает оплаты
    PAID = "paid"  # Оплачена, в очереди
    READ = "read"  # Прочитана
    DELETED = "deleted"  # Удалена


class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False),
        default=UserRole.USER,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="user", cascade="all, delete-orphan")


class Note(Base):
    """Модель записки."""
    __tablename__ = "notes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[NoteType] = mapped_column(
        SQLEnum(NoteType, native_enum=False),
        nullable=False
    )
    status: Mapped[NoteStatus] = mapped_column(
        SQLEnum(NoteStatus, native_enum=False),
        default=NoteStatus.PENDING,
        nullable=False,
        index=True
    )
    payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notes")
    names: Mapped[List["NoteName"]] = relationship("NoteName", back_populates="note", cascade="all, delete-orphan")


class NoteName(Base):
    """Модель имени в записке."""
    __tablename__ = "note_names"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    list_type: Mapped[NoteType] = mapped_column(
        SQLEnum(NoteType, native_enum=False),
        nullable=False
    )
    
    # Relationships
    note: Mapped["Note"] = relationship("Note", back_populates="names")


class Setting(Base):
    """Модель настроек системы."""
    __tablename__ = "settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

