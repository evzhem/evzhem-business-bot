import asyncio
import logging
from typing import Dict, List, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

logger = logging.getLogger(__name__)

BUILTIN_ANIMATIONS: Dict[str, Dict] = {
    "люблю": {
        "title": "Признание в любви",
        "category": "romance",
        "is_premium": False,
        "interval": 0.38,
        "frames": [
            "🖤",
            "❤️",
            "💖",
            "Я ❤️",
            "Я ❤️ тебя",
            "Я люблю ❤️ тебя",
            "Я люблю тебя больше жизни 💖✨",
            "🔒 *Любовь сохранена навсегда* ❤️🔐"
        ]
    },
    "сердце": {
        "title": "Пульсирующее сердце",
        "category": "romance",
        "is_premium": False,
        "interval": 0.35,
        "frames": [
            "🤍",
            "💛",
            "🧡",
            "❤️",
            "💖",
            "💓",
            "💗",
            "Моё сердце бьется для тебя 🫀✨"
        ]
    },
    "сладких снов": {
        "title": "Сладких снов",
        "category": "wishes",
        "is_premium": False,
        "interval": 0.4,
        "frames": [
            "🌙",
            "🌙 ✨",
            "🌙 ✨ Сладких...",
            "🌙 ✨ Сладких снов...",
            "🌙 ✨ Сладких снов и волшебных сновидений! 💤🛌"
        ]
    },
    "доброе утро": {
        "title": "Доброе утро",
        "category": "wishes",
        "is_premium": False,
        "interval": 0.4,
        "frames": [
            "⛅",
            "☀️",
            "☀️ ☕",
            "☀️ ☕ Доброе...",
            "☀️ ☕ Доброе утро! 🥐",
            "☀️ ☕ Прекрасного и легкого дня! ✨💛"
        ]
    },
    "иди нахуй": {
        "title": "Трансформация в розу",
        "category": "fun",
        "is_premium": False,
        "interval": 0.42,
        "frames": [
            "Иди нахуй...",
            "Иди на... 🥀",
            "Иди... 🌱",
            "Держи... 🌿",
            "Держи розочку 🌹",
            "Держи букет роз! 🌹💐❤️"
        ]
    },
    "роза": {
        "title": "Распускающаяся роза",
        "category": "romance",
        "is_premium": False,
        "interval": 0.4,
        "frames": [
            "🌱",
            "🌿",
            "🥀",
            "🌹",
            "🌹✨",
            "Для самого прекрасного человека! 🌹💐"
        ]
    },
    "пиздец": {
        "title": "Я плачу",
        "category": "emotions",
        "is_premium": False,
        "interval": 0.4,
        "frames": [
            "😐",
            "🥺",
            "🥺💧",
            "😭💦",
            "Я сейчас расплачусь... 😭💔",
            "Это просто пиздец... 🌊😭"
        ]
    },
    "плачу": {
        "title": "Слезы водопадом",
        "category": "emotions",
        "is_premium": False,
        "interval": 0.38,
        "frames": [
            "🥺",
            "😭💧",
            "😭😭💦",
            "😭😭😭🌊",
            "Утешь меня пожалуйста... 🥺🫂"
        ]
    },
    "печатает": {
        "title": "Имитация печати",
        "category": "tools",
        "is_premium": False,
        "interval": 0.45,
        "frames": [
            "✍️ Набирает сообщение.",
            "✍️ Набирает сообщение..",
            "✍️ Набирает сообщение...",
            "💭 Тщательно подбирает слова...",
            "💡 Придумал(а) гениальный ответ!",
            "✨ Ну ладно, слушай..."
        ]
    },
    "загрузка": {
        "title": "Прогресс бар",
        "category": "tools",
        "is_premium": False,
        "interval": 0.35,
        "frames": [
            "Загрузка: [░░░░░░░░░░] 0%",
            "Загрузка: [██░░░░░░░░] 20%",
            "Загрузка: [████░░░░░░] 45%",
            "Загрузка: [██████░░░░] 68%",
            "Загрузка: [████████░░] 89%",
            "Успешно: [██████████] 100% ✅"
        ]
    },
    "матрица": {
        "title": "Код Матрицы",
        "category": "fun",
        "is_premium": True,
        "interval": 0.4,
        "frames": [
            "0 1 0 0 1 0 1 1",
            "1 0 1 1 0 1 0 0",
            "Wake up, Neo...",
            "The Matrix has you...",
            "Follow the white rabbit. 🐇"
        ]
    },
    "ты": {
        "title": "Комплимент 18+",
        "category": "18+",
        "is_premium": True,
        "interval": 0.4,
        "frames": [
            "😏",
            "🍌",
            "🍌💦",
            "🍆✨",
            "Ты просто секс и пожар! 🔥🤤"
        ]
    },
    "писюн": {
        "title": "Юмор 18+",
        "category": "18+",
        "is_premium": True,
        "interval": 0.38,
        "frames": [
            "👀",
            "📏 3 см...",
            "📏 10 см...",
            "📏 18 см! 🚀",
            "Главное не размер, а любовь! ❤️😂"
        ]
    },
    "огонь": {
        "title": "Пожар и взрыв",
        "category": "fun",
        "is_premium": False,
        "interval": 0.35,
        "frames": [
            "🕯️",
            "🔥",
            "🔥🔥",
            "🔥🔥🔥",
            "Это просто пушка и пожар! 🧨🔥💥"
        ]
    },
    "взрыв": {
        "title": "Таймер бомбы",
        "category": "fun",
        "is_premium": False,
        "interval": 0.45,
        "frames": [
            "💣 3...",
            "💣 2...",
            "💣 1...",
            "💥 БАБАХ!",
            "🎉🥳✨ ПРАЗДНИЧНЫЙ САЛЮТ! ✨🎆"
        ]
    },
    "дождь": {
        "title": "Гроза и радуга",
        "category": "wishes",
        "is_premium": False,
        "interval": 0.38,
        "frames": [
            "☁️",
            "☁️⚡",
            "🌧️🌧️",
            "🌧️🌧️🌧️",
            "🌦️",
            "🌈 Пусть после любого дождя сияет яркая радуга! ✨🌤️"
        ]
    },
    "костер": {
        "title": "Уютный костер",
        "category": "emotions",
        "is_premium": False,
        "interval": 0.38,
        "frames": [
            "🪵",
            "🪵 ✨",
            "🪵 🔥",
            "🪵 🔥🔥",
            "🪵 🔥🔥🔥",
            "Тепло и уют для тебя этой ночью! ⛺🔥🌌"
        ]
    },
    "фейерверк": {
        "title": "Праздничный салют",
        "category": "fun",
        "is_premium": False,
        "interval": 0.36,
        "frames": [
            "🚀 ...",
            "🚀 ✨ ...",
            "💥",
            "🎆✨",
            "🎇🎆✨",
            "🎉 Поздравляю от всего сердца! 🥳🎆"
        ]
    },
    "корона": {
        "title": "Коронация короля/королевы",
        "category": "romance",
        "is_premium": False,
        "interval": 0.38,
        "frames": [
            "✨",
            "✨ 👑",
            "👑 Коронация...",
            "👑 Для настоящего Короля / Королевы! 💎✨"
        ]
    },
    "сердечки": {
        "title": "Радужные сердца",
        "category": "romance",
        "is_premium": False,
        "interval": 0.32,
        "frames": [
            "❤️",
            "❤️ 🧡",
            "❤️ 🧡 💛",
            "❤️ 🧡 💛 💚",
            "❤️ 🧡 💛 💚 💙",
            "❤️ 🧡 💛 💚 💙 💜",
            "💖 Вся любовь мира для тебя! ✨🌈"
        ]
    }
}


def generate_typewriter_frames(text: str, step: int = 2) -> List[str]:
    """Generates frames for typewriter effect."""
    if not text:
        text = "Привет! Это эффект живой печати ✨"
    frames = []
    length = len(text)
    for i in range(1, length + 1, step):
        chunk = text[:i]
        frames.append(f"{chunk}|")
    frames.append(text)
    # Ensure not too many frames
    if len(frames) > 16:
        # Downsample
        stride = len(frames) // 14 + 1
        sub_frames = frames[::stride]
        if sub_frames[-1] != text:
            sub_frames.append(text)
        return sub_frames
    return frames


class AnimationEngine:
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot

    async def play_animation(
        self,
        business_connection_id: str,
        chat_id: int,
        message_id: int,
        frames: List[str],
        interval: float = 0.38
    ) -> bool:
        if not self.bot or not frames:
            return False

        last_frame = frames[-1]
        for i, frame in enumerate(frames):
            try:
                await self.bot.edit_message_text(
                    text=frame,
                    business_connection_id=business_connection_id,
                    chat_id=chat_id,
                    message_id=message_id
                )
                if i < len(frames) - 1:
                    await asyncio.sleep(max(interval, 0.32))
            except TelegramRetryAfter as e:
                logger.warning(f"Telegram FloodWait hit: retry after {e.retry_after}s. Skipping to final frame.")
                await asyncio.sleep(e.retry_after)
                try:
                    await self.bot.edit_message_text(
                        text=last_frame,
                        business_connection_id=business_connection_id,
                        chat_id=chat_id,
                        message_id=message_id
                    )
                except Exception:
                    pass
                return True
            except TelegramBadRequest as e:
                # Message not modified or deleted
                logger.debug(f"TelegramBadRequest in animation: {e}")
                if "message is not modified" in str(e).lower():
                    continue
                break
            except Exception as e:
                logger.error(f"Unexpected error in animation: {e}")
                break
        return True


animation_engine = AnimationEngine()
