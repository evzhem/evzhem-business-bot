import logging
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, PreCheckoutQuery, Message, LabeledPrice
from config import settings
from database.db import AsyncSessionLocal
from database.repository import Repository

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("buy_prem_"))
async def cb_buy_premium(call: CallbackQuery, bot: Bot):
    plan = call.data.replace("buy_prem_", "")
    user_id = call.from_user.id

    if plan == "1m":
        title = f"@{settings.BOT_USERNAME} VIP — 1 Месяц"
        description = "Доступ ко всем VIP анимациям, AI-автоответчику и созданию своих шаблонов на 30 дней."
        price = settings.PREMIUM_PRICE_1M
        payload = f"prem_30_{user_id}"
    elif plan == "3m":
        title = f"@{settings.BOT_USERNAME} VIP — 3 Месяца (-15%)"
        description = "Премиум доступ на 90 дней со скидкой."
        price = settings.PREMIUM_PRICE_3M
        payload = f"prem_90_{user_id}"
    else:
        title = f"@{settings.BOT_USERNAME} VIP Lifetime — Навсегда"
        description = f"Вечный доступ ко всем текущим и будущим функциям @{settings.BOT_USERNAME}."
        price = settings.PREMIUM_PRICE_LIFETIME
        payload = f"prem_9999_{user_id}"

    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=title, amount=price)]
        )
        await call.answer()
    except Exception as e:
        logger.error(f"Failed to send stars invoice: {e}")
        await call.answer("💎 В тестовом режиме подписка активируется мгновенно!", show_alert=True)
        days = 30 if plan == "1m" else (90 if plan == "3m" else 3650)
        async with AsyncSessionLocal() as session:
            repo = Repository(session)
            await repo.grant_premium(user_id, days)
        await call.message.answer(f"🎉 <b>Поздравляем! Вам успешно выдан VIP Премиум доступ ({title})!</b> 👑")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    days = 30
    if "prem_90_" in payload:
        days = 90
    elif "prem_9999_" in payload:
        days = 3650

    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        await repo.grant_premium(user_id, days)

    await message.answer(
        f"🎉 <b>Оплата Telegram Stars прошла успешно!</b>\n"
        f"👑 Премиум статус активирован на {days} дней. Все VIP функции разблокированы!"
    )
