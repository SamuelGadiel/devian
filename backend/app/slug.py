"""Helper de slug (usado por chats e messages)."""

import re
import unicodedata


def slugify(text: str, max_len: int = 50) -> str:
    """Gera um slug legível a partir de um texto (ex: 'Qual a cor?' -> 'qual-a-cor')."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_len].strip("-") or "conversa"
