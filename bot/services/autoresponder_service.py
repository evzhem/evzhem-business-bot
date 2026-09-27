import asyncio
import json
import logging
from datetime import datetime, time
from typing import Dict, Tuple, Optional
from aiogram import Bot
from config import settings
from database.models import AutoResponderSetting

logger = logging.getLogger(__name__)

# Cooldown memory store: (user_id, interlocutor_chat_id) -> last_reply_timestamp
COOLDOWN_CACHE: Dict[Tuple[int, int], datetime] = {}


class AutoResponderService:
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot

    def is_in_cooldown(self, user_id: int, chat_id: int, cooldown_minutes: int) -> bool:
        key = (user_id, chat_id)
        last_time = COOLDOWN_CACHE.get(key)
        if not last_time:
            return False
        diff = (datetime.utcnow() - last_time).total_seconds() / 60
        return diff < cooldown_minutes

    def mark_replied(self, user_id: int, chat_id: int) -> None:
        key = (user_id, chat_id)
        COOLDOWN_CACHE[key] = datetime.utcnow()

    def is_within_schedule(self, start_str: str, end_str: str) -> bool:
        try:
            sh, sm = map(int, start_str.split(":"))
            eh, em = map(int, end_str.split(":"))
            start_t = time(sh, sm)
            end_t = time(eh, em)
            now_t = datetime.utcnow().time()

            if start_t <= end_t:
                return start_t <= now_t <= end_t
            else:
                # Night crossover (e.g., 23:00 to 08:00)
                return now_t >= start_t or now_t <= end_t
        except Exception as e:
            logger.error(f"Error checking schedule: {e}")
            return True

    async def generate_ai_reply(self, prompt: str, incoming_text: str) -> str:
        """Calls OpenAI or intelligent fallback."""
        if settings.OPENAI_API_KEY:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": settings.OPENAI_MODEL,
                            "messages": [
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": incoming_text}
                            ],
                            "max_tokens": 120,
                            "temperature": 0.7
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"AI auto-responder request failed: {e}")

        # Intelligent fallback when no API key is provided
        return f"🤖 [AI-Ассистент]: Сообщение принято! Владелец аккаунта скоро освободится и ответит вам лично."

    async def check_and_reply(
        self,
        business_conn_id: str,
        user_id: int,
        chat_id: int,
        incoming_text: str,
        setting: AutoResponderSetting
    ) -> Optional[str]:
        if not setting.is_active or not self.bot:
            return None

        # Check cooldown
        if self.is_in_cooldown(user_id, chat_id, setting.cooldown_minutes):
            return None

        reply_text: Optional[str] = None

        if setting.mode == "simple":
            reply_text = setting.text_template

        elif setting.mode == "schedule":
            if self.is_within_schedule(setting.work_hours_start, setting.work_hours_end):
                reply_text = setting.text_template
            else:
                return None

        elif setting.mode == "keywords":
            try:
                kw_list = json.loads(setting.keywords_json or "[]")
                incoming_lower = incoming_text.lower()
                for item in kw_list:
                    kw = item.get("keyword", "").lower()
                    if kw and kw in incoming_lower:
                        reply_text = item.get("reply", setting.text_template)
                        break
            except Exception as e:
                logger.error(f"Error parsing keywords: {e}")
                reply_text = setting.text_template

        elif setting.mode == "ai":
            reply_text = await self.generate_ai_reply(setting.ai_prompt, incoming_text)

        if reply_text:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=reply_text,
                    business_connection_id=business_conn_id
                )
                self.mark_replied(user_id, chat_id)
                return reply_text
            except Exception as e:
                logger.error(f"Failed to send autoresponder message: {e}")

        return None


auto_responder_service = AutoResponderService()
