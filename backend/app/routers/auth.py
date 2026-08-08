from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import (
    _hash_refresh,
    create_access_token,
    create_refresh_token,
    revoke_refresh_token,
    verify_password,
)
from app.db import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])

UNAUTHORIZED = {
    401: {
        "description": "Credenciais inválidas ou token inválido/expirado",
        "model": schemas.ErrorOut,
    }
}
FORBIDDEN = {
    403: {"description": "Conta inativa ou deletada", "model": schemas.ErrorOut}
}
VALIDATION = {422: {"description": "Corpo da requisição inválido", "model": schemas.ErrorOut}}


def _issue_tokens(db: Session, user: models.User) -> schemas.LoginResponse:
    """Gera o par access + refresh e monta a resposta padrão."""
    access = create_access_token(user)
    refresh = create_refresh_token(db, user)
    return schemas.LoginResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        user=schemas.UserOut.model_validate(user),
    )


@router.post(
    "/login",
    response_model=schemas.LoginResponse,
    summary="Login",
    response_description=(
        "Confere e-mail + senha e devolve o par de tokens (access + refresh) "
        "e o perfil. Público (não exige Bearer)."
    ),
    responses={**UNAUTHORIZED, **FORBIDDEN, **VALIDATION},
)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(models.User).filter_by(email=email).first()

    # Mesma mensagem para e-mail inexistente e senha errada (não vaza qual é).
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Conta inativa ou deletada")

    if user.role == "admin":
        # Adota projetos órfãos (user_id NULL) — o admin é o dono deles.
        db.query(models.Project).filter(models.Project.user_id.is_(None)).update(
            {models.Project.user_id: user.id}
        )
        db.commit()

    return _issue_tokens(db, user)


@router.post(
    "/refresh",
    response_model=schemas.LoginResponse,
    summary="Refresh session",
    response_description=(
        "Troca um refresh token válido por um novo par (rotação: o token "
        "antigo é revogado). Público (não exige Bearer)."
    ),
    responses={**UNAUTHORIZED, **FORBIDDEN, **VALIDATION},
)
def refresh(req: schemas.RefreshRequest, db: Session = Depends(get_db)):
    token_hash = _hash_refresh(req.refresh_token)
    session = (
        db.query(models.UserSession)
        .filter(
            models.UserSession.token_hash == token_hash,
            models.UserSession.revoked_at.is_(None),
            models.UserSession.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    user = db.get(models.User, session.user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="Sessão inválida")

    # Rotação: revoga a sessão atual e emite outra (token antigo morre).
    session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return _issue_tokens(db, user)


@router.post(
    "/logout",
    status_code=204,
    summary="Logout",
    response_description=(
        "Revoga o refresh token (encerra a sessão do dispositivo). "
        "Idempotente: sempre 204, mesmo com token já revogado."
    ),
    responses={**VALIDATION},
)
def logout(req: schemas.LogoutRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(db, req.refresh_token)
