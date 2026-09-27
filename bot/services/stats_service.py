import math
from typing import Optional
from database.models import ChatStatistic


class StatsService:
    @staticmethod
    def render_progress_bar(val1: int, val2: int, length: int = 10) -> str:
        total = val1 + val2
        if total == 0:
            return "░" * length
        ratio = val1 / total
        filled = int(round(ratio * length))
        filled = max(0, min(length, filled))
        return "🟩" * filled + "🟪" * (length - filled)

    @classmethod
    def format_chat_stats_card(
        cls,
        stat: ChatStatistic,
        user_name: str = "Вы",
        partner_name: str = "Собеседник"
    ) -> str:
        total = stat.outgoing_count + stat.incoming_count
        if total == 0:
            out_pct = 50
            in_pct = 50
        else:
            out_pct = int((stat.outgoing_count / total) * 100)
            in_pct = 100 - out_pct

        bar = cls.render_progress_bar(stat.outgoing_count, stat.incoming_count, length=8)

        # Dynamic rating
        if total > 500:
            status_text = "🔥 Неразлучные друзья (S-Rank)"
        elif total > 100:
            status_text = "💬 Активный диалог (A-Rank)"
        elif total > 20:
            status_text = "🤝 Теплое общение (B-Rank)"
        else:
            status_text = "🌱 Только начинаем (C-Rank)"

        card = (
            f"📊 <b>СТАТИСТИКА ПЕРЕПИСКИ</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Вы:</b> {user_name}\n"
            f"👥 <b>Собеседник:</b> {partner_name}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✉️ <b>Всего сообщений:</b> <code>{total}</code>\n"
            f"   ├ 🟢 Отправлено вами: <b>{stat.outgoing_count}</b> ({out_pct}%)\n"
            f"   └ 🟣 Получено ответов: <b>{stat.incoming_count}</b> ({in_pct}%)\n\n"
            f"Баланс диалога:\n"
            f"[{bar}]\n"
            f"🟢 {user_name} | {partner_name} 🟣\n\n"
            f"🏆 <b>Уровень связи:</b> {status_text}\n"
            f"⏱ <b>Последняя активность:</b> <code>{stat.last_message_at.strftime('%d.%m.%Y %H:%M')} UTC</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>evzhem_business_bot</i>"
        )
        return card

    @classmethod
    def format_global_stats(cls, stats_dict: dict, user_name: str) -> str:
        tot_in = stats_dict.get("total_incoming", 0)
        tot_out = stats_dict.get("total_outgoing", 0)
        tot_dialogues = stats_dict.get("total_dialogues", 0)
        total_all = tot_in + tot_out

        return (
            f"📈 <b>ВАША ОБЩАЯ СТАТИСТИКА В TELEGRAM</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 Пользователь: <b>{user_name}</b>\n"
            f"💬 Активных диалогов: <b>{tot_dialogues}</b>\n"
            f"✉️ Всего обработано сообщений: <b>{total_all}</b>\n"
            f"   ├ 📤 Исходящих: <b>{tot_out}</b>\n"
            f"   └ 📥 Входящих: <b>{tot_in}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🚀 <i>Все сообщения анализируются в режиме реального времени.</i>"
        )


stats_service = StatsService()
