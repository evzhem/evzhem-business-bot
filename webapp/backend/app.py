import asyncio
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramNetworkError, TelegramAPIError

from config import settings
from database.db import AsyncSessionLocal, init_db
from database.repository import Repository
from bot.services.animation_engine import BUILTIN_ANIMATIONS, generate_typewriter_frames
from bot.services.stats_service import stats_service
from bot.services.utilities_service import utilities_service
from bot.services.autoresponder_service import auto_responder_service
from bot.services.crm_service import crm_service
from bot.services.ai_assistant_service import ai_assistant
from bot.handlers.business_connection import router as business_conn_router
from bot.handlers.business_messages import router as business_messages_router
from bot.handlers.pm_bot_dialogs import router as pm_dialogs_router
from bot.handlers.payments import router as payments_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="evzhem_business_bot API & WebApp")

# Mount static files
app.mount("/static", StaticFiles(directory="/home/user/telegram_business_bot/webapp/static"), name="static")


@app.on_event("startup")
async def startup():
    await init_db()
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        demo_user = await repo.get_or_create_user(
            telegram_id=777888999,
            username="evzhem",
            first_name="Евгений"
        )
        await repo.save_or_update_business_conn(
            connection_id="conn_demo_12345",
            user_id=demo_user.telegram_id,
            user_chat_id=demo_user.telegram_id,
            can_reply=True,
            is_enabled=True,
            rights_summary="5/5 (Full Rights)"
        )
        await repo.record_message_stat(demo_user.telegram_id, 1001, is_outgoing=True, interlocutor_name="Анна (Клиент)")
        await repo.record_message_stat(demo_user.telegram_id, 1001, is_outgoing=False, interlocutor_name="Анна (Клиент)")
        await repo.record_message_stat(demo_user.telegram_id, 1002, is_outgoing=True, interlocutor_name="Мария ❤️")
        await repo.record_message_stat(demo_user.telegram_id, 1002, is_outgoing=True, interlocutor_name="Мария ❤️")
        await repo.record_message_stat(demo_user.telegram_id, 1002, is_outgoing=False, interlocutor_name="Мария ❤️")
        await repo.add_or_toggle_tag(demo_user.telegram_id, 1002, "Любимая")
        await repo.add_or_toggle_tag(demo_user.telegram_id, 1002, "VIP")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("/home/user/telegram_business_bot/webapp/static/index.html")


# Schemas
class AutoResponderUpdate(BaseModel):
    is_active: bool
    mode: str
    text_template: str
    ai_prompt: str
    work_hours_start: str
    work_hours_end: str
    cooldown_minutes: int
    keywords_json: str


class CustomAnimationCreate(BaseModel):
    command_name: str
    frames: List[str]
    interval: float = 0.4


class MuteCreate(BaseModel):
    target_id: int
    target_name: Optional[str] = "Собеседник"
    duration_minutes: Optional[int] = None


class CommandSimulateRequest(BaseModel):
    command_text: str
    user_id: int = 777888999


@app.get("/api/user/{user_id}")
async def get_user_profile(user_id: int):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        user = await repo.get_or_create_user(user_id)
        conn = await repo.get_business_conn_by_user(user_id)
        ar = await repo.get_auto_responder(user_id)
        stats = await repo.get_global_user_stats(user_id)

    return {
        "telegram_id": user.telegram_id,
        "username": user.username or "evzhem",
        "first_name": user.first_name or "Пользователь",
        "is_premium": user.is_premium,
        "premium_until": user.premium_until.strftime("%d.%m.%Y") if user.premium_until else None,
        "is_connected": conn.is_enabled if conn else False,
        "connection_rights": conn.rights_summary if conn else "Не подключен",
        "autoresponder_active": ar.is_active,
        "stats": stats
    }


@app.get("/api/animations")
async def get_animations(user_id: int = 777888999):
    builtins = []
    for key, data in BUILTIN_ANIMATIONS.items():
        builtins.append({
            "command": f".{key}",
            "name": key,
            "title": data["title"],
            "category": data["category"],
            "is_premium": data["is_premium"],
            "interval": data.get("interval", 0.38),
            "frames": data["frames"],
            "is_custom": False
        })

    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        customs = await repo.get_all_user_custom_animations(user_id)

    custom_list = []
    for c in customs:
        custom_list.append({
            "command": f".{c.command_name}",
            "name": c.command_name,
            "title": f"Кастом: .{c.command_name}",
            "category": "custom",
            "is_premium": False,
            "interval": c.interval_seconds,
            "frames": json.loads(c.frames_json),
            "is_custom": True
        })

    return {"builtin": builtins, "custom": custom_list}


@app.post("/api/animations/custom")
async def create_custom_anim(data: CustomAnimationCreate, user_id: int = Query(777888999)):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        anim = await repo.create_custom_animation(
            user_id=user_id,
            command_name=data.command_name,
            frames=data.frames,
            interval=data.interval
        )
    return {"status": "ok", "command": f".{anim.command_name}"}


@app.get("/api/crm/contacts/{user_id}")
async def get_crm_contacts(user_id: int):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        notes = await repo.get_user_notes(user_id)
        tags = await repo.get_all_contact_tags(user_id)
        
    return {
        "notes": [{"id": n.id, "target_id": n.target_id, "name": n.target_name, "text": n.note_text, "date": n.created_at.strftime("%d.%m.%Y")} for n in notes],
        "tags": [{"target_id": t.target_id, "tag": t.tag_name} for t in tags]
    }


@app.get("/api/autoresponder/{user_id}")
async def get_autoresponder_settings(user_id: int):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        ar = await repo.get_auto_responder(user_id)
    return {
        "is_active": ar.is_active,
        "mode": ar.mode,
        "text_template": ar.text_template,
        "ai_prompt": ar.ai_prompt,
        "work_hours_start": ar.work_hours_start,
        "work_hours_end": ar.work_hours_end,
        "cooldown_minutes": ar.cooldown_minutes,
        "keywords": json.loads(ar.keywords_json or "[]")
    }


@app.post("/api/autoresponder/{user_id}")
async def update_autoresponder_settings(user_id: int, data: AutoResponderUpdate):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        ar = await repo.update_auto_responder(
            user_id=user_id,
            is_active=data.is_active,
            mode=data.mode,
            text_template=data.text_template,
            ai_prompt=data.ai_prompt,
            work_hours_start=data.work_hours_start,
            work_hours_end=data.work_hours_end,
            cooldown_minutes=data.cooldown_minutes,
            keywords_json=data.keywords_json
        )
    return {"status": "ok", "is_active": ar.is_active}


@app.get("/api/mutes/{user_id}")
async def get_mutes(user_id: int):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        mutes = await repo.get_user_mutes(user_id)
    return [
        {
            "id": m.id,
            "target_id": m.target_id,
            "target_name": m.target_name,
            "is_permanent": m.is_permanent,
            "muted_until": m.muted_until.strftime("%d.%m %H:%M") if m.muted_until else "Навсегда",
            "created_at": m.created_at.strftime("%d.%m.%Y")
        }
        for m in mutes
    ]


@app.post("/api/mutes/{user_id}")
async def add_mute(user_id: int, data: MuteCreate):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        m = await repo.mute_chat(
            user_id=user_id,
            target_id=data.target_id,
            target_name=data.target_name,
            duration_minutes=data.duration_minutes
        )
    return {"status": "ok", "target_name": m.target_name}


@app.delete("/api/mutes/{user_id}/{target_id}")
async def remove_mute(user_id: int, target_id: int):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        success = await repo.unmute_chat(user_id=user_id, target_id=target_id)
    return {"status": "ok" if success else "not_found"}


@app.get("/api/achievements/{user_id}")
async def get_achievements(user_id: int):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        achs = await repo.get_user_achievements(user_id)
    return [
        {
            "code": a.achievement_code,
            "title": a.title,
            "description": a.description,
            "icon": a.icon,
            "current_count": a.current_count,
            "target_count": a.target_count,
            "is_unlocked": a.is_unlocked,
            "progress_pct": min(100, int((a.current_count / a.target_count) * 100)) if a.target_count > 0 else 100
        }
        for a in achs
    ]


@app.post("/api/simulate/command")
async def simulate_command(req: CommandSimulateRequest):
    text = req.command_text.strip()
    if not text.startswith("."):
        return {"type": "plain", "result": text}

    cmd_raw = text[1:].strip()
    parts = cmd_raw.split(maxsplit=1)
    command_name = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # Voice command
    if command_name in ["гс", "voice", "голос"]:
        return {
            "type": "text",
            "result": f"🎙️ <b>[Голосовое сообщение (0:05)]:</b>\n<i>«{args or 'Привет! Это голосовое сообщение от бота.'}»</i> 🔊"
        }

    # QR command
    if command_name in ["qr", "кр"]:
        return {
            "type": "text",
            "result": (
                f"📱 <b>QR-код успешно сгенерирован:</b>\n"
                f"<code>[ ██████████████ ]\n"
                f"[ █  ██  ██  █ ]\n"
                f"[ █  ██  ██  █ ]\n"
                f"[ ██████████████ ]</code>\n"
                f"🔗 <b>Ссылка:</b> {args or 'https://t.me/evzhem_business_bot'}"
            )
        }

    # Dossier command
    if command_name in ["досье", "dossier"]:
        async with AsyncSessionLocal() as session:
            repo = Repository(session)
            stat = await repo.get_chat_stat(req.user_id, 1002)
            tags = await repo.get_tags_for_contact(req.user_id, 1002)
            notes = await repo.get_user_notes(req.user_id)
            dossier = crm_service.format_dossier("Мария ❤️", 1002, stat, tags, notes)
        return {"type": "text", "result": dossier}

    # Check / Receipt command
    if command_name in ["чек", "bill", "receipt"]:
        p = args.split(maxsplit=1)
        amt = p[0] if p else "15000"
        item = p[1] if len(p) > 1 else "Разработка бота"
        receipt = crm_service.generate_receipt(amt, item, "Евгений", "Мария ❤️")
        return {"type": "text", "result": receipt}

    # Summary command
    if command_name in ["суммари", "summary"]:
        summary_res = await ai_assistant.summarize_dialog(20)
        return {"type": "text", "result": summary_res}

    # Grammar fix
    if command_name in ["исправь", "fix"]:
        fixed = await ai_assistant.correct_grammar(args or "превет как дила я тут пишу бота")
        return {"type": "text", "result": fixed}

    # Style change
    if command_name in ["стиль", "деловой"]:
        styled = await ai_assistant.change_style("деловой", args or "дай мне отчет быстрее")
        return {"type": "text", "result": styled}

    # Translation
    if command_name in ["перевод", "translate"]:
        p = args.split(maxsplit=1)
        lang = p[0] if (len(p) >= 2 and len(p[0]) <= 3) else "en"
        tr_text = p[1] if (len(p) >= 2 and len(p[0]) <= 3) else args
        translated = await ai_assistant.translate_text(lang, tr_text or "Привет, мир!")
        return {"type": "text", "result": translated}

    # Check built-in animations
    clean_lower = cmd_raw.lower()
    for key, data in BUILTIN_ANIMATIONS.items():
        if clean_lower == key or clean_lower.startswith(key + " "):
            return {
                "type": "animation",
                "command": f".{key}",
                "interval": data.get("interval", 0.38),
                "frames": data["frames"]
            }

    if command_name in ["печать", "type", "print"]:
        target_text = args or "Привет! Это эффект живой печати ✨"
        frames = generate_typewriter_frames(target_text)
        return {
            "type": "animation",
            "command": ".печать",
            "interval": 0.3,
            "frames": frames
        }

    if clean_lower.startswith("наша стата") or command_name == "стата":
        async with AsyncSessionLocal() as session:
            repo = Repository(session)
            stat = await repo.get_chat_stat(req.user_id, 1002)
            if not stat:
                stat = await repo.record_message_stat(req.user_id, 1002, True, "Мария ❤️")
            card = stats_service.format_chat_stats_card(stat, "Евгений", "Мария ❤️")
        return {"type": "text", "result": card}

    if command_name in ["крипта", "курс", "btc", "ton"]:
        rates = await utilities_service.get_crypto_rates()
        return {"type": "text", "result": rates}

    if command_name in ["погода", "weather"]:
        w = await utilities_service.get_weather(args or "Москва")
        return {"type": "text", "result": w}

    if command_name in ["вики", "wiki"]:
        w = await utilities_service.get_wiki_summary(args or "Telegram")
        return {"type": "text", "result": w}

    if command_name in ["пароль", "pass"]:
        p = utilities_service.generate_password(int(args) if args.isdigit() else 12)
        return {"type": "text", "result": p}

    if command_name in ["комплимент", "хвали"]:
        return {"type": "text", "result": utilities_service.get_compliment()}

    if command_name in ["цитата", "мысль"]:
        return {"type": "text", "result": utilities_service.get_quote()}

    if command_name in ["анекдот", "шутка"]:
        return {"type": "text", "result": utilities_service.get_joke()}

    if command_name in ["кубик", "рандом"]:
        return {"type": "text", "result": utilities_service.roll_dice(int(args) if args.isdigit() else 100)}

    if command_name in ["монетка", "coin"]:
        return {"type": "text", "result": utilities_service.flip_coin()}

    if command_name in ["инфо", "ктоты"]:
        return {"type": "text", "result": utilities_service.scan_interlocutor("Мария ❤️")}

    if command_name in ["зеркало", "реверс"]:
        return {"type": "text", "result": f"🪞 <b>Зеркало:</b> <code>{utilities_service.reverse_text(args or 'Привет!')}</code>"}

    if command_name in ["калькулятор", "calc"]:
        res = utilities_service.calculate_expression(args)
        return {"type": "text", "result": res}

    if command_name in ["шрифт", "font"]:
        style = 1
        font_text = args
        p = args.split(maxsplit=1)
        if p and p[0].isdigit():
            style = int(p[0])
            font_text = p[1] if len(p) > 1 else ""
        res = utilities_service.apply_fancy_font(style, font_text)
        return {"type": "text", "result": res or "𝗧𝗲𝘅𝘁 𝗘𝘅𝗮𝗺𝗽𝗹𝗲"}

    if command_name in ["мут", "mute"]:
        return {
            "type": "text",
            "result": "🔇 <b>Собеседник замучен!</b>\n<i>Все входящие сообщения в этом диалоге будут мгновенно удаляться.</i>"
        }

    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        custom_anim = await repo.get_custom_animation(req.user_id, command_name)
        if custom_anim:
            return {
                "type": "animation",
                "command": f".{custom_anim.command_name}",
                "interval": custom_anim.interval_seconds,
                "frames": json.loads(custom_anim.frames_json)
            }

    return {
        "type": "text",
        "result": f"❓ Команда <code>.{command_name}</code> не найдена. Откройте вкладку «База функций» для списка команд!"
    }
