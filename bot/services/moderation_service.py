import asyncio
import logging
import re
from typing import Optional, List
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


class ModerationService:
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot

    async def delete_message_safe(
        self,
        business_connection_id: str,
        chat_id: int,
        message_id: int
    ) -> bool:
        if not self.bot:
            return False
        try:
            # Official Telegram Bot API 7.2+ method for Business messages
            if hasattr(self.bot, "delete_business_messages"):
                await self.bot.delete_business_messages(
                    business_connection_id=business_connection_id,
                    message_ids=[message_id]
                )
                logger.info(f"Successfully deleted business message {message_id} via delete_business_messages")
                return True
            else:
                # Fallback
                await self.bot.delete_messages(chat_id=chat_id, message_ids=[message_id])
                return True
        except TelegramBadRequest as e:
            logger.warning(f"TelegramBadRequest deleting message {message_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error in delete_message_safe: {e}", exc_info=True)
            return False

    async def schedule_self_destruct(
        self,
        business_connection_id: str,
        chat_id: int,
        message_id: int,
        seconds: int
    ) -> None:
        async def _destruct():
            await asyncio.sleep(seconds)
            await self.delete_message_safe(business_connection_id, chat_id, message_id)

        asyncio.create_task(_destruct())

    async def run_spam_safe(
        self,
        business_connection_id: str,
        chat_id: int,
        text: str,
        count: int = 10,
        max_limit: int = 30
    ) -> int:
        if not self.bot:
            return 0
        actual_count = min(count, max_limit)
        sent = 0
        for i in range(actual_count):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"{text} ({i+1}/{actual_count})",
                    business_connection_id=business_connection_id
                )
                sent += 1
                await asyncio.sleep(0.4)
            except Exception as e:
                logger.error(f"Spam stopped due to error: {e}")
                break
        return sent


moderation_service = ModerationService()
