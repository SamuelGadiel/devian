from fastapi import Header, HTTPException

from app.config import settings


def require_token(authorization: str | None = Header(default=None)):
    """Camada mínima de segurança: Bearer token fixo.

    Será substituído por Cloudflare Access (Zero Trust) na fase do app.
    """
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Não autorizado")
