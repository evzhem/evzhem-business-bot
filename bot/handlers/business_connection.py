import logging
from aiogram import Router, Bot
from aiogram.types import BusinessConnection
from database.db import AsyncSessionLocal
from database.repository import Repository
from bot.keyboards.inline import get_main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.business_connection()
async def handle_business_connection_update(connection: BusinessConnection, bot: Bot):
    logger.info(
        f"Business connection update: id={connection.id}, user={connection.user.id}, "
        f"can_reply={connection.can_reply}, is_enabled={connection.is_enabled}"
    )

    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        # Register or update user
        await repo.get_or_create_user(
            telegram_id=connection.user.id,
            username=connection.user.username,
            first_name=connection.user.first_name
        )
        # Save business connection
        await repo.save_or_update_business_conn(
            connection_id=connection.id,
            user_id=connection.user.id,
            user_chat_id=connection.user_chat_id,
            can_reply=connection.can_reply,
            is_enabled=connection.is_enabled,
            rights_summary="5/5 (Full Rights)" if connection.can_reply else "Partial Rights"
        )

    if connection.is_enabled and connection.can_reply:
        try:
            await bot.send_message(
                chat_id=connection.user.id,
                text=(
                    f"🎉 <b>Поздравляем! Бот успешно подключен к вашему Telegram Business!</b> 🍀\n\n"
                    f"✨ <i>Теперь в любых ваших личных диалогах доступны анимации, эффект живой печати, "
                    f"умный мут и автоответчик.</i>\n\n"
                    f"💡 <b>Быстрый старт:</b>\n"
                    f"• Напишите в любом ЛС: <code>.люблю</code> или <code>.печать Привет!</code>\n"
                    f"• Посмотрите статистику переписки: <code>.наша стата</code>\n"
                    f"• Заглушите спамера: <code>.мут</code>\n\n"
                    f"👇 Откройте панель управления для настройки:"
                ),
                reply_markup=get_main_menu_keyboard(autoresponder_active=False)
            )
        except Exception as e:
            logger.error(f"Failed to send business connection welcome: {e}")
    elif not connection.is_enabled:
        try:
            await bot.send_message(
                chat_id=connection.user.id,
                text="⚠️ <b>Бот был отключен от вашего профиля Telegram Business.</b>\nЧтобы вернуть автоматизацию, включите бота в настройках чатов."
            )
        except Exception as e:
            logger.error(f"Failed to send disconnection notice: {e}")
