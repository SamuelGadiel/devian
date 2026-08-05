"""Serialização de datas da API: ISO 8601 / RFC 3339, UTC com sufixo Z.

Toda data retornada pela API segue o padrão `2026-08-05T17:44:40Z`:
- instante absoluto (UTC) — o cliente (app Flutter/Dart) converte pro fuso
  local com `DateTime.parse(...).toLocal()`
- sem fração de segundos — mais legível e suficiente para o domínio

O banco continua armazenando timestamptz (UTC internamente). A infra
(host, Postgres, container) opera em America/Sao_Paulo.
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import PlainSerializer


def to_utc_z(dt: datetime) -> str:
    """Formata um datetime como `YYYY-MM-DDTHH:MM:SSZ` (UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# Campo datetime que serializa para JSON sempre em UTC com Z
# (ex: 2026-08-05T17:44:40Z)
UtcDateTime = Annotated[
    datetime,
    PlainSerializer(to_utc_z, return_type=str, when_used="json"),
]
