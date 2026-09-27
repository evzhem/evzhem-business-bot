import asyncio
import logging
import re
from datetime import datetime
from aiogram import Router, Bot, F
from aiogram.types import Message
from database.db import AsyncSessionLocal
from database.repository import Repository
from bot.services.animation_engine import (
    BUILTIN_ANIMATIONS,
    generate_typewriter_frames,
    animation_engine
)
from bot.services.moderation_service import moderation_service
from bot.services.autoresponder_service import auto_responder_service
from bot.services.stats_service import stats_service
from bot.services.utilities_service import utilities_service
from bot.services.voice_service import voice_service
from bot.services.qr_service import qr_service
from bot.services.crm_service import crm_service
from bot.services.ai_assistant_service import ai_assistant

logger = logging.getLogger(__name__)
router = Router()


# In-memory fast cache
CONN_CACHE: dict = {}
MUTED_CACHE: dict = {}  # owner_id -> set of muted target_ids
WHITELIST_CACHE: dict = {}

@router.business_message()
async def handle_business_message(message: Message, bot: Bot):
    business_conn_id = message.business_connection_id
    if not business_conn_id:
        return

    # Ensure services have bot instance
    moderation_service.bot = bot
    animation_engine.bot = bot
    auto_responder_service.bot = bot

    text = message.text or message.caption or ""
    sender_id = message.from_user.id if message.from_user else 0
    chat_id = message.chat.id
    sender_name = message.from_user.first_name if message.from_user else "Собеседник"

    # Fast connection check
    owner_user_id = CONN_CACHE.get(business_conn_id)
    if not owner_user_id:
        async with AsyncSessionLocal() as session:
            repo = Repository(session)
            b_conn = await repo.get_business_conn_by_id(business_conn_id)
            if not b_conn:
                return
            owner_user_id = b_conn.user_id
            CONN_CACHE[business_conn_id] = owner_user_id

    is_outgoing = (sender_id == owner_user_id)

    # 1. INCOMING MESSAGE PROCESSING (from interlocutor)
    if not is_outgoing:
        # Check in-memory fast mute cache first
        muted_set = MUTED_CACHE.get(owner_user_id, set())
        whitelist_set = WHITELIST_CACHE.get(owner_user_id, set())

        is_whitelisted = sender_id in whitelist_set or chat_id in whitelist_set
        is_target_muted = sender_id in muted_set or chat_id in muted_set

        if not is_target_muted and not is_whitelisted:
            async with AsyncSessionLocal() as session:
                repo = Repository(session)
                is_whitelisted = (
                    await repo.is_whitelisted(user_id=owner_user_id, target_id=sender_id) or
                    await repo.is_whitelisted(user_id=owner_user_id, target_id=chat_id)
                )
                is_target_muted = (
                    await repo.is_muted(user_id=owner_user_id, target_id=sender_id) or
                    await repo.is_muted(user_id=owner_user_id, target_id=chat_id)
                )
                if is_target_muted:
                    if owner_user_id not in MUTED_CACHE:
                        MUTED_CACHE[owner_user_id] = set()
                    MUTED_CACHE[owner_user_id].add(sender_id)
                    MUTED_CACHE[owner_user_id].add(chat_id)

        if not is_whitelisted and is_target_muted:
            logger.info(f"MUTED USER DETECTED! Instantly deleting message {message.message_id} from {sender_id} in chat {chat_id}")
            await moderation_service.delete_message_safe(business_conn_id, chat_id, message.message_id)
            return

        async with AsyncSessionLocal() as session:
            repo = Repository(session)
            await repo.record_message_stat(
                user_id=owner_user_id,
                chat_id=chat_id,
                is_outgoing=False,
                interlocutor_name=sender_name
            )

            ar_setting = await repo.get_auto_responder(owner_user_id)
            if ar_setting.is_active:
                await auto_responder_service.check_and_reply(
                    business_conn_id=business_conn_id,
                    user_id=owner_user_id,
                    chat_id=chat_id,
                    incoming_text=text,
                    setting=ar_setting
                )
                await repo.progress_achievement(owner_user_id, "automation_boss")
        return

        # 2. OUTGOING MESSAGE PROCESSING
        await repo.record_message_stat(
            user_id=owner_user_id,
            chat_id=chat_id,
            is_outgoing=True,
            interlocutor_name=message.chat.first_name or "Собеседник"
        )

        if datetime.utcnow().hour >= 3 and datetime.utcnow().hour <= 5:
            await repo.progress_achievement(owner_user_id, "night_owl")

        if not text.startswith("."):
            return

        raw_cmd = text[1:].strip()
        cmd_parts = raw_cmd.split(maxsplit=1)
        command_name = cmd_parts[0].lower()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""

        animation_engine.bot = bot
        moderation_service.bot = bot

        # ================= 1. ГОЛОСОВОЙ МОДУЛЬ (.гс / .voice) =================
        if command_name in ["гс", "voice", "голос"]:
            await moderation_service.delete_message_safe(business_conn_id, chat_id, message.message_id)
            target_text = args or "Привет! Это голосовое сообщение."
            await voice_service.send_voice_message(
                bot=bot,
                chat_id=chat_id,
                business_conn_id=business_conn_id,
                text=target_text
            )
            return

        # ================= 2. QR-КОДЫ (.qr) =================
        if command_name in ["qr", "кр"]:
            await moderation_service.delete_message_safe(business_conn_id, chat_id, message.message_id)
            qr_content = args or f"https://t.me/{message.from_user.username or 'telegram'}"
            await qr_service.send_qr_photo(
                bot=bot,
                chat_id=chat_id,
                business_conn_id=business_conn_id,
                data_text=qr_content
            )
            return

        # ================= 3. CRM, ДОСЬЕ, ТЕГИ И ЧЕКИ =================
        if command_name in ["досье", "dossier", "инфа"]:
            stat = await repo.get_chat_stat(owner_user_id, chat_id)
            tags = await repo.get_tags_for_contact(owner_user_id, chat_id)
            notes = await repo.get_user_notes(owner_user_id)
            contact_notes = [n for n in notes if n.target_id == chat_id]
            dossier_text = crm_service.format_dossier(
                target_name=message.chat.first_name or "Собеседник",
                target_id=chat_id,
                stat=stat,
                tags=tags,
                notes=contact_notes
            )
            await bot.edit_message_text(
                text=dossier_text,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["тег", "tag"]:
            if args:
                added = await repo.add_or_toggle_tag(owner_user_id, chat_id, args)
                status = f"✅ Тег <code>#{args}</code> добавлен" if added else f"🗑 Тег <code>#{args}</code> удален"
                await bot.edit_message_text(
                    text=f"🏷 <b>Контакты:</b> {status} для {message.chat.first_name or 'собеседника'}.",
                    business_connection_id=business_conn_id,
                    chat_id=chat_id,
                    message_id=message.message_id
                )
                await moderation_service.schedule_self_destruct(business_conn_id, chat_id, message.message_id, 3)
            return

        if command_name in ["чек", "bill", "receipt"]:
            parts = args.split(maxsplit=1)
            amount = parts[0] if parts else "1000"
            item = parts[1] if len(parts) > 1 else "Оказание услуг"
            receipt_card = crm_service.generate_receipt(
                amount=amount,
                item_name=item,
                sender_name=message.from_user.first_name or "Исполнитель",
                client_name=message.chat.first_name or "Клиент"
            )
            await bot.edit_message_text(
                text=receipt_card,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        # ================= 4. AI ИНТЕЛЛЕКТ (.суммари, .исправь, .стиль, .перевод) =================
        if command_name in ["суммари", "выжимка", "summary"]:
            count = int(args) if args.isdigit() else 20
            summary_card = await ai_assistant.summarize_dialog(count)
            await bot.edit_message_text(
                text=summary_card,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["исправь", "fix", "корректор"]:
            fixed = await ai_assistant.correct_grammar(args)
            await bot.edit_message_text(
                text=fixed,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["стиль", "деловой", "вежливо"]:
            style_name = "деловой" if command_name in ["деловой", "вежливо"] else "дружеский"
            styled = await ai_assistant.change_style(style_name, args)
            await bot.edit_message_text(
                text=styled,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["перевод", "translate"]:
            p = args.split(maxsplit=1)
            if len(p) >= 2 and len(p[0]) <= 3:
                target_lang = p[0]
                text_to_tr = p[1]
            else:
                target_lang = "en"
                text_to_tr = args
            translated = await ai_assistant.translate_text(target_lang, text_to_tr)
            await bot.edit_message_text(
                text=translated,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        # ================= 5. АНИМАЦИИ (ВКЛЮЧАЯ НОВЫЕ) =================
        clean_text_cmd = raw_cmd.lower()
        matched_anim_key = None
        for key in BUILTIN_ANIMATIONS.keys():
            if clean_text_cmd == key or clean_text_cmd.startswith(key + " "):
                matched_anim_key = key
                break

        if matched_anim_key:
            anim_data = BUILTIN_ANIMATIONS[matched_anim_key]
            if matched_anim_key in ["люблю", "сердце", "роза", "сердечки", "корона"]:
                await repo.progress_achievement(owner_user_id, "master_of_romance")

            await animation_engine.play_animation(
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id,
                frames=anim_data["frames"],
                interval=anim_data.get("interval", 0.38)
            )
            return

        custom_anim = await repo.get_custom_animation(owner_user_id, command_name)
        if custom_anim:
            import json
            frames = json.loads(custom_anim.frames_json)
            await animation_engine.play_animation(
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id,
                frames=frames,
                interval=custom_anim.interval_seconds
            )
            return

        # ================= 6. ЖИВАЯ ПЕЧАТЬ (.печать) =================
        if command_name in ["печать", "type", "print"]:
            target_text = args if args else "Привет! Это эффект живой печати ✨"
            frames = generate_typewriter_frames(target_text)
            await repo.progress_achievement(owner_user_id, "typewriter_pro")
            await animation_engine.play_animation(
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id,
                frames=frames,
                interval=0.32
            )
            return

        # ================= 7. МОДЕРАЦИЯ И МУТ =================
        if command_name in ["мут", "mute"]:
            duration_minutes = None
            if args:
                match = re.search(r"(\d+)\s*([мчmhd]?)", args.lower())
                if match:
                    val = int(match.group(1))
                    unit = match.group(2)
                    if unit in ["ч", "h"]:
                        duration_minutes = val * 60
                    elif unit in ["д", "d"]:
                        duration_minutes = val * 1440
                    else:
                        duration_minutes = val

            target_id = chat_id
            target_name = message.chat.first_name or f"User {chat_id}"
            # Instant in-memory cache update
            if owner_user_id not in MUTED_CACHE:
                MUTED_CACHE[owner_user_id] = set()
            MUTED_CACHE[owner_user_id].add(target_id)
            if owner_user_id in WHITELIST_CACHE:
                WHITELIST_CACHE[owner_user_id].discard(target_id)

            await repo.mute_chat(
                user_id=owner_user_id,
                target_id=target_id,
                target_name=target_name,
                duration_minutes=duration_minutes
            )
            await repo.progress_achievement(owner_user_id, "silence_keeper")

            status_msg = (
                f"🔇 <b>Собеседник замучен на {duration_minutes} мин.</b>"
                if duration_minutes
                else "🔇 <b>Собеседник замучен навсегда.</b>"
            )
            await bot.edit_message_text(
                text=f"{status_msg}\n<i>Все входящие сообщения в этом диалоге будут мгновенно удаляться.</i>",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            await moderation_service.schedule_self_destruct(business_conn_id, chat_id, message.message_id, 4)
            return

        if command_name in ["размут", "unmute"]:
            target_id = chat_id
            if owner_user_id in MUTED_CACHE:
                MUTED_CACHE[owner_user_id].discard(target_id)
            await repo.unmute_chat(user_id=owner_user_id, target_id=target_id)
            await bot.edit_message_text(
                text="🔊 <b>Мут снят.</b> Собеседник снова может писать.",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            await moderation_service.schedule_self_destruct(business_conn_id, chat_id, message.message_id, 3)
            return

        if command_name in ["антимут", "antimute", "whitelist"]:
            target_id = chat_id
            target_name = message.chat.first_name or f"User {chat_id}"
            if owner_user_id not in WHITELIST_CACHE:
                WHITELIST_CACHE[owner_user_id] = set()
            WHITELIST_CACHE[owner_user_id].add(target_id)
            if owner_user_id in MUTED_CACHE:
                MUTED_CACHE[owner_user_id].discard(target_id)
            await repo.add_to_whitelist(user_id=owner_user_id, target_id=target_id, target_name=target_name)
            await bot.edit_message_text(
                text=f"🛡️ <b>Пользователь {target_name} добавлен в Белый список!</b>",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            await moderation_service.schedule_self_destruct(business_conn_id, chat_id, message.message_id, 3)
            return

        # ================= 8. СТАТИСТИКА =================
        if clean_text_cmd.startswith("наша стата") or command_name == "стата":
            stat = await repo.get_chat_stat(owner_user_id, chat_id)
            if not stat:
                stat = await repo.record_message_stat(
                    user_id=owner_user_id,
                    chat_id=chat_id,
                    is_outgoing=True,
                    interlocutor_name=message.chat.first_name or "Собеседник"
                )
            card = stats_service.format_chat_stats_card(
                stat=stat,
                user_name=message.from_user.first_name or "Вы",
                partner_name=message.chat.first_name or "Собеседник"
            )
            await bot.edit_message_text(
                text=card,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        # ================= 9. СПАМ & САМОУНИЧТОЖЕНИЕ =================
        if command_name in ["спам", "spam"]:
            spam_text = "Спам-тест"
            count = 10
            parts = args.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                count = int(parts[-1])
                spam_text = " ".join(parts[:-1]).strip("'\"")
            elif len(parts) == 1 and parts[0].isdigit():
                count = int(parts[0])
            elif args:
                spam_text = args.strip("'\"")

            await moderation_service.delete_message_safe(business_conn_id, chat_id, message.message_id)
            await moderation_service.run_spam_safe(
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                text=spam_text,
                count=count,
                max_limit=30
            )
            return

        if command_name in ["самоуничтожение", "таймер", "sd"]:
            seconds = 5
            target_text = "💣 Это сообщение самоуничтожится..."
            parts = args.split(maxsplit=1)
            if parts and parts[0].isdigit():
                seconds = int(parts[0])
                if len(parts) > 1:
                    target_text = parts[1]
            elif args:
                target_text = args

            await bot.edit_message_text(
                text=f"{target_text}\n\n⏳ <i>[Исчезнет через {seconds} сек]</i>",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            await moderation_service.schedule_self_destruct(business_conn_id, chat_id, message.message_id, seconds)
            return

        # ================= 10. УТИЛИТЫ И СЕРВИСЫ =================
        if command_name in ["крипта", "курс", "btc", "ton", "crypto"]:
            rates = await utilities_service.get_crypto_rates()
            await bot.edit_message_text(
                text=rates,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["погода", "weather"]:
            w_res = await utilities_service.get_weather(args or "Москва")
            await bot.edit_message_text(
                text=w_res,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["вики", "wiki", "поиск"]:
            w_sum = await utilities_service.get_wiki_summary(args)
            await bot.edit_message_text(
                text=w_sum,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["сократи", "clck", "short"]:
            short_res = await utilities_service.shorten_url(args)
            await bot.edit_message_text(
                text=short_res,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["пароль", "pass", "pwd"]:
            length = int(args) if args.isdigit() else 12
            pwd_res = utilities_service.generate_password(length)
            await bot.edit_message_text(
                text=pwd_res,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["комплимент", "хвали"]:
            await bot.edit_message_text(
                text=utilities_service.get_compliment(),
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["цитата", "мысль", "quote"]:
            await bot.edit_message_text(
                text=utilities_service.get_quote(),
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["анекдот", "шутка", "joke"]:
            await bot.edit_message_text(
                text=utilities_service.get_joke(),
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["кубик", "рандом", "dice"]:
            sides = int(args) if args.isdigit() else 100
            await bot.edit_message_text(
                text=utilities_service.roll_dice(sides),
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["монетка", "монета", "coin"]:
            await bot.edit_message_text(
                text=utilities_service.flip_coin(),
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["инфо", "ктоты", "скан"]:
            partner_name = message.chat.first_name or "Собеседник"
            await bot.edit_message_text(
                text=utilities_service.scan_interlocutor(partner_name),
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["зеркало", "реверс"]:
            rev = utilities_service.reverse_text(args or "Привет!")
            await bot.edit_message_text(
                text=f"🪞 <b>Зеркало:</b> <code>{rev}</code>",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["калькулятор", "calc"]:
            res = utilities_service.calculate_expression(args)
            await bot.edit_message_text(
                text=res,
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["шрифт", "font"]:
            style = 1
            font_text = args
            parts = args.split(maxsplit=1)
            if parts and parts[0].isdigit():
                style = int(parts[0])
                font_text = parts[1] if len(parts) > 1 else ""
            transformed = utilities_service.apply_fancy_font(style, font_text)
            await bot.edit_message_text(
                text=transformed or "❌ Введите текст: <code>.шрифт 1 Привет</code>",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["транслит"]:
            res = utilities_service.transliterate(args)
            await bot.edit_message_text(
                text=f"🔤 <b>Транслит:</b>\n{res}",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            return

        if command_name in ["напоминание", "remind"]:
            parts = args.split(maxsplit=1)
            minutes = 5
            rem_text = "Важное напоминание!"
            if parts and parts[0].isdigit():
                minutes = int(parts[0])
                rem_text = parts[1] if len(parts) > 1 else rem_text
            elif args:
                rem_text = args

            await utilities_service.schedule_reminder(
                bot=bot,
                chat_id=chat_id,
                business_conn_id=business_conn_id,
                delay_seconds=minutes * 60,
                reminder_text=rem_text
            )
            await bot.edit_message_text(
                text=f"⏰ <b>Напоминание установлено!</b> Сработает через {minutes} мин:\n📌 <i>{rem_text}</i>",
                business_connection_id=business_conn_id,
                chat_id=chat_id,
                message_id=message.message_id
            )
            await moderation_service.schedule_self_destruct(business_conn_id, chat_id, message.message_id, 4)
            return

        if command_name in ["заметка", "важное", "note"]:
            if args:
                await repo.add_or_update_note(
                    user_id=owner_user_id,
                    target_id=chat_id,
                    note_text=args,
                    target_name=message.chat.first_name or f"User {chat_id}"
                )
                await bot.edit_message_text(
                    text=f"📝 <b>Заметка сохранена:</b>\n<i>{args}</i>",
                    business_connection_id=business_conn_id,
                    chat_id=chat_id,
                    message_id=message.message_id
                )
                await moderation_service.schedule_self_destruct(business_conn_id, chat_id, message.message_id, 3)
            return
