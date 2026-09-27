import pytest
import asyncio
from database.db import init_db, AsyncSessionLocal
from database.repository import Repository
from bot.services.voice_service import voice_service
from bot.services.qr_service import qr_service
from bot.services.crm_service import crm_service
from bot.services.animation_engine import BUILTIN_ANIMATIONS


@pytest.mark.asyncio
async def test_full_system_and_services():
    await init_db()
    async with AsyncSessionLocal() as session:
        repo = Repository(session)

        # 1. User creation
        user = await repo.get_or_create_user(
            telegram_id=999111222,
            username="evzhem_test",
            first_name="Евгений"
        )
        assert user.telegram_id == 999111222
        assert user.first_name == "Евгений"

        # 2. Business Connection
        conn = await repo.save_or_update_business_conn(
            connection_id="test_conn_001",
            user_id=user.telegram_id,
            user_chat_id=user.telegram_id,
            can_reply=True,
            is_enabled=True
        )
        assert conn.connection_id == "test_conn_001"
        assert conn.can_reply is True

        # 3. Tags & CRM
        test_contact_id = 123456789
        is_added = await repo.add_or_toggle_tag(user.telegram_id, test_contact_id, "VIP")
        if not is_added:
            await repo.add_or_toggle_tag(user.telegram_id, test_contact_id, "VIP")
        tags = await repo.get_tags_for_contact(user.telegram_id, test_contact_id)
        assert "VIP" in tags

        # 4. Notes
        note = await repo.add_or_update_note(user.telegram_id, test_contact_id, "Важный контакт", "Партнер")
        assert note.note_text == "Важный контакт"

        # 5. Mute & Whitelist
        mute = await repo.mute_chat(user.telegram_id, 888777666, "Spammer", 30)
        assert await repo.is_muted(user.telegram_id, 888777666) is True
        assert await repo.is_muted(user.telegram_id, 111111111) is False

        await repo.unmute_chat(user.telegram_id, 888777666)
        assert await repo.is_muted(user.telegram_id, 888777666) is False


def test_qr_generation():
    qr_bytes = qr_service.generate_qr("https://t.me/evzhem_business_bot")
    assert len(qr_bytes) > 100


def test_crm_receipt_generation():
    receipt = crm_service.generate_receipt("15000", "Разработка бота", "Евгений", "Клиент")
    assert "15000" in receipt
    assert "№ TR-" in receipt
    assert "Евгений" in receipt


def test_animation_engine_frames():
    assert "люблю" in BUILTIN_ANIMATIONS
    assert "корона" in BUILTIN_ANIMATIONS
    assert "дождь" in BUILTIN_ANIMATIONS
    assert len(BUILTIN_ANIMATIONS["люблю"]) >= 3


@pytest.mark.asyncio
async def test_voice_tts():
    audio = await voice_service.text_to_speech("Тест голоса", "ru-RU-DmitryNeural")
    assert len(audio) > 0
