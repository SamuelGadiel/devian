from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User, UserSession

# HTTPBearer padrão do OpenAPI: faz o Swagger UI exibir o botão "Authorize"
# e a cadeirinha de segurança em cada endpoint protegido.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description=(
        "Access token (JWT) do Devian — retornado por POST /auth/login.\n"
        "Pode colar com ou sem o prefixo 'Bearer '."
    ),
)


class AuthContext:
    """Usuário autenticado, resolvido a partir do access token."""

    def __init__(self, user: User):
        self.user = user

    @property
    def user_id(self) -> UUID:
        return self.user.id


# ============================================================
# Senha (bcrypt — nunca armazenada em texto puro)
# ============================================================


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False


# ============================================================
# Tokens: access (JWT curto, stateless) + refresh (opaco, no banco)
# ============================================================


def create_access_token(user: User) -> str:
    """JWT de acesso — identifica o usuário; expira em minutos."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    return jwt.encode(payload, settings.session_jwt_secret, algorithm="HS256")


def _hash_refresh(raw: str) -> str:
    return sha256(raw.encode("utf-8")).hexdigest()


def create_refresh_token(db: Session, user: User) -> str:
    """Refresh token opaco + registro de sessão no banco (só o hash fica)."""
    raw = token_urlsafe(48)
    session = UserSession(
        user_id=user.id,
        token_hash=_hash_refresh(raw),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_ttl_days),
    )
    db.add(session)
    db.commit()
    return raw


def revoke_refresh_token(db: Session, raw: str) -> None:
    """Revoga a sessão do refresh token (idempotente)."""
    session = (
        db.query(UserSession)
        .filter(UserSession.token_hash == _hash_refresh(raw))
        .first()
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()


# ============================================================
# Dependência de auth — TODO endpoint protegido usa isso
# ============================================================


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

    # Normaliza o prefixo: aceita "Bearer <token>" ou só "<token>" no campo
    # do Authorize (o Swagger envia o valor digitado direto no header).
    raw = creds.credentials.strip()
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado: token Bearer ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            raw, settings.session_jwt_secret, algorithms=["HS256"]
        )
        if payload.get("type") != "access":
            raise ValueError("não é access token")
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
