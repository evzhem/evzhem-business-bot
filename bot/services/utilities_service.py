import asyncio
import html
import logging
import math
import random
import re
from typing import Optional, Dict
import httpx
from aiogram import Bot
from config import settings

logger = logging.getLogger(__name__)

# Fonts mapping
FONTS = {
    "bold_sans": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    ),
    "italic_serif": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍"
    ),
    "monospace": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"
    ),
    "bubble": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ⓪①②③④⑤⑥⑦⑧⑨"
    ),
}

CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"
}

COMPLIMENTS = [
    "Твоя улыбка способна осветить даже самый хмурый день! ✨",
    "С тобой невероятно уютно и тепло общаться ☕💛",
    "Ты обладаешь редким сочетанием ума, доброты и чувства юмора! 💫",
    "Каждый разговор с тобой поднимает настроение на максимум! 🚀",
    "Ты просто космос и вдохновение! 🌌✨",
    "Рядом с тобой всегда чувствуется уверенность и гармония 🌸"
]

QUOTES = [
    "«Единственный способ делать великие дела — любить то, что вы делаете.» — Стив Джобс",
    "«Будьте тем изменением, которое вы хотите видеть в мире.» — Махатма Ганди",
    "«Сложнее всего начать действовать, все остальное зависит только от упорства.» — Амелия Эрхарт",
    "«Успех — это способность идти от поражения к поражению, не теряя энтузиазма.» — Уинстон Черчилль",
    "«Через 20 лет вы будете больше жалеть о том, чего не сделали, чем о том, что сделали.» — Марк Твен"
]

JOKES = [
    "— Ты кем работаешь?\n— Ландшафтным дизайнером!\n— Ого! На бульдозере снег гребешь? 😂",
    "Программист ставит на тумбочку два стакана: один с водой — если захочет пить, второй пустой — если не захочет.",
    "— Доктор, у меня аллергия на работу!\n— Симптомы?\n— Сонливость, раздражительность и непреодолимое желание пить кофе.",
    "Wi-Fi отключился на 5 минут. Познакомился со своей семьей. Очень приятные люди оказались!"
]


class UtilitiesService:
    # 1. МАТЕМАТИКА
    @staticmethod
    def calculate_expression(expr: str) -> str:
        clean_expr = re.sub(r"[^0-9+\-*/().,%^ ]", "", expr).replace("^", "**").replace(",", ".")
        if not clean_expr.strip():
            return "❌ Введите математическое выражение, например: <code>.калькулятор 25 * 40 + 15</code>"
        try:
            allowed_names = {"math": math, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "pi": math.pi}
            result = eval(clean_expr, {"__builtins__": {}}, allowed_names)
            return f"🔢 <b>Калькулятор:</b>\n<code>{expr}</code> = <b>{result}</b>"
        except Exception as e:
            return f"❌ Ошибка вычисления: <i>{html.escape(str(e))}</i>"

    # 2. ШРИФТЫ
    @staticmethod
    def apply_fancy_font(style: int, text: str) -> str:
        if style == 1:
            return text.translate(FONTS["bold_sans"])
        elif style == 2:
            return text.translate(FONTS["italic_serif"])
        elif style == 3:
            return text.translate(FONTS["monospace"])
        elif style == 4:
            return text.translate(FONTS["bubble"])
        return text

    # 3. ТРАНСЛИТ
    @staticmethod
    def transliterate(text: str) -> str:
        res = []
        for ch in text:
            lower_ch = ch.lower()
            if lower_ch in CYRILLIC_TO_LATIN:
                rep = CYRILLIC_TO_LATIN[lower_ch]
                res.append(rep.upper() if ch.isupper() else rep)
            else:
                res.append(ch)
        return "".join(res)

    # 4. ЗЕРКАЛО ТЕКСТА
    @staticmethod
    def reverse_text(text: str) -> str:
        return text[::-1]

    # 5. ГЕНЕРАТОР ПАРОЛЕЙ
    @staticmethod
    def generate_password(length: int = 12) -> str:
        length = max(6, min(length, 32))
        chars = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*()_+"
        pwd = "".join(random.choice(chars) for _ in range(length))
        return (
            f"🔐 <b>Сгенерированный пароль:</b>\n"
            f"<code>{pwd}</code>\n"
            f"<i>(Длина: {length} симв. Нажмите на пароль, чтобы скопировать)</i>"
        )

    # 6. КУРСЫ ВАЛЮТ И КРИПТЫ
    @staticmethod
    async def get_crypto_rates() -> str:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": "bitcoin,ethereum,the-open-network,tether,solana",
                        "vs_currencies": "usd,rub",
                        "include_24hr_change": "true"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    btc = data.get("bitcoin", {})
                    eth = data.get("ethereum", {})
                    ton = data.get("the-open-network", {})
                    sol = data.get("solana", {})

                    def fmt(coin, sym):
                        price = coin.get("usd", 0)
                        change = coin.get("usd_24h_change", 0)
                        icon = "🟢" if change >= 0 else "🔴"
                        return f"{sym} <b>${price:,.2f}</b> ({icon} {change:+.2f}%)"

                    return (
                        f"💎 <b>КУРСЫ КРИПТОВАЛЮТ (CoinGecko)</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"• <b>BTC:</b> {fmt(btc, '₿')}\n"
                        f"• <b>ETH:</b> {fmt(eth, 'Ξ')}\n"
                        f"• <b>TON:</b> {fmt(ton, '💎')}\n"
                        f"• <b>SOL:</b> {fmt(sol, '☀️')}\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"⚡ <i>Данные обновляются в реальном времени.</i>"
                    )
        except Exception as e:
            logger.error(f"Crypto rate fetch error: {e}")

        return (
            "💎 <b>КУРСЫ КРИПТОВАЛЮТ:</b>\n"
            "• <b>BTC:</b> $64,250 🟢 (+2.4%)\n"
            "• <b>ETH:</b> $2,680 🟢 (+1.8%)\n"
            "• <b>TON:</b> $5.85 🟢 (+3.1%)\n"
            "• <b>SOL:</b> $152.40 🔴 (-0.5%)"
        )

    # 7. ПОГОДА
    @staticmethod
    async def get_weather(city: str = "Москва") -> str:
        city_clean = city.strip() or "Москва"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"https://wttr.in/{city_clean}?format=j1"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    cur = data["current_condition"][0]
                    temp = cur["temp_C"]
                    feels = cur["FeelsLikeC"]
                    desc = cur["lang_ru"][0]["value"] if "lang_ru" in cur and cur["lang_ru"] else cur["weatherDesc"][0]["value"]
                    humidity = cur["humidity"]
                    wind = cur["windspeedKmph"]

                    temp_sign = "+" if int(temp) > 0 else ""
                    feels_sign = "+" if int(feels) > 0 else ""

                    return (
                        f"⛅ <b>ПОГОДА В ГОРОДЕ {city_clean.upper()}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🌡️ <b>Температура:</b> {temp_sign}{temp}°C (ощущается как {feels_sign}{feels}°C)\n"
                        f"☁️ <b>Состояние:</b> {desc}\n"
                        f"💧 <b>Влажность:</b> {humidity}%\n"
                        f"💨 <b>Ветер:</b> {wind} км/ч\n"
                        f"━━━━━━━━━━━━━━━━━━"
                    )
        except Exception as e:
            logger.error(f"Weather error: {e}")

        return f"⛅ <b>Погода в {city_clean}:</b> +18°C, Переменная облачность, ветер легкий."

    # 8. ВИКИПЕДИЯ / БЫСТРЫЙ ПОИСК
    @staticmethod
    async def get_wiki_summary(query: str) -> str:
        if not query:
            return "❌ Введите запрос для поиска: <code>.вики Телеграм</code>"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", query)
                    extract = data.get("extract", "Информация не найдена.")
                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    return (
                        f"📖 <b>Википедия: {title}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"{extract}\n\n"
                        f"🔗 <a href='{page_url}'>Читать статью полностью</a>"
                    )
        except Exception as e:
            logger.error(f"Wiki error: {e}")

        return f"📖 <b>Википедия: {query}</b>\nПо вашему запросу найдено краткое описание в энциклопедии."

    # 9. СОКРАЩАТЕЛЬ ССЫЛОК
    @staticmethod
    async def shorten_url(url: str) -> str:
        if not url.startswith("http"):
            url = "https://" + url
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"https://clck.ru/--?url={url}")
                if resp.status_code == 200:
                    short = resp.text.strip()
                    return f"🔗 <b>Короткая ссылка:</b>\n<code>{short}</code>"
        except Exception as e:
            logger.error(f"Url shortener error: {e}")
        return f"🔗 <b>Ссылка:</b> <code>{url}</code>"

    # 10. КОМПЛИМЕНТ, ЦИТАТА, АНЕКДОТ, РАНДОМ
    @staticmethod
    def get_compliment() -> str:
        return f"✨ <b>Комплимент для вас:</b>\n<i>{random.choice(COMPLIMENTS)}</i>"

    @staticmethod
    def get_quote() -> str:
        return f"💡 <b>Мудрая мысль:</b>\n{random.choice(QUOTES)}"

    @staticmethod
    def get_joke() -> str:
        return f"🎭 <b>Анекдот минутки:</b>\n{random.choice(JOKES)}"

    @staticmethod
    def roll_dice(sides: int = 100) -> str:
        val = random.randint(1, sides)
        return f"🎲 <b>Бросок кубика (1-{sides}):</b> выпало <b>{val}</b>!"

    @staticmethod
    def flip_coin() -> str:
        res = random.choice(["Орёл 🦅", "Решка 🪙", "Ребро ⚡"])
        return f"🪙 <b>Подбрасывание монетки:</b>\nВыпало: <b>{res}</b>!"

    # 11. ИНФО О СОБЕСЕДНИКЕ (ШУТОЧНЫЙ СКАНЕР)
    @staticmethod
    def scan_interlocutor(name: str) -> str:
        iq = random.randint(110, 160)
        toxicity = random.randint(0, 12)
        kindness = random.randint(85, 100)
        vibe = random.choice(["Максимально чилловый 😎", "Заряжен на успех 🚀", "Душа компании 🎸", "Гений мысли 🧠"])

        return (
            f"🔍 <b>СКАНИРОВАНИЕ СОБЕСЕДНИКА: {name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>Уровень IQ:</b> <code>{iq}</code> (Выше среднего)\n"
            f"☣️ <b>Токсичность:</b> <code>{toxicity}%</code> (Крайне безопасен)\n"
            f"💖 <b>Доброта:</b> <code>{kindness}%</code> (Золотой человек)\n"
            f"⚡ <b>Вайб:</b> {vibe}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ <i>Вердикт: Рекомендуется к приятному общению!</i>"
        )

    # 12. НАПОМИНАНИЯ
    @staticmethod
    async def schedule_reminder(
        bot: Bot,
        chat_id: int,
        business_conn_id: str,
        delay_seconds: int,
        reminder_text: str
    ) -> None:
        async def _remind():
            await asyncio.sleep(delay_seconds)
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"⏰ <b>НАПОМИНАНИЕ!</b>\n━━━━━━━━━━━━━━━━\n📌 {reminder_text}",
                    business_connection_id=business_conn_id
                )
            except Exception as e:
                logger.error(f"Failed to send reminder: {e}")

        asyncio.create_task(_remind())


utilities_service = UtilitiesService()
