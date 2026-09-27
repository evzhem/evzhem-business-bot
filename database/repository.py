import json
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, update, delete, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    User,
    BusinessConnectionModel,
    AutoResponderSetting,
    MutedChat,
    WhitelistChat,
    ChatStatistic,
    CustomAnimation,
    UserAchievement,
    UserNote,
    UserTag
)

DEFAULT_ACHIEVEMENTS = [
    {
        "code": "master_of_romance",
        "title": "Мастер романтики ❤️",
        "description": "Отправьте 20 анимаций любви (.люблю, .сердце)",
        "icon": "💖",
        "target_count": 20
    },
    {
        "code": "silence_keeper",
        "title": "Хранитель тишины 🤫",
        "description": "Замутьте 3 токсичных собеседников (.мут)",
        "icon": "🔇",
        "target_count": 3
    },
    {
        "code": "automation_boss",
        "title": "Босс автоматизации ⚡",
        "description": "Активируйте и настройте умный автоответчик",
        "icon": "🤖",
        "target_count": 1
    },
    {
        "code": "night_owl",
        "title": "Ночная сова 🦉",
        "description": "Отправьте команду или сообщение после 3:00 ночи",
        "icon": "🌙",
        "target_count": 5
    },
    {
        "code": "typewriter_pro",
        "title": "Клавиатурный ниндзя ⌨️",
        "description": "Используйте эффект живой печати (.печать) 15 раз",
        "icon": "⚡",
        "target_count": 15
    }
]


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ================= USER =================
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        referrer_id: Optional[int] = None
    ) -> User:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                referrer_id=referrer_id
            )
            self.session.add(user)
            await self.session.flush()

            # Initialize default auto-responder
            ar = AutoResponderSetting(user_id=telegram_id)
            self.session.add(ar)

            # Initialize achievements
            for ach in DEFAULT_ACHIEVEMENTS:
                u_ach = UserAchievement(
                    user_id=telegram_id,
                    achievement_code=ach["code"],
                    title=ach["title"],
                    description=ach["description"],
                    icon=ach["icon"],
                    target_count=ach["target_count"],
                    current_count=0,
                    is_unlocked=False
                )
                self.session.add(u_ach)

            await self.session.commit()
            await self.session.refresh(user)
        else:
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if updated:
                await self.session.commit()
        return user

    async def get_user_by_tg_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def grant_premium(self, telegram_id: int, days: int) -> User:
        user = await self.get_or_create_user(telegram_id)
        now = datetime.utcnow()
        if user.premium_until and user.premium_until > now:
            user.premium_until = user.premium_until + timedelta(days=days)
        else:
            user.premium_until = now + timedelta(days=days)
        user.is_premium = True
        await self.session.commit()
        await self.session.refresh(user)
        return user

    # ================= BUSINESS CONNECTION =================
    async def save_or_update_business_conn(
        self,
        connection_id: str,
        user_id: int,
        user_chat_id: int,
        can_reply: bool,
        is_enabled: bool,
        rights_summary: str = "5/5"
    ) -> BusinessConnectionModel:
        result = await self.session.execute(
            select(BusinessConnectionModel).where(BusinessConnectionModel.user_id == user_id)
        )
        conn = result.scalar_one_or_none()
        if not conn:
            conn = BusinessConnectionModel(
                connection_id=connection_id,
                user_id=user_id,
                user_chat_id=user_chat_id,
                can_reply=can_reply,
                is_enabled=is_enabled,
                rights_summary=rights_summary
            )
            self.session.add(conn)
        else:
            conn.connection_id = connection_id
            conn.user_chat_id = user_chat_id
            conn.can_reply = can_reply
            conn.is_enabled = is_enabled
            conn.rights_summary = rights_summary
            conn.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(conn)
        return conn

    async def get_business_conn_by_user(self, user_id: int) -> Optional[BusinessConnectionModel]:
        result = await self.session.execute(
            select(BusinessConnectionModel).where(
                and_(
                    BusinessConnectionModel.user_id == user_id,
                    BusinessConnectionModel.is_enabled == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_business_conn_by_id(self, connection_id: str) -> Optional[BusinessConnectionModel]:
        result = await self.session.execute(
            select(BusinessConnectionModel).where(BusinessConnectionModel.connection_id == connection_id)
        )
        return result.scalar_one_or_none()

    # ================= AUTO RESPONDER =================
    async def get_auto_responder(self, user_id: int) -> AutoResponderSetting:
        result = await self.session.execute(
            select(AutoResponderSetting).where(AutoResponderSetting.user_id == user_id)
        )
        ar = result.scalar_one_or_none()
        if not ar:
            ar = AutoResponderSetting(user_id=user_id)
            self.session.add(ar)
            await self.session.commit()
            await self.session.refresh(ar)
        return ar

    async def update_auto_responder(
        self,
        user_id: int,
        is_active: Optional[bool] = None,
        mode: Optional[str] = None,
        text_template: Optional[str] = None,
        ai_prompt: Optional[str] = None,
        work_hours_start: Optional[str] = None,
        work_hours_end: Optional[str] = None,
        cooldown_minutes: Optional[int] = None,
        keywords_json: Optional[str] = None
    ) -> AutoResponderSetting:
        ar = await self.get_auto_responder(user_id)
        if is_active is not None:
            ar.is_active = is_active
        if mode is not None:
            ar.mode = mode
        if text_template is not None:
            ar.text_template = text_template
        if ai_prompt is not None:
            ar.ai_prompt = ai_prompt
        if work_hours_start is not None:
            ar.work_hours_start = work_hours_start
        if work_hours_end is not None:
            ar.work_hours_end = work_hours_end
        if cooldown_minutes is not None:
            ar.cooldown_minutes = cooldown_minutes
        if keywords_json is not None:
            ar.keywords_json = keywords_json
        ar.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(ar)
        return ar

    # ================= MUTED CHATS =================
    async def mute_chat(
        self,
        user_id: int,
        target_id: int,
        target_name: Optional[str] = None,
        duration_minutes: Optional[int] = None
    ) -> MutedChat:
        # Check if already muted
        result = await self.session.execute(
            select(MutedChat).where(
                and_(MutedChat.user_id == user_id, MutedChat.target_id == target_id)
            )
        )
        mute = result.scalar_one_or_none()
        muted_until = (
            datetime.utcnow() + timedelta(minutes=duration_minutes)
            if duration_minutes
            else None
        )
        is_perm = duration_minutes is None

        if not mute:
            mute = MutedChat(
                user_id=user_id,
                target_id=target_id,
                target_name=target_name or f"User {target_id}",
                is_permanent=is_perm,
                muted_until=muted_until
            )
            self.session.add(mute)
        else:
            mute.is_permanent = is_perm
            mute.muted_until = muted_until
            mute.target_name = target_name or mute.target_name
        await self.session.commit()
        await self.session.refresh(mute)
        return mute

    async def unmute_chat(self, user_id: int, target_id: int) -> bool:
        result = await self.session.execute(
            delete(MutedChat).where(
                and_(MutedChat.user_id == user_id, MutedChat.target_id == target_id)
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def is_muted(self, user_id: int, target_id: int) -> bool:
        result = await self.session.execute(
            select(MutedChat).where(
                and_(MutedChat.user_id == user_id, MutedChat.target_id == target_id)
            )
        )
        mute = result.scalar_one_or_none()
        if not mute:
            return False
        if mute.is_permanent:
            return True
        if mute.muted_until and mute.muted_until > datetime.utcnow():
            return True
        # Expired mute
        await self.unmute_chat(user_id, target_id)
        return False

    async def get_user_mutes(self, user_id: int) -> List[MutedChat]:
        result = await self.session.execute(
            select(MutedChat).where(MutedChat.user_id == user_id).order_by(desc(MutedChat.created_at))
        )
        return list(result.scalars().all())

    # ================= WHITELIST =================
    async def add_to_whitelist(self, user_id: int, target_id: int, target_name: Optional[str] = None) -> WhitelistChat:
        result = await self.session.execute(
            select(WhitelistChat).where(
                and_(WhitelistChat.user_id == user_id, WhitelistChat.target_id == target_id)
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            item = WhitelistChat(user_id=user_id, target_id=target_id, target_name=target_name)
            self.session.add(item)
            await self.session.commit()
            await self.session.refresh(item)
        return item

    async def is_whitelisted(self, user_id: int, target_id: int) -> bool:
        result = await self.session.execute(
            select(WhitelistChat).where(
                and_(WhitelistChat.user_id == user_id, WhitelistChat.target_id == target_id)
            )
        )
        return result.scalar_one_or_none() is not None

    # ================= STATISTICS =================
    async def record_message_stat(
        self,
        user_id: int,
        chat_id: int,
        is_outgoing: bool,
        interlocutor_name: str = "Собеседник"
    ) -> ChatStatistic:
        result = await self.session.execute(
            select(ChatStatistic).where(
                and_(ChatStatistic.user_id == user_id, ChatStatistic.chat_id == chat_id)
            )
        )
        stat = result.scalar_one_or_none()
        if not stat:
            stat = ChatStatistic(
                user_id=user_id,
                chat_id=chat_id,
                interlocutor_name=interlocutor_name,
                incoming_count=0 if is_outgoing else 1,
                outgoing_count=1 if is_outgoing else 0,
                last_message_at=datetime.utcnow()
            )
            self.session.add(stat)
        else:
            if is_outgoing:
                stat.outgoing_count += 1
            else:
                stat.incoming_count += 1
            stat.interlocutor_name = interlocutor_name
            stat.last_message_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(stat)
        return stat

    async def get_chat_stat(self, user_id: int, chat_id: int) -> Optional[ChatStatistic]:
        result = await self.session.execute(
            select(ChatStatistic).where(
                and_(ChatStatistic.user_id == user_id, ChatStatistic.chat_id == chat_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_global_user_stats(self, user_id: int) -> dict:
        result = await self.session.execute(
            select(
                func.sum(ChatStatistic.incoming_count).label("total_in"),
                func.sum(ChatStatistic.outgoing_count).label("total_out"),
                func.count(ChatStatistic.id).label("total_dialogues")
            ).where(ChatStatistic.user_id == user_id)
        )
        row = result.one()
        return {
            "total_incoming": row.total_in or 0,
            "total_outgoing": row.total_out or 0,
            "total_dialogues": row.total_dialogues or 0
        }

    # ================= CUSTOM ANIMATIONS =================
    async def create_custom_animation(
        self,
        user_id: int,
        command_name: str,
        frames: List[str],
        interval: float = 0.4
    ) -> CustomAnimation:
        clean_name = command_name.lower().strip().lstrip(".")
        result = await self.session.execute(
            select(CustomAnimation).where(
                and_(CustomAnimation.user_id == user_id, CustomAnimation.command_name == clean_name)
            )
        )
        anim = result.scalar_one_or_none()
        frames_json = json.dumps(frames, ensure_ascii=False)
        if not anim:
            anim = CustomAnimation(
                user_id=user_id,
                command_name=clean_name,
                frames_json=frames_json,
                interval_seconds=interval
            )
            self.session.add(anim)
        else:
            anim.frames_json = frames_json
            anim.interval_seconds = interval
        await self.session.commit()
        await self.session.refresh(anim)
        return anim

    async def get_custom_animation(self, user_id: int, command_name: str) -> Optional[CustomAnimation]:
        clean_name = command_name.lower().strip().lstrip(".")
        result = await self.session.execute(
            select(CustomAnimation).where(
                and_(CustomAnimation.user_id == user_id, CustomAnimation.command_name == clean_name)
            )
        )
        return result.scalar_one_or_none()

    async def get_all_user_custom_animations(self, user_id: int) -> List[CustomAnimation]:
        result = await self.session.execute(
            select(CustomAnimation).where(CustomAnimation.user_id == user_id).order_by(desc(CustomAnimation.created_at))
        )
        return list(result.scalars().all())

    # ================= ACHIEVEMENTS =================
    async def progress_achievement(self, user_id: int, achievement_code: str, increment: int = 1) -> Optional[UserAchievement]:
        result = await self.session.execute(
            select(UserAchievement).where(
                and_(UserAchievement.user_id == user_id, UserAchievement.achievement_code == achievement_code)
            )
        )
        ach = result.scalar_one_or_none()
        if not ach:
            return None
        if not ach.is_unlocked:
            ach.current_count += increment
            if ach.current_count >= ach.target_count:
                ach.is_unlocked = True
                ach.unlocked_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(ach)
        return ach

    async def get_user_achievements(self, user_id: int) -> List[UserAchievement]:
        result = await self.session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        return list(result.scalars().all())

    # ================= USER NOTES =================
    async def add_or_update_note(self, user_id: int, target_id: int, note_text: str, target_name: Optional[str] = None) -> UserNote:
        result = await self.session.execute(
            select(UserNote).where(
                and_(UserNote.user_id == user_id, UserNote.target_id == target_id)
            )
        )
        note = result.scalar_one_or_none()
        if not note:
            note = UserNote(user_id=user_id, target_id=target_id, target_name=target_name, note_text=note_text)
            self.session.add(note)
        else:
            note.note_text = note_text
            note.target_name = target_name or note.target_name
        await self.session.commit()
        await self.session.refresh(note)
        return note

    # ================= USER TAGS & DOSSIER =================
    async def add_or_toggle_tag(self, user_id: int, target_id: int, tag_name: str) -> bool:
        clean_tag = tag_name.strip().lstrip("#")
        result = await self.session.execute(
            select(UserTag).where(
                and_(
                    UserTag.user_id == user_id,
                    UserTag.target_id == target_id,
                    UserTag.tag_name == clean_tag
                )
            )
        )
        tag = result.scalar_one_or_none()
        if tag:
            await self.session.delete(tag)
            await self.session.commit()
            return False  # Removed
        else:
            new_tag = UserTag(user_id=user_id, target_id=target_id, tag_name=clean_tag)
            self.session.add(new_tag)
            await self.session.commit()
            return True  # Added

    async def get_tags_for_contact(self, user_id: int, target_id: int) -> List[str]:
        result = await self.session.execute(
            select(UserTag.tag_name).where(
                and_(UserTag.user_id == user_id, UserTag.target_id == target_id)
            )
        )
        return list(result.scalars().all())

    async def get_all_contact_tags(self, user_id: int) -> List[UserTag]:
        result = await self.session.execute(
            select(UserTag).where(UserTag.user_id == user_id).order_by(desc(UserTag.created_at))
        )
        return list(result.scalars().all())
