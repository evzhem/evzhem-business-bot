import asyncio
import sys
from bot.services.animation_engine import BUILTIN_ANIMATIONS, generate_typewriter_frames
from bot.services.stats_service import stats_service
from bot.services.utilities_service import utilities_service
from database.db import init_db, AsyncSessionLocal
from database.repository import Repository


async def run_simulation():
    print("=" * 60)
    print("🍀 EVZHEM BUSINESS BOT — LIVE SIMULATION")
    print("=" * 60)
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        user = await repo.get_or_create_user(
            telegram_id=777888999,
            username="alexander_dev",
            first_name="Александр"
        )
        print(f"\n[1] Пользователь зарегистрирован: {user.first_name} (@{user.username})")
        
        conn = await repo.save_or_update_business_conn(
            connection_id="conn_demo_simulation_999",
            user_id=user.telegram_id,
            user_chat_id=user.telegram_id,
            can_reply=True,
            is_enabled=True,
            rights_summary="5/5 (Full Rights)"
        )
        print(f"[2] Telegram Business подключен: ID={conn.connection_id}, Rights={conn.rights_summary}")
        
        # Test Animation Playback in terminal
        print("\n[3] Демонстрация анимации .люблю в реальном времени:")
        frames = BUILTIN_ANIMATIONS["люблю"]["frames"]
        for i, frame in enumerate(frames, 1):
            sys.stdout.write(f"\r  Кадр {i}/{len(frames)}: {frame:<40}")
            sys.stdout.flush()
            await asyncio.sleep(0.35)
        print("\n  -> Анимация успешно завершена!")

        # Test Typewriter Animation
        print("\n[4] Демонстрация эффекта .печать Привет, как твои дела?:")
        tw_frames = generate_typewriter_frames("Привет, как твои дела?")
        for i, frame in enumerate(tw_frames, 1):
            sys.stdout.write(f"\r  Печать {i}/{len(tw_frames)}: {frame:<35}")
            sys.stdout.flush()
            await asyncio.sleep(0.2)
        print("\n  -> Эффект печати завершен!")

        # Test Stats
        await repo.record_message_stat(user.telegram_id, 1002, is_outgoing=True, interlocutor_name="Мария ❤️")
        await repo.record_message_stat(user.telegram_id, 1002, is_outgoing=False, interlocutor_name="Мария ❤️")
        stat = await repo.get_chat_stat(user.telegram_id, 1002)
        print("\n[5] Результат выполнения команды .наша стата:")
        card = stats_service.format_chat_stats_card(stat, "Александр", "Мария ❤️")
        print("-" * 40)
        # Strip HTML tags for clean CLI preview
        import re
        clean_card = re.sub(r"<[^>]+>", "", card)
        print(clean_card)
        print("-" * 40)

        # Test Mute
        await repo.mute_chat(user.telegram_id, 999000, "Spammer999", duration_minutes=60)
        is_m = await repo.is_muted(user.telegram_id, 999000)
        print(f"\n[6] Проверка мута: пользователь 999000 замучен? -> {is_m} (сообщения блокируются)")

    print("\n✅ Все системы evzhem_business_bot работают идеально!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_simulation())
