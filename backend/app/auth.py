from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

# HTTPBearer padrão do OpenAPI: faz o Swagger UI exibir o botão "Authorize"
# e a cadeirinha de segurança em cada endpoint protegido.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description=(
        "Token Bearer do Devian (DEVIAN_API_TOKEN). "
        "Cole apenas o token, sem o prefixo 'Bearer '."
    ),
)


def require_token(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Camada mínima de segurança: token fixo via Authorization: Bearer.

    Será substituído por Cloudflare Access (Zero Trust) na fase do app —
    o backend então confia no header `Cf-Access-Authenticated-User-Email`
    injetado pela borda e este código sai.
    """
    if creds is None or creds.credentials != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado: token Bearer inválido ou ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
