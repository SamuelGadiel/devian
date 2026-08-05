"""Fuso padrão do hub: America/Sao_Paulo (BRT, UTC-3).

O banco armazena timestamptz (UTC internamente). Na serialização JSON,
os datetimes são convertidos para BRT — o app e o usuário veem horário
de Brasília sempre.
"""

from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import PlainSerializer

BRT = ZoneInfo("America/Sao_Paulo")


def to_brt(dt: datetime) -> datetime:
    """Converte para BRT. Datetimes naive são tratados como UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(BRT)


# Campo datetime que serializa para JSON sempre em BRT (ex: 2026-08-05T18:19:44.781330-03:00)
BrDateTime = Annotated[
    datetime,
    PlainSerializer(to_brt, return_type=datetime, when_used="json"),
]
