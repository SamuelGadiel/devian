"""Geração de UUIDv7 (RFC 9562) — ordenável por tempo, usado nos IDs do hub."""

import secrets
import time
import uuid

_MASK_74 = (1 << 74) - 1


def uuid7() -> uuid.UUID:
    """UUID v7: 48 bits de timestamp (ms) + 74 bits aleatórios.

    A parte temporal na frente faz `ORDER BY id` acompanhar a ordem de criação
    e permite paginação por cursor (`id < cursor`) mesmo com IDs UUID.
    """
    ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF
    rand = secrets.randbits(74) & _MASK_74
    return uuid.UUID(int=(ms << 80) | (0x7 << 76) | rand)
