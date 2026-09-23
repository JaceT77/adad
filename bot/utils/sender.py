import logging
import re

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

# Telegram ruxsat bergan rasmiy HTML teglari
ALLOWED_TAG_PATTERN = re.compile(
    r"</?(?:b|strong|i|em|u|ins|s|strike|del|span|tg-spoiler|code|pre|blockquote)(?:\s*|/)>"
    r"|<a\s+href=[\"'][^\"']+[\"'](?:\s*)>|</a>",
    re.IGNORECASE,
)


def clean_text_for_telegram(text: str) -> str:
    """LaTeX va muammoli matematik belgilarni tozalash."""
    if not text:
        return ""
    # $$ ... $$ ko'rinishidagi blokli formulalar
    cleaned = re.sub(r"\$\$(.*?)\$\$", r"\1", text, flags=re.DOTALL)
    # $ ... $ ko'rinishidagi inline formulalar
    cleaned = re.sub(r"\$(.*?)\$", r"\1", cleaned)
    # \( ... \) va \[ ... \] formulalar
    cleaned = re.sub(r"\\\((.*?)\\\)", r"\1", cleaned)
    cleaned = re.sub(r"\\\[(.*?)\\\]", r"\1", cleaned, flags=re.DOTALL)
    # \text{...} va \textbf{...} kabi buyruqlar
    cleaned = re.sub(r"\\text(?:bf|it)?\{([^}]+)\}", r"\1", cleaned)
    cleaned = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1 / \2)", cleaned)
    # Matematik va fizik belgilar
    replacements = {
        "\\le": "≤",
        "\\ge": "≥",
        "\\approx": "≈",
        "\\cdot": "·",
        "\\times": "×",
        "\\pm": "±",
        "\\neq": "≠",
        "\\degree": "°",
        "^\\circ": "°",
        "\\mu": "µ",
        "\\Omega": "Om",
        "\\alpha": "alfa",
        "\\beta": "beta",
        "\\lambda": "lambda",
        "\\Delta": "Δ",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    # Qolgan yolg'iz $ belgilarini tozalash
    cleaned = cleaned.replace("$", "")
    return cleaned


def sanitize_telegram_html(text: str) -> str:
    """Ruxsat berilgan HTML teglarini saqlab, qolgan &, <, > belgilarini xavfsiz qilish."""
    tags = []

    def save_tag(m: re.Match) -> str:
        tags.append(m.group(0))
        return f"\x00TAG_{len(tags) - 1}\x00"

    # 1. Ruxsat berilgan teglarni vaqtincha ajratib olish
    tokenized = ALLOWED_TAG_PATTERN.sub(save_tag, text)

    # 2. Qolgan & < > larni escape qilish
    escaped = tokenized.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 3. Ruxsat berilgan teglarni qaytarish
    for i, tag in enumerate(tags):
        escaped = escaped.replace(f"\x00TAG_{i}\x00", tag)

    return escaped


def prepare_telegram_html(text: str) -> str:
    """Markdown sintaksisini chiroyli Telegram HTML ga o'tkazish va tozalash."""
    if not text:
        return ""

    text = clean_text_for_telegram(text)

    # Markdown sarlavhalarni <b> ga o'tkazish: ### Sarlavha -> <b>Sarlavha</b>
    text = re.sub(r"^#{1,6}\s*(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Pre/code bloklari: ```...``` -> <pre><code>...</code></pre>
    text = re.sub(r"```(?:\w+)?\n?(.*?)```", r"<pre><code>\1</code></pre>", text, flags=re.DOTALL)

    # Inline code: `...` -> <code>...</code>
    text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)

    # Bold: **matn** -> <b>matn</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Italic: *matn* yoki _matn_ -> <i>matn</i>
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<i>\1</i>", text)

    return sanitize_telegram_html(text)


def split_text_into_chunks(text: str, max_chunk_size: int = 3800) -> list[str]:
    """Matnni Telegram sig'adigan (3800 belgigacha) bo'laklarga xavfsiz ajratish."""
    if not text:
        return []
    if len(text) <= max_chunk_size:
        return [text]

    # 1. Avval paragraflar bo'yicha (\n\n) bo'lamiz
    paragraphs = text.split("\n\n")
    sub_blocks = []
    for p in paragraphs:
        if len(p) <= max_chunk_size:
            sub_blocks.append(p)
        else:
            # 2. Paragraf 3800 dan katta bo'lsa, qatorlar (\n) bo'yicha bo'lamiz
            lines = p.split("\n")
            for line in lines:
                if len(line) <= max_chunk_size:
                    sub_blocks.append(line)
                else:
                    # 3. Qator ham 3800 dan katta bo'lsa, qat'iy belgilab kesamiz
                    for i in range(0, len(line), max_chunk_size):
                        sub_blocks.append(line[i : i + max_chunk_size])

    chunks = []
    current_chunk = ""
    for block in sub_blocks:
        stripped_block = block.strip()
        if not stripped_block:
            continue

        if current_chunk and (len(current_chunk) + len(block) + 2 > max_chunk_size):
            chunks.append(current_chunk.strip())
            current_chunk = block + "\n\n"
        else:
            if current_chunk:
                current_chunk += block + "\n\n"
            else:
                current_chunk = block + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


async def safe_send_message(bot: Bot, chat_id: int, text: str) -> None:
    """
    Xabarni xavfsiz va chiroyli Telegram HTML formatida yuborish:
    1. LaTeX va formulalarni tozalaydi.
    2. Markdown formatlarini Telegram HTML teglari (<b>, <i>, <code>, <blockquote>) ga o'tkazadi.
    3. Maxsus belgilarni (&, <, >) to'g'ri sanitizatsiya qiladi.
    4. 3800 belgilik qismlarga bo'ladi (Telegram chegarasi 4096).
    5. HTML orqali yuboradi. Agar Telegram entity parse xatosi bersa,
       teglar tozalanib, darhol oddiy matn (parse_mode=None) ko'rinishida yetkaziladi.
    """
    html_text = prepare_telegram_html(text)
    chunks = split_text_into_chunks(html_text)

    for chunk in chunks:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.HTML,
            )
        except TelegramBadRequest as e:
            logger.warning(f"Telegram HTML parse error: {e}. Retrying as sanitized plain text...")
            try:
                # Teglarni olib tashlab, xavfsiz tekis matn sifatida yuborish
                plain_chunk = re.sub(r"<[^>]+>", "", chunk)
                # Maxsus HTML entitiylarni asliga qaytarish
                plain_chunk = plain_chunk.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
                await bot.send_message(
                    chat_id=chat_id,
                    text=plain_chunk,
                    parse_mode=None,
                )
            except Exception as ex:
                logger.error(f"Failed to send fallback plain text message: {ex}")
