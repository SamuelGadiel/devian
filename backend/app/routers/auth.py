from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_session_token
from app.config import settings
from app.db import get_db
from app.services.google_auth import GoogleTokenError, verify_google_id_token

router = APIRouter(prefix="/auth", tags=["Auth"])

UNAUTHORIZED = {
    401: {"description": "Token do Google inválido ou expirado", "model": schemas.ErrorOut}
}
FORBIDDEN = {
    403: {
        "description": "Conta não autorizada, inativa ou deletada",
        "model": schemas.ErrorOut,
    }
}
SERVICE_UNAVAILABLE = {
    503: {
        "description": "Autenticação não configurada (GOOGLE_CLIENT_ID / SESSION_JWT_SECRET)",
        "model": schemas.ErrorOut,
    }
}
VALIDATION = {422: {"description": "Corpo da requisição inválido", "model": schemas.ErrorOut}}


def _allowed_emails() -> set[str]:
    return {
        e.strip().lower()
        for e in settings.allowed_login_emails.split(",")
        if e.strip()
    }


@router.post(
    "/login",
    response_model=schemas.LoginResponse,
    summary="Login with Google",
    response_description=(
        "Valida o ID token do Google, cria/atualiza o usuário e devolve o "
        "token de sessão + perfil. Público (não exige Bearer)."
    ),
    responses={**UNAUTHORIZED, **FORBIDDEN, **SERVICE_UNAVAILABLE, **VALIDATION},
)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Autenticação não configurada: DEVIAN_GOOGLE_CLIENT_ID vazio",
        )
    if settings.session_jwt_secret == "troque-me":
        raise HTTPException(
            status_code=503,
            detail="Autenticação não configurada: DEVIAN_SESSION_JWT_SECRET no default",
        )

    try:
        info = verify_google_id_token(req.id_token, settings.google_client_id)
    except GoogleTokenError as exc:
        raise HTTPException(
            status_code=401, detail=f"Token do Google inválido: {exc}"
        ) from exc

    sub = str(info["sub"])
    email = str(info.get("email") or "").lower()
    name = str(info.get("name") or "")
    raw_picture = info.get("picture")
    picture = str(raw_picture) if raw_picture else None

    user = db.query(models.User).filter_by(google_sub=sub).first()
    if user is None:
        # Primeiro usuário do sistema = admin (dono). Demais precisam estar
        # no allowlist (ALLOWED_LOGIN_EMAILS) — senão nem são criados.
        is_first = db.query(models.User).count() == 0
        if not is_first and email not in _allowed_emails():
            raise HTTPException(status_code=403, detail="Conta não autorizada no Devian")
        user = models.User(
            google_sub=sub,
            email=email,
            name=name,
            picture_url=picture,
            role="admin" if is_first else "member",
            status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if user.status != "active":
            raise HTTPException(status_code=403, detail="Conta inativa ou deletada")
        # Perfil sempre refrescado pelo Google a cada login (foto/nome atuais).
        user.email = email or user.email
        user.name = name or user.name
        user.picture_url = picture
        db.commit()
        db.refresh(user)

    if user.role == "admin":
        # Adota projetos órfãos (criados por token de máquina antes do 1º login).
        db.query(models.Project).filter(models.Project.user_id.is_(None)).update(
            {models.Project.user_id: user.id}
        )
        db.commit()

    return schemas.LoginResponse(
        token=create_session_token(user),
        user=schemas.UserOut.model_validate(user),
    )
