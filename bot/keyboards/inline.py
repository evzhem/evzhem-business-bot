from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import settings


def get_main_menu_keyboard(autoresponder_active: bool = False, webapp_url: str = "") -> InlineKeyboardMarkup:
    ar_status = "🟢 Автоответчик: ВКЛ" if autoresponder_active else "🔴 Автоответчик: ВЫКЛ"
    url = webapp_url or settings.WEBAPP_BASE_URL

    keyboard = []

    # WebApp button if HTTPS available
    if url and url.startswith("https://"):
        keyboard.append([
            InlineKeyboardButton(
                text="📱 Открыть WebApp Панель Управления ✨",
                web_app=WebAppInfo(url=url)
            )
        ])

    keyboard.extend([
        [
            InlineKeyboardButton(text="📚 Все 35+ команд и функций", callback_data="btn_catalog"),
        ],
        [
            InlineKeyboardButton(text="💼 Личный CRM & Досье", callback_data="btn_crm"),
            InlineKeyboardButton(text="🎙️ Голосовой модуль", callback_data="btn_voice_info")
        ],
        [
            InlineKeyboardButton(text="💫 Живые Анимации", callback_data="btn_smiles"),
            InlineKeyboardButton(text="🔇 Мут и Приватность", callback_data="btn_moderation_info")
        ],
        [
            InlineKeyboardButton(text="📊 Аналитика чатов", callback_data="btn_analytics"),
            InlineKeyboardButton(text="🏆 Достижения", callback_data="btn_achievements")
        ],
        [
            InlineKeyboardButton(text=ar_status, callback_data="toggle_autoresponder"),
            InlineKeyboardButton(text="👤 Мой статус", callback_data="btn_status")
        ],
        [
            InlineKeyboardButton(text="🎬 Инструкция по подключению", callback_data="btn_tutorial"),
            InlineKeyboardButton(text="⭐ VIP Премиум", callback_data="btn_premium")
        ]
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_keyboard(back_to: str = "main_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data=back_to)]
        ]
    )


def get_catalog_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎙️ Голос & QR", callback_data="cat_voice"),
                InlineKeyboardButton(text="💼 CRM & Чек", callback_data="cat_crm")
            ],
            [
                InlineKeyboardButton(text="🧠 AI & Текст", callback_data="cat_ai"),
                InlineKeyboardButton(text="💫 Анимации", callback_data="cat_anim")
            ],
            [
                InlineKeyboardButton(text="🔇 Модерация", callback_data="cat_mod"),
                InlineKeyboardButton(text="💎 Финансы", callback_data="cat_utils")
            ],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="main_menu")]
        ]
    )


def get_premium_buy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⭐ 1 Месяц — {settings.PREMIUM_PRICE_1M} Stars", callback_data="buy_prem_1m")],
            [InlineKeyboardButton(text=f"⭐ 3 Месяца — {settings.PREMIUM_PRICE_3M} Stars (-15%)", callback_data="buy_prem_3m")],
            [InlineKeyboardButton(text=f"👑 VIP Lifetime — {settings.PREMIUM_PRICE_LIFETIME} Stars", callback_data="buy_prem_life")],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="main_menu")]
        ]
    )
