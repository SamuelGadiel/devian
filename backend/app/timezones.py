"""Serialização de datas da API: ISO 8601 / RFC 3339 em America/Sao_Paulo.

Toda data retornada pela API segue o padrão `2026-08-05T17:44:40-03:00`:
- números no fuso de Brasília (o usuário lê a hora local direto no JSON)
- com offset explícito (-03:00), ISO 8601 / RFC 3339 válido
- o app Flutter faz `DateTime.parse(...)` direto e o Dart devolve
  isUtc=false com a hora local do aparelho — sem precisar de .toLocal()
- sem fração de segundos

O banco continua armazenando timestamptz (UTC internamente).
"""

from datetime import UTC, datetime, timedelta, tzinfo
from typing import Annotated

from pydantic import PlainSerializer

BR_OFFSET = timedelta(hours=-3)  # America/Sao_Paulo (sem horário de verão desde 2019)


class FixedOffset(tzinfo):
    """tzinfo com offset fixo (-03:00)."""

    def __init__(self, offset: timedelta, name: str) -> None:
        self._offset = offset
        self._name = name

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return self._offset

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(0)

    def tzname(self, dt: datetime | None) -> str:
        return self._name


BR_TZ = FixedOffset(BR_OFFSET, "-03:00")


def to_brt(dt: datetime) -> str:
    """Formata um datetime como `YYYY-MM-DDTHH:MM:SS-03:00` (Brasília)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    br = dt.astimezone(BR_TZ)
    return f"{br.strftime('%Y-%m-%dT%H:%M:%S')}-03:00"


# Campo datetime que serializa para JSON em Brasília com offset
# (ex: 2026-08-05T17:44:40-03:00)
BrDateTime = Annotated[
    datetime,
    PlainSerializer(to_brt, return_type=str, when_used="json"),
]
