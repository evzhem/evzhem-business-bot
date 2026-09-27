import io
import logging
import edge_tts
from typing import Optional
from aiogram import Bot
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)

# Real neural voices from Edge-TTS
AVAILABLE_VOICES = {
    "dmitry": "ru-RU-DmitryNeural",      # Мужской глубокий голос
    "svetlana": "ru-RU-SvetlanaNeural",  # Женский естественный голос
    "guy": "en-US-GuyNeural",            # Английский мужской
    "jenny": "en-US-JennyNeural"         # Английский женский
}


class VoiceService:
    DEFAULT_VOICE = "ru-RU-DmitryNeural"

    @staticmethod
    async def synthesize_voice_bytes(
        text: str,
        voice_name: str = "ru-RU-DmitryNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> Optional[bytes]:
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice_name, rate=rate, pitch=pitch)
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            return bytes(audio_data)
        except Exception as e:
            logger.error(f"Voice synthesis error: {e}")
            return None

    @classmethod
    async def text_to_speech(
        cls,
        text: str,
        voice_name: str = "ru-RU-DmitryNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> Optional[bytes]:
        return await cls.synthesize_voice_bytes(text, voice_name, rate, pitch)

    @classmethod
    async def send_voice_message(
        cls,
        bot: Bot,
        chat_id: int,
        business_conn_id: Optional[str] = None,
        business_connection_id: Optional[str] = None,
        text: str = "Привет!",
        voice_key: str = "dmitry"
    ) -> bool:
        conn_id = business_conn_id or business_connection_id
        voice_name = AVAILABLE_VOICES.get(voice_key.lower(), AVAILABLE_VOICES["dmitry"])
        audio_bytes = await cls.synthesize_voice_bytes(text=text, voice_name=voice_name)

        if not audio_bytes:
            return False

        try:
            voice_file = BufferedInputFile(audio_bytes, filename="voice.ogg")
            if conn_id:
                await bot.send_voice(
                    chat_id=chat_id,
                    voice=voice_file,
                    business_connection_id=conn_id
                )
            else:
                await bot.send_voice(
                    chat_id=chat_id,
                    voice=voice_file
                )
            return True
        except Exception as e:
            logger.error(f"Failed to send voice message: {e}")
            return False


voice_service = VoiceService()
