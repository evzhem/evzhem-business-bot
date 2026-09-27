import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
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
from webapp.backend.app import app as webapp_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("evzhem_unified_service")


async def run_bot_polling_forever():
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting Telegram Bot continuous polling loop...")
    while True:
        try:
            bot = Bot(
                token=settings.BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            dp = Dispatcher()

            # Include all handlers
            dp.include_router(business_conn_router)
            dp.include_router(business_messages_router)
            dp.include_router(pm_dialogs_router)
            dp.include_router(payments_router)

            logger.info("Aiogram Polling active for @evzhem_business_bot")
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
            logger.warning(f"Network glitch: {e}. Reconnecting bot in 1s...")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Unexpected error in bot polling: {e}", exc_info=True)
            await asyncio.sleep(2)
        finally:
            try:
                await bot.session.close()
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Launch Bot polling task on server startup
    bot_task = asyncio.create_task(run_bot_polling_forever())
    logger.info("🚀 Background Telegram Bot task spawned successfully!")
    yield
    logger.info("Shutting down background bot task...")
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass


# Attach lifespan to FastAPI WebApp
webapp_app.router.lifespan_context = lifespan


async def main():
    config = uvicorn.Config(
        app=webapp_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
