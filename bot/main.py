import asyncio
import logging
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramNetworkError, TelegramAPIError
from config import settings
from database.db import init_db
from bot.handlers.business_connection import router as business_conn_router
from bot.handlers.business_messages import router as business_messages_router
from bot.handlers.pm_bot_dialogs import router as pm_dialogs_router
from bot.handlers.payments import router as payments_router

# Setup double logging (Console + Rotating File bot.log)
log_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# File Handler (bot.log)
file_handler = RotatingFileHandler(
    filename="bot.log",
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger("evzhem_bot")


async def create_bot_and_dispatcher():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register Routers
    dp.include_router(business_conn_router)
    dp.include_router(business_messages_router)
    dp.include_router(pm_dialogs_router)
    dp.include_router(payments_router)

    return bot, dp


async def main():
    logger.info("==========================================")
    logger.info("Initializing evzhem_business_bot system...")
    logger.info("==========================================")
    await init_db()

    # Resilient Polling Loop with Auto-Reconnect
    while True:
        bot, dp = await create_bot_and_dispatcher()
        try:
            logger.info("Starting Telegram Polling loop for @evzhem_business_bot...")
            await dp.start_polling(
                bot,
                allowed_updates=[
                    "message",
                    "edited_message",
                    "business_connection",
                    "business_message",
                    "edited_business_message",
                    "deleted_business_messages",
                    "callback_query",
                    "pre_checkout_query"
                ],
                handle_signals=False,
                polling_timeout=20
            )
        except (TelegramNetworkError, asyncio.TimeoutError) as e:
            logger.warning(f"Telegram Network connection drop: {e}. Reconnecting in 1 second...")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Critical exception in bot loop: {e}", exc_info=True)
            await asyncio.sleep(2)
        finally:
            try:
                await bot.session.close()
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
