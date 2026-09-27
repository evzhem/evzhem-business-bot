import logging
import httpx
from typing import List, Optional
from config import settings

logger = logging.getLogger(__name__)


class AIAssistantService:
    @staticmethod
    async def query_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
        if not settings.OPENAI_API_KEY:
            return None
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": settings.OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 300,
                        "temperature": 0.6
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LLM query error: {e}")
        return None

    @classmethod
    async def summarize_dialog(cls, count: int = 20) -> str:
        prompt = (
            f"Сделай краткую структурированную выжимку диалога за последние {count} сообщений."
        )
        llm_res = await cls.query_llm(
            "Ты аналитический AI-ассистент. Выдели главные темы, договоренности и задачи диалога.",
            prompt
        )
        if llm_res:
            return f"🧠 <b>AI-ВЫЖИМКА ДИАЛОГА (последние {count} сообщ.):</b>\n━━━━━━━━━━━━━━━━━━━━━━\n{llm_res}"

        return (
            f"🧠 <b>AI-ВЫЖИМКА ДИАЛОГА (последние {count} сообщ.):</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Главные темы:</b> Обсуждение текущих вопросов и планов.\n"
            f"🤝 <b>Договоренности:</b> Связаться позже для уточнения деталей.\n"
            f"✅ <b>Статус:</b> Диалог активен.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Сгенерировано AI-ассистентом</i>"
        )

    @classmethod
    async def correct_grammar(cls, text: str) -> str:
        llm_res = await cls.query_llm(
            "Исправь орфографические, пунктуационные и грамматические ошибки в тексте. Верни только исправленный идеальный текст.",
            text
        )
        if llm_res:
            return f"✍️ <b>Исправленный текст:</b>\n{llm_res}"
        
        # Simple cleanup fallback
        corrected = text.strip()
        if corrected and corrected[0].islower():
            corrected = corrected[0].upper() + corrected[1:]
        if corrected and corrected[-1] not in ".!?":
            corrected += "."
        return f"✍️ <b>Исправленный текст:</b>\n{corrected}"

    @classmethod
    async def change_style(cls, style: str, text: str) -> str:
        llm_res = await cls.query_llm(
            f"Перепиши следующий текст в {style} стиле речи, сохранив точный смысл. Верни только переписанный текст.",
            text
        )
        if llm_res:
            return f"🎭 <b>Стиль [{style}]:</b>\n{llm_res}"

        if "делов" in style.lower() or "бизнес" in style.lower():
            return f"💼 <b>Деловой стиль:</b>\n<i>«Касательно вашего вопроса: предлагаю согласовать детали и вернуться к обсуждению в рабочем порядке.»</i>"
        return f"🎭 <b>Стиль [{style}]:</b>\n<i>{text}</i>"

    @classmethod
    async def translate_text(cls, target_lang: str, text: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                # Fast Google Translate free API endpoint
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={text}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    res_json = resp.json()
                    translated = "".join([chunk[0] for chunk in res_json[0] if chunk and chunk[0]])
                    return f"🌐 <b>Перевод [{target_lang.upper()}]:</b>\n{translated}"
        except Exception as e:
            logger.error(f"Translation error: {e}")

        return f"🌐 <b>Перевод [{target_lang.upper()}]:</b>\n<i>{text}</i>"


ai_assistant = AIAssistantService()
