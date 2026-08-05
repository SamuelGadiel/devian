"""Serialização de datas da API: hora de Brasília com sufixo Z.

Formato padrão: `2026-08-05T17:44:40Z`.

Contrato acordado com o app (Flutter/Dart): o número expressa o horário
de Brasília (America/Sao_Paulo) e o sufixo Z é nominal. O app faz
`DateTime.parse(json['created_at'])` direto e exibe o valor sem conversão.

O banco continua armazenando timestamptz (UTC internamente); a conversão
para o fuso de Brasília acontece apenas na serialização JSON.
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Annotated

from pydantic import PlainSerializer

BRT = timezone(timedelta(hours=-3), "BRT")


def to_brt_z(dt: datetime) -> str:
    """Formata um datetime como `YYYY-MM-DDTHH:MM:SSZ` em hora de Brasília."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    br = dt.astimezone(BRT)
    return f"{br.strftime('%Y-%m-%dT%H:%M:%S')}Z"


# Campo datetime que serializa para JSON em hora de Brasília com sufixo Z
# (ex: 2026-08-05T17:44:40Z)
BrDateTime = Annotated[
    datetime,
    PlainSerializer(to_brt_z, return_type=str, when_used="json"),
]
