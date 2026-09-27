import io
import logging
from typing import Optional
import qrcode
from PIL import Image
from aiogram import Bot
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)


class QRService:
    @staticmethod
    def generate_qr_bytes(data: str) -> bytes:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=3,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#17212b", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    @staticmethod
    def generate_qr(data: str) -> bytes:
        return QRService.generate_qr_bytes(data)

    @classmethod
    async def send_qr_photo(
        cls,
        bot: Bot,
        chat_id: int,
        business_conn_id: Optional[str] = None,
        business_connection_id: Optional[str] = None,
        data_text: Optional[str] = None,
        data: Optional[str] = None,
        caption: Optional[str] = None
    ) -> bool:
        conn_id = business_conn_id or business_connection_id
        content = data_text or data or "https://t.me/evzhem_business_bot"
        try:
            qr_bytes = cls.generate_qr_bytes(content)
            photo_file = BufferedInputFile(qr_bytes, filename="qr.png")
            cap = caption or f"📱 <b>QR-код сгенерирован:</b>\n<code>{content}</code>"

            if conn_id:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=cap,
                    business_connection_id=conn_id
                )
            else:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=cap
                )
            return True
        except Exception as e:
            logger.error(f"Failed to send QR code: {e}")
            return False

    @classmethod
    async def send_qr_code(cls, *args, **kwargs):
        return await cls.send_qr_photo(*args, **kwargs)


qr_service = QRService()
