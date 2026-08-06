from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

# HTTPBearer padrão do OpenAPI: faz o Swagger UI exibir o botão "Authorize"
# e a cadeirinha de segurança em cada endpoint protegido.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description=(
        "Token Bearer do Devian — aceita dois formatos:\n"
        "1. Token de máquina (DEVIAN_API_TOKEN): atua como o admin (dono).\n"
        "2. JWT de sessão: retornado por POST /auth/login após login com Google.\n"
        "Cole apenas o token, sem o prefixo 'Bearer '."
    ),
)


class AuthContext:
    """Identidade resolvida a partir do token.

    - ``user`` preenchido: usuário autenticado (JWT de sessão) ou o admin
      (token de máquina, quando o primeiro login já aconteceu).
    - ``user`` None: token de máquina antes de existir qualquer usuário
      (estado pré-migração) — acesso irrestrito, sem filtro por dono.
    """

    def __init__(self, user: User | None):
        self.user = user

    @property
    def user_id(self) -> UUID | None:
        return self.user.id if self.user else None


def _machine_admin(db: Session) -> User | None:
    """Token de máquina age como o admin (dono do Devian)."""
    return (
        db.query(User)
        .filter(User.role == "admin", User.status == "active")
        .order_by(User.created_at.asc())
        .first()
    )


def require_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthContext:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado: token Bearer ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = creds.credentials

    # Token de máquina (DEVIAN_API_TOKEN) — automação, atua como o admin.
    if token == settings.api_token:
        return AuthContext(_machine_admin(db))

    # JWT de sessão (emitido por POST /auth/login).
    try:
        payload = jwt.decode(
            token, settings.session_jwt_secret, algorithms=["HS256"]
        )
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado: token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado: usuário não encontrado",
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta inativa ou deletada",
        )
    return AuthContext(user)


def create_session_token(user: User) -> str:
    """JWT de sessão do Devian: identifica o usuário nas próximas chamadas."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(days=settings.session_ttl_days),
    }
    return jwt.encode(payload, settings.session_jwt_secret, algorithm="HS256")
