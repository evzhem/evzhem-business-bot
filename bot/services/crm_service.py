import random
from datetime import datetime
from typing import List, Optional
from database.models import ChatStatistic, UserNote


class CRMService:
    @staticmethod
    def generate_receipt(amount: str, item_name: str, sender_name: str = "Исполнитель", client_name: str = "Клиент") -> str:
        order_num = random.randint(1000, 9999)
        date_str = datetime.utcnow().strftime("%d.%m.%Y %H:%M")
        
        # Clean amount
        clean_amount = amount.replace("k", "000").replace("к", "000")
        if not any(char.isdigit() for char in clean_amount):
            clean_amount = "1,000"

        receipt = (
            f"🧾 <b>ЭЛЕКТРОННЫЙ ЧЕК / СЧЕТ №{order_num}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Исполнитель:</b> {sender_name}\n"
            f"👤 <b>Клиент:</b> {client_name}\n"
            f"📋 <b>Назначение:</b> {item_name or 'Оказание услуг'}\n"
            f"💰 <b>Сумма платежа:</b> <code>{clean_amount} RUB</code>\n"
            f"📅 <b>Дата операции:</b> {date_str} UTC\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<code>[ █║▌│█│║▌║││█║▌║▌║ ]</code>\n"
            f"       <code>№ TR-{order_num}-2026-OK</code>\n"
            f"✅ <b>Статус:</b> Оплачено и подтверждено\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>evzhem_business_bot CRM</i>"
        )
        return receipt

    @staticmethod
    def format_crm_dossier(
        target_name: str,
        target_id: int,
        tags: List[str] = None,
        notes: List[UserNote] = None,
        stats: Optional[ChatStatistic] = None,
        is_muted: bool = False,
        is_whitelisted: bool = False
    ) -> str:
        tags_list = tags or []
        notes_list = notes or []
        tags_str = " ".join([f"<code>#{t}</code>" for t in tags_list]) if tags_list else "<i>тегов нет</i>"
        
        if notes_list:
            notes_str = "\n".join([f"  • {n.note_text} (<i>{n.category}</i>)" for n in notes_list])
        else:
            notes_str = "  <i>заметок пока нет</i>"

        out_count = stats.outgoing_count if stats else 0
        in_count = stats.incoming_count if stats else 0
        total = out_count + in_count

        mute_status = "🔇 В муте (сообщения удаляются)" if is_muted else "🔊 Активен"
        if is_whitelisted:
            mute_status += " | 🛡️ В белом списке"

        dossier = (
            f"👤 <b>CRM ДОСЬЕ КОНТАКТА</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 <b>Имя:</b> {target_name}\n"
            f"🆔 <b>Telegram ID:</b> <code>{target_id}</code>\n"
            f"📌 <b>Теги:</b> {tags_str}\n"
            f"🔒 <b>Статус:</b> {mute_status}\n\n"
            f"📊 <b>Статистика общения:</b>\n"
            f"  • Всего сообщений: <b>{total}</b>\n"
            f"  • Отправлено вами: <b>{out_count}</b>\n"
            f"  • Получено от него: <b>{in_count}</b>\n\n"
            f"📝 <b>Заметки и важные детали:</b>\n"
            f"{notes_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Добавить тег: <code>.тег Название</code> | Заметка: <code>.заметка Текст</code></i>"
        )
        return dossier

    @classmethod
    def format_dossier(cls, target_name: str, target_id: int, tags=None, notes=None, stat=None, stats=None, is_muted=False, is_whitelisted=False):
        return cls.format_crm_dossier(
            target_name=target_name,
            target_id=target_id,
            tags=tags,
            notes=notes,
            stats=stat or stats,
            is_muted=is_muted,
            is_whitelisted=is_whitelisted
        )


crm_service = CRMService()
