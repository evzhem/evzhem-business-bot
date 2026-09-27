from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stars_balance: Mapped[int] = mapped_column(Integer, default=0)
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BusinessConnectionModel(Base):
    __tablename__ = "business_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_chat_id: Mapped[int] = mapped_column(BigInteger, default=0)
    can_reply: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rights_summary: Mapped[Optional[str]] = mapped_column(String(255), default="5/5 full rights")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AutoResponderSetting(Base):
    __tablename__ = "auto_responders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    mode: Mapped[str] = mapped_column(String(50), default="simple")
    text_template: Mapped[str] = mapped_column(
        Text, 
        default="👋 Привет! Сейчас я не у телефона или занят(а). Отвечу тебе при первой возможности!"
    )
    ai_prompt: Mapped[str] = mapped_column(
        Text, 
        default="Ты вежливый и лаконичный AI-ассистент владельца аккаунта. Ответь от его имени кратко (1-2 предложения), что сообщение принято."
    )
    work_hours_start: Mapped[str] = mapped_column(String(10), default="23:00")
    work_hours_end: Mapped[str] = mapped_column(String(10), default="08:00")
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60)
    only_new_contacts: Mapped[bool] = mapped_column(Boolean, default=False)
    keywords_json: Mapped[str] = mapped_column(Text, default='[{"keyword":"цена","reply":"Прайс-лист отправлен в закреп!"},{"keyword":"где ты","reply":"Я сейчас на встрече."}]')
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MutedChat(Base):
    __tablename__ = "muted_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    target_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=True)
    muted_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WhitelistChat(Base):
    __tablename__ = "whitelist_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    target_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatStatistic(Base):
    __tablename__ = "chat_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    interlocutor_name: Mapped[str] = mapped_column(String(255), default="Собеседник")
    incoming_count: Mapped[int] = mapped_column(Integer, default=0)
    outgoing_count: Mapped[int] = mapped_column(Integer, default=0)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    first_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CustomAnimation(Base):
    __tablename__ = "custom_animations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    command_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    frames_json: Mapped[str] = mapped_column(Text, nullable=False)
    interval_seconds: Mapped[float] = mapped_column(Float, default=0.4)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    achievement_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="🏆")
    current_count: Mapped[int] = mapped_column(Integer, default=0)
    target_count: Mapped[int] = mapped_column(Integer, default=10)
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class UserNote(Base):
    __tablename__ = "user_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    target_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserTag(Base):
    __tablename__ = "user_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    tag_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
