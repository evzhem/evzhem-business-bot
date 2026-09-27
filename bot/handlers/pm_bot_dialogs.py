import html
import asyncio
import logging
import re
from datetime import datetime
from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from config import settings
from database.db import AsyncSessionLocal
from database.repository import Repository
from bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_back_keyboard,
    get_catalog_keyboard,
    get_premium_buy_keyboard
)
from bot.services.stats_service import stats_service
from bot.services.animation_engine import BUILTIN_ANIMATIONS, generate_typewriter_frames, animation_engine
from bot.services.voice_service import voice_service
from bot.services.qr_service import qr_service
from bot.services.crm_service import crm_service
from bot.services.ai_assistant_service import ai_assistant
from bot.services.utilities_service import utilities_service

logger = logging.getLogger(__name__)
router = Router()


async def safe_answer(call: CallbackQuery, text: str = None, show_alert: bool = False):
    try:
        if text:
            await call.answer(text=text, show_alert=show_alert)
        else:
            await call.answer()
    except Exception:
        pass


@router.message(CommandStart())
@router.message(Command("menu"))
async def handle_start(message: Message, bot: Bot):
    try:
        user_id = message.from_user.id
        raw_name = message.from_user.first_name or message.from_user.username or "Пользователь"
        clean_name = html.escape(raw_name)
        username = message.from_user.username

        referrer_id = None
        parts = message.text.split()
        if len(parts) > 1 and parts[1].startswith("ref_") and parts[1][4:].isdigit():
            referrer_id = int(parts[1][4:])

        async with AsyncSessionLocal() as session:
            repo = Repository(session)
            user = await repo.get_or_create_user(
                telegram_id=user_id,
                username=username,
                first_name=raw_name,
                referrer_id=referrer_id
            )
            b_conn = await repo.get_business_conn_by_user(user_id)
            ar = await repo.get_auto_responder(user_id)

        status_icon = "🟢 Подключён (5/5)" if (b_conn and b_conn.is_enabled) else "🔴 Не подключён к Business"
        plan_title = "👑 VIP Премиум" if user.is_premium else "Стандартный доступ"

        text = (
            f"🏢 <b>ПАНЕЛЬ УПРАВЛЕНИЯ | @{settings.BOT_USERNAME}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Интеллектуальный сервис автоматизации и прокачки личных чатов Telegram Business.</i>\n\n"
            f"📱 <b>Статус интеграции:</b> {status_icon}\n"
            f"⭐ <b>Тарифный план:</b> {plan_title}\n"
            f"👤 <b>Пользователь:</b> {clean_name} (<code>{user_id}</code>)\n\n"
            f"<b>Ключевые модули системы:</b>\n"
            f"• 🎙️ <b>Синтез речи</b> — голосовые сообщения из текста (<code>.гс</code>)\n"
            f"• 💼 <b>Личный CRM</b> — досье, заметки, теги и чеки (<code>.досье</code>, <code>.чек</code>)\n"
            f"• 🧠 <b>AI-Ассистент</b> — суммаризация, перевод и авто-корректор\n"
            f"• 💫 <b>Живые анимации</b> — эффект набора и трансформеры (<code>.люблю</code>, <code>.печать</code>)\n"
            f"• 🔇 <b>Приватность</b> — тихий мут спамеров и секретный таймер\n\n"
            f"👇 <i>Используйте меню ниже для выбора раздела:</i>"
        )

        await message.answer(
            text=text,
            reply_markup=get_main_menu_keyboard(
                autoresponder_active=ar.is_active,
                webapp_url=settings.WEBAPP_BASE_URL
            )
        )
    except Exception as e:
        logger.error(f"Error handling /start: {e}", exc_info=True)
        await message.answer(f"👋 Добро пожаловать! Бот активен. Напишите <code>.люблю</code> или <code>.печать Привет</code>!")


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery):
    await safe_answer(call)
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        user = await repo.get_or_create_user(call.from_user.id)
        b_conn = await repo.get_business_conn_by_user(call.from_user.id)
        ar = await repo.get_auto_responder(call.from_user.id)

    status_icon = "🟢 Подключён (5/5)" if (b_conn and b_conn.is_enabled) else "🔴 Не подключён"

    text = (
        f"🏢 <b>ГЛАВНОЕ МЕНЮ | @{settings.BOT_USERNAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Интеграция Business: {status_icon}\n"
        f"⭐ Тариф: {'👑 VIP Премиум' if user.is_premium else 'Стандарт'}\n\n"
        f"Выберите категорию функций:"
    )
    try:
        await call.message.edit_text(
            text=text,
            reply_markup=get_main_menu_keyboard(autoresponder_active=ar.is_active)
        )
    except Exception:
        pass


# 1. CATALOG OF COMMANDS
@router.callback_query(F.data == "btn_catalog")
async def cb_catalog(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"📚 <b>БАЗА ЗНАНИЙ: ВСЕ 35+ КОМАНД СИСТЕМЫ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Все команды пишутся с точкой в начале в любых диалогах.</i>\n\n"
        f"Выберите категорию для просмотра подробных инструкций и примеров:"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_catalog_keyboard())
    except Exception:
        pass


@router.callback_query(F.data == "cat_voice")
async def cb_cat_voice(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"🎙️ <b>ГОЛОСОВОЙ МОДУЛЬ И МУЛЬТИМЕДИА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <code>.гс Текст</code> — генерирует настоящее голосовое сообщение от вашего имени с реалистичной речью.\n"
        f"• <code>.voice Hello world</code> — англоязычная озвучка.\n"
        f"• <code>.qr https://site.ru</code> — создает аккуратное фото QR-кода прямо в переписке.\n"
        f"• <code>.шрифт 1 Текст</code> — жирный шрифт Unicode.\n"
        f"• <code>.зеркало Текст</code> — переворот текста задом наперед.\n"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard("btn_catalog"))
    except Exception:
        pass


@router.callback_query(F.data == "cat_crm")
async def cb_cat_crm(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"💼 <b>ЛИЧНЫЙ CRM, ДОСЬЕ И ФИНАНСЫ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <code>.досье</code> — открыть полную карточку собеседника (теги, заметки, баланс переписки).\n"
        f"• <code>.тег VIP</code> — присвоить метку человеку (#Клиент, #Партнер, #Друг).\n"
        f"• <code>.заметка Любит чай без сахара</code> — сохранить важную деталь о друге.\n"
        f"• <code>.чек 15000 Разработка бота</code> — создать стильный электронный чек об оплате со штрихкодом.\n"
        f"• <code>.напоминание 10 Позвонить</code> — отложенное напоминание в чат через 10 минут.\n"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard("btn_catalog"))
    except Exception:
        pass


@router.callback_query(F.data == "cat_ai")
async def cb_cat_ai(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"🧠 <b>AI-ИНТЕЛЛЕКТ И РАБОТА С ТЕКСТОМ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <code>.суммари 20</code> — выжимка последних 20 сообщений диалога (темы, задачи, договоренности).\n"
        f"• <code>.исправь Текст</code> — автокорректор грамматики и опечаток.\n"
        f"• <code>.стиль деловой Текст</code> — переписывание текста в строгий бизнес-стиль.\n"
        f"• <code>.перевод en Текст</code> — синхронный переводчик на английский, немецкий, китайский.\n"
        f"• <code>.ai Вопрос</code> — быстрый емкий ответ ChatGPT прямо в тело сообщения.\n"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard("btn_catalog"))
    except Exception:
        pass


@router.callback_query(F.data == "cat_anim")
async def cb_cat_anim(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"💫 <b>ЖИВЫЕ АНИМАЦИИ И ТРАНСФОРМЕРЫ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <code>.люблю</code> — признание в любви с замком ❤️🔒\n"
        f"• <code>.печать Текст</code> — эффект пишущей машинки (набор по буквам)\n"
        f"• <code>.сердце</code> — пульсирующее сердце 🫀\n"
        f"• <code>.корона</code> — золотая коронация 👑\n"
        f"• <code>.дождь</code> — гроза и радуга 🌦️🌈\n"
        f"• <code>.костер</code> — уютный потрескивающий костер 🔥\n"
        f"• <code>.фейерверк</code> — праздничный салют 🎆\n"
        f"• <code>.иди нахуй</code> — трансформация грубости в букет роз 🌹\n"
        f"• <code>.загрузка</code> — прогресс-бар 0-100%\n"
        f"• <code>.матрица</code> — бегущий код матрицы 🟢\n"
        f"• <code>.ты</code> / <code>.писюн</code> — юмор 18+\n"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard("btn_catalog"))
    except Exception:
        pass


@router.callback_query(F.data == "cat_mod")
async def cb_cat_mod(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"🔇 <b>МОДЕРАЦИЯ И ПРИВАТНОСТЬ В ЛС</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <code>.мут</code> — мгновенно удалять входящие сообщения от собеседника.\n"
        f"• <code>.мут 15м</code> — мут на 15 минут с автоматическим размутом.\n"
        f"• <code>.размут</code> — вернуть возможность писать.\n"
        f"• <code>.антимут</code> — добавить близкого человека в Белый список.\n"
        f"• <code>.самоуничтожение 10 Текст</code> — удалить сообщение через 10 секунд.\n"
        f"• <code>.спам 'Текст' 10</code> — контролируемый безопасный спам.\n"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard("btn_catalog"))
    except Exception:
        pass


@router.callback_query(F.data == "cat_utils")
async def cb_cat_utils(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"💎 <b>ФИНАНСЫ, АНАЛИТИКА И РАЗВЛЕЧЕНИЯ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <code>.наша стата</code> — карточка переписки (баланс, ранг, активность).\n"
        f"• <code>.крипта</code> — актуальные курсы BTC, ETH, TON, SOL.\n"
        f"• <code>.погода Москва</code> — температура, влажность, ветер.\n"
        f"• <code>.пароль 16</code> — генератор безопасного пароля.\n"
        f"• <code>.калькулятор 150*4 + 80</code> — расчет математических выражений.\n"
        f"• <code>.вики Телеграм</code> — быстрая справка из энциклопедии.\n"
        f"• <code>.инфо</code> — шуточный сканер собеседника (IQ, токсичность, вайб).\n"
        f"• <code>.кубик 100</code> / <code>.монетка</code> — кости или орел/решка.\n"
        f"• <code>.комплимент</code> / <code>.цитата</code> / <code>.анекдот</code> — генераторы фраз.\n"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard("btn_catalog"))
    except Exception:
        pass


# 2. CRM SCREEN
@router.callback_query(F.data == "btn_crm")
async def cb_crm(call: CallbackQuery):
    await safe_answer(call)
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        notes = await repo.get_user_notes(call.from_user.id)
        tags = await repo.get_all_contact_tags(call.from_user.id)

    notes_str = "\n".join([f"• 👤 <b>{html.escape(n.target_name or 'Контакт')}:</b> {html.escape(n.note_text)}" for n in notes[:5]]) if notes else "<i>Заметок пока нет</i>"
    tags_str = ", ".join([f"<code>#{html.escape(t.tag_name)}</code>" for t in tags[:8]]) if tags else "<i>Тегов пока нет</i>"

    text = (
        f"💼 <b>ЛИЧНЫЙ CRM-ОРГАНАЙЗЕР</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Управляйте информацией о ваших клиентах и контактах прямо из диалогов:\n\n"
        f"🏷 <b>Активные теги:</b> {tags_str}\n\n"
        f"📝 <b>Последние заметки:</b>\n{notes_str}\n\n"
        f"💡 <b>Команды в любом диалоге:</b>\n"
        f"• <code>.досье</code> — открыть карточку собеседника\n"
        f"• <code>.тег Название</code> — добавить метку\n"
        f"• <code>.заметка Текст</code> — сохранить заметку\n"
        f"• <code>.чек Сумма Услуга</code> — выписать чек об оплате"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 3. VOICE INFO SCREEN
@router.callback_query(F.data == "btn_voice_info")
async def cb_voice_info(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"🎙️ <b>ГОЛОСОВОЙ МОДУЛЬ (TEXT-TO-SPEECH)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Бот умеет синтезировать реалистичную человеческую речь и отправлять её в виде **настоящих голосовых сообщений** от вашего имени.\n\n"
        f"💡 <b>Как использовать:</b>\n"
        f"1. Откройте любой диалог с другом или клиентом (или отправьте прямо сюда!).\n"
        f"2. Отправьте сообщение: <code>.гс Привет! Сейчас не могу говорить, перезвоню через 10 минут</code>\n"
        f"3. Бот сразу пришлет аудиозапись речи!\n\n"
        f"📱 Также доступна команда <code>.qr [ссылка]</code> для генерации QR-кодов."
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 4. SMILES SCREEN
@router.callback_query(F.data == "btn_smiles")
async def cb_smiles(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"💫 <b>ЖИВЫЕ СМАЙЛЫ И АНИМАЦИИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Отправляйте эти команды в любой ЛС диалог:</i>\n\n"
        f"💖 <code>.люблю</code> — признание в любви с замком\n"
        f"⌨️ <code>.печать Текст</code> — эффект пишущей машинки\n"
        f"🫀 <code>.сердце</code> — пульсирующее сердце\n"
        f"👑 <code>.корона</code> — коронация короля/королевы\n"
        f"🌦️ <code>.дождь</code> — гроза и радуга\n"
        f"🔥 <code>.костер</code> — уютный костер\n"
        f"🎆 <code>.фейерверк</code> — праздничный салют\n"
        f"🌹 <code>.иди нахуй</code> — трансформация в букет роз\n"
        f"⏳ <code>.загрузка</code> — прогресс-бар 0-100%\n"
        f"🟢 <code>.матрица</code> — код матрицы\n"
        f"😏 <code>.ты</code> / 🍌 <code>.писюн</code> — юмор 18+\n"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 5. MODERATION SCREEN
@router.callback_query(F.data == "btn_moderation_info")
async def cb_mod_info(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"🔇 <b>ТИХИЙ МУТ И ПРИВАТНОСТЬ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <code>.мут</code> — входящие сообщения от собеседника мгновенно и бесшумно удаляются.\n"
        f"• <code>.мут 15м</code> — мут на 15 минут с автоматическим размутом.\n"
        f"• <code>.размут</code> — вернуть возможность писать.\n"
        f"• <code>.антимут</code> — добавить контакт в Белый список.\n"
        f"• <code>.самоуничтожение 10 Текст</code> — удалить сообщение через 10 секунд."
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 6. STATUS SCREEN
@router.callback_query(F.data == "btn_status")
async def cb_status(call: CallbackQuery):
    await safe_answer(call)
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        user = await repo.get_or_create_user(call.from_user.id)
        b_conn = await repo.get_business_conn_by_user(call.from_user.id)

    if b_conn and b_conn.is_enabled:
        conn_text = "🟢 <b>Бот успешно интегрирован в Telegram Business</b>\nПрава: 5/5 (чтение, ответы, удаление входящих и исходящих)"
    else:
        conn_text = "🔴 <b>Интеграция не активна</b>\n<i>Перейдите в Настройки Telegram ➔ Telegram Business ➔ Чат-боты и добавьте @evzhem_business_bot.</i>"

    text = (
        f"👤 <b>ИНФОРМАЦИЯ О ПОДКЛЮЧЕНИИ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"👤 Имя: <b>{html.escape(call.from_user.first_name or 'Пользователь')}</b>\n"
        f"⭐ Тариф: <b>{'👑 VIP Премиум' if user.is_premium else 'Стандартный'}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{conn_text}"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 7. ACHIEVEMENTS SCREEN
@router.callback_query(F.data == "btn_achievements")
async def cb_achievements(call: CallbackQuery):
    await safe_answer(call)
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        achs = await repo.get_user_achievements(call.from_user.id)

    text = "🏆 <b>ДОСТИЖЕНИЯ И НАГРАДЫ</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for a in achs:
        status = "✅ ВЫПОЛНЕНО" if a.is_unlocked else f"⏳ {a.current_count}/{a.target_count}"
        text += f"{a.icon} <b>{a.title}</b> — {status}\n└ <i>{a.description}</i>\n\n"

    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 8. ANALYTICS SCREEN
@router.callback_query(F.data == "btn_analytics")
async def cb_analytics(call: CallbackQuery):
    await safe_answer(call)
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        stats = await repo.get_global_user_stats(call.from_user.id)

    text = stats_service.format_global_stats(stats, call.from_user.first_name or "Пользователь")
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 9. TOGGLE AUTORESPONDER
@router.callback_query(F.data == "toggle_autoresponder")
async def cb_toggle_autoresponder(call: CallbackQuery):
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        ar = await repo.get_auto_responder(call.from_user.id)
        new_state = not ar.is_active
        await repo.update_auto_responder(call.from_user.id, is_active=new_state)

    state_word = "ВКЛЮЧЕН 🟢" if new_state else "ВЫКЛЮЧЕН 🔴"
    await safe_answer(call, f"Автоответчик {state_word}!", show_alert=True)

    try:
        await call.message.edit_reply_markup(
            reply_markup=get_main_menu_keyboard(autoresponder_active=new_state)
        )
    except Exception:
        pass


# 10. TUTORIAL SCREEN
@router.callback_query(F.data == "btn_tutorial")
async def cb_tutorial(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"🎬 <b>ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ К TELEGRAM BUSINESS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ Откройте настройки Telegram на телефоне.\n"
        f"2️⃣ Перейдите в раздел <b>Telegram Business ➔ Чат-боты</b> (или <i>«Автоматизация чатов»</i>).\n"
        f"3️⃣ В строке поиска введите юзернейм: <code>@{settings.BOT_USERNAME}</code>\n"
        f"4️⃣ Нажмите <b>«Добавить»</b> и выдайте все 5 прав:\n"
        f"   • Чтение сообщений\n"
        f"   • Ответы на сообщения\n"
        f"   • Отметки о прочтении\n"
        f"   • Удаление исходящих\n"
        f"   • Удаление входящих\n\n"
        f"✅ <i>Готово! Бот мгновенно начнет обрабатывать команды с точкой в любых личных чатах!</i>"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_back_keyboard())
    except Exception:
        pass


# 11. PREMIUM SCREEN
@router.callback_query(F.data == "btn_premium")
async def cb_premium(call: CallbackQuery):
    await safe_answer(call)
    text = (
        f"⭐ <b>VIP ПРЕМИУМ ТАРИФ | @{settings.BOT_USERNAME}</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Откройте максимальные возможности сервиса:\n\n"
        f"✨ Все эксклюзивные и 18+ анимации (.матрица, .ты, .писюн)\n"
        f"🎙️ Неограниченный синтез голосовых сообщений (.гс)\n"
        f"🧠 Smart AI автоответчик на базе GPT-4o с поддержанием контекста\n"
        f"💼 Полный доступ к модулю CRM и конструктору шаблонов\n"
        f"🚀 Приоритетная очередь обработки и отсутствие задержек\n\n"
        f"👇 <i>Выберите период подписки (оплата Telegram Stars ⭐):</i>"
    )
    try:
        await call.message.edit_text(text=text, reply_markup=get_premium_buy_keyboard())
    except Exception:
        pass


# ================= DIRECT PM COMMANDS HANDLER =================
@router.message(F.text)
async def handle_direct_pm_messages(message: Message, bot: Bot):
    text = message.text.strip()
    user_id = message.from_user.id
    
    # If it's a dot-command sent directly to the bot in PM:
    if text.startswith("."):
        parts = text[1:].split(maxsplit=1)
        command_name = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        # Voice command in PM
        if command_name in ["гс", "voice", "голос"]:
            voice_text = args if args else "Привет! Это проверка голосового модуля."
            voice_bytes = await voice_service.text_to_speech(voice_text, voice_service.DEFAULT_VOICE)
            if voice_bytes:
                voice_file = BufferedInputFile(voice_bytes, filename="voice.ogg")
                await message.reply_voice(voice=voice_file, caption=f"🎙️ <i>Озвучка: «{voice_text[:40]}...»</i>")
            else:
                await message.reply("❌ Не удалось синтезировать голос.")
            return

        # QR command in PM
        if command_name in ["qr", "куар"]:
            target_data = args if args else f"https://t.me/{settings.BOT_USERNAME}"
            qr_bytes = qr_service.generate_qr(target_data)
            photo_file = BufferedInputFile(qr_bytes, filename="qr.png")
            await message.reply_photo(photo=photo_file, caption=f"📱 <b>QR-код сгенерирован:</b>\n<code>{target_data}</code>")
            return

        # Calculator in PM
        if command_name in ["калькулятор", "calc", "посчитай"]:
            expr = args if args else "2+2"
            res = utilities_service.calculate_expression(expr)
            await message.reply(f"🧮 <b>Расчёт:</b> <code>{expr}</code> = <b>{res}</b>")
            return

        # AI prompt in PM
        if command_name in ["ai", "ии", "gpt"]:
            prompt = args if args else "Расскажи интересный факт о технологиях"
            wait_msg = await message.reply("🧠 <i>AI думает...</i>")
            ans = await ai_assistant.ask_assistant(prompt)
            await wait_msg.edit_text(f"🧠 <b>AI Ответ:</b>\n\n{ans}")
            return

        # Animations in PM
        if command_name in BUILTIN_ANIMATIONS:
            anim_dict = BUILTIN_ANIMATIONS[command_name]
            frames = anim_dict["frames"] if isinstance(anim_dict, dict) and "frames" in anim_dict else anim_dict
            interval = anim_dict.get("interval", 0.38) if isinstance(anim_dict, dict) else 0.38
            anim_msg = await message.reply(frames[0])
            for frame in frames[1:]:
                await asyncio.sleep(interval)
                try:
                    await anim_msg.edit_text(frame)
                except Exception:
                    pass
            return

        if command_name in ["печать", "print"]:
            target_text = args if args else "Привет! Это эффект живой печати ✨"
            frames = generate_typewriter_frames(target_text)
            anim_msg = await message.reply(frames[0])
            for frame in frames[1:]:
                await asyncio.sleep(0.3)
                try:
                    await anim_msg.edit_text(frame)
                except Exception:
                    pass
            return

        # Check / Receipt in PM
        if command_name in ["чек", "receipt"]:
            check_text = crm_service.generate_receipt(
                amount=args.split()[0] if args else "5000",
                item_name=" ".join(args.split()[1:]) if len(args.split()) > 1 else "Услуги разработки",
                sender_name=message.from_user.first_name or "Исполнитель",
                client_name="Клиент"
            )
            await message.reply(check_text)
            return

        # Weather in PM
        if command_name in ["погода", "weather"]:
            city = args if args else "Москва"
            w = await utilities_service.get_weather_card(city)
            await message.reply(w)
            return

        # Crypto in PM
        if command_name in ["крипта", "crypto"]:
            c = await utilities_service.get_crypto_card()
            await message.reply(c)
            return

        # Password in PM
        if command_name in ["пароль", "pass"]:
            p = utilities_service.generate_password(int(args) if args.isdigit() else 16)
            await message.reply(f"🔐 <b>Сгенерированный надёжный пароль:</b>\n<code>{p}</code>")
            return

        # Other fun utilities
        if command_name in ["комплимент", "цитата", "анекдот", "монетка", "кубик"]:
            if command_name == "комплимент":
                await message.reply(utilities_service.get_compliment())
            elif command_name == "цитата":
                await message.reply(utilities_service.get_quote())
            elif command_name == "анекдот":
                await message.reply(utilities_service.get_joke())
            elif command_name == "монетка":
                await message.reply(utilities_service.flip_coin())
            elif command_name == "кубик":
                await message.reply(utilities_service.roll_dice(int(args) if args.isdigit() else 6))
            return

    # If user sends plain text in bot's PM, show menu and helpful tips
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        ar = await repo.get_auto_responder(user_id)

    await message.reply(
        "👋 Чтобы настроить бота, используйте кнопки ниже.\n\n"
        "💡 <b>Для работы команд в личных переписках:</b>\n"
        "1. Подключите бота в <b>Telegram Business ➔ Чат-боты</b>\n"
        "2. Пишите команды с точкой (<code>.люблю</code>, <code>.гс Привет</code>, <code>.досье</code>) в диалогах с собеседниками!",
        reply_markup=get_main_menu_keyboard(autoresponder_active=ar.is_active)
    )
